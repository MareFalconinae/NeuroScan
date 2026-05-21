import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import settings
from ..core.auth import (
    issue_auth_tokens,
    clear_auth_cookies,
    hash_password,
    verify_password,
    get_current_user,
    get_user_from_refresh,
)
from ..database import get_db
from ..models import User, PendingRegistration
from ..schemas import (
    UserRegister,
    UserLogin,
    UpdateUsernameRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
    PendingVerificationResponse,
    VerifyEmailRequest,
    ResendVerificationRequest,
)
from ..utils.email import send_verification_email


logger = logging.getLogger("neuroscan.auth")

_DUMMY_HASH = "$2b$12$" + "x" * 53

router = APIRouter(prefix="/auth", tags=["auth"])


def _generate_verification_code() -> tuple[str, datetime]:
    code = f"{secrets.randbelow(1_000_000):06d}"
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES
    )
    return code, expires_at


#register — saves to pending_registrations, NOT users table
@router.post("/register", response_model=PendingVerificationResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, db: Session = Depends(get_db)):
    email = body.email.lower()

    # username taken by active user
    if db.execute(
        select(User).where(
            func.lower(User.username) == func.lower(body.username),
            User.deleted_at.is_(None),
        )
    ).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu kullanici adi zaten alinmis")

    # email taken by active user
    if db.execute(
        select(User).where(User.email == email, User.deleted_at.is_(None))
    ).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu e-posta zaten kayitli")

    # clean up soft-deleted user with same email
    deleted = db.execute(
        select(User).where(User.email == email, User.deleted_at.isnot(None))
    ).scalar_one_or_none()
    if deleted:
        db.delete(deleted)

    # upsert pending registration (replace expired or new)
    existing_pending = db.execute(
        select(PendingRegistration).where(PendingRegistration.email == email)
    ).scalar_one_or_none()
    if existing_pending:
        db.delete(existing_pending)
        db.flush()

    code, expires_at = _generate_verification_code()

    pending = PendingRegistration(
        email=email,
        username=body.username,
        password_hash=hash_password(body.password),
        verification_code=code,
        expires_at=expires_at,
    )
    db.add(pending)
    db.commit()

    try:
        send_verification_email(email, code)
    except Exception as exc:
        logger.error(f"Email send failed for {email}: {exc}")
    logger.info(f"Pending registration created: {body.username} ({email})")
    return PendingVerificationResponse(
        message="Dogrulama kodu e-posta adresinize gonderildi",
        email=email,
    )


#verify email — creates real user only after correct code
@router.post("/verify-email", response_model=TokenResponse)
def verify_email(body: VerifyEmailRequest, response: Response, db: Session = Depends(get_db)):
    email = body.email.lower()

    pending = db.execute(
        select(PendingRegistration).where(PendingRegistration.email == email)
    ).scalar_one_or_none()

    if not pending:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Kayit islemi bulunamadi. Yeniden kayit olun.")

    if datetime.now(timezone.utc) > pending.expires_at:
        db.delete(pending)
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Dogrulama kodunun suresi dolmus. Yeniden kayit olun.")

    if pending.verification_code != body.code:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Hatali dogrulama kodu")

    # final username conflict check (race condition guard)
    if db.execute(
        select(User).where(
            func.lower(User.username) == func.lower(pending.username),
            User.deleted_at.is_(None),
        )
    ).scalar_one_or_none():
        db.delete(pending)
        db.commit()
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu kullanici adi kayit sirasinda baska biri tarafindan alindi. Yeniden kayit olun.")

    new_user = User(
        email=pending.email,
        username=pending.username,
        password_hash=pending.password_hash,
        email_verified=True,
    )
    db.add(new_user)
    db.delete(pending)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu e-posta zaten kayitli")

    issue_auth_tokens(response, new_user.user_id)
    logger.info(f"User created after verification: {new_user.username} ({new_user.email})")
    return TokenResponse(user=UserResponse.model_validate(new_user), message="Email dogrulandi, giris yapildi")


#resend verification
@router.post("/resend-verification", response_model=PendingVerificationResponse)
def resend_verification(body: ResendVerificationRequest, db: Session = Depends(get_db)):
    email = body.email.lower()

    pending = db.execute(
        select(PendingRegistration).where(PendingRegistration.email == email)
    ).scalar_one_or_none()

    if not pending:
        # don't reveal whether email exists
        return PendingVerificationResponse(message="Dogrulama kodu gonderildi", email=email)

    last_sent = pending.expires_at - timedelta(minutes=settings.VERIFICATION_CODE_EXPIRE_MINUTES)
    if datetime.now(timezone.utc) - last_sent < timedelta(seconds=60):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Cok sikli deniyorsunuz. 1 dakika bekleyin.",
        )

    code, expires_at = _generate_verification_code()
    pending.verification_code = code
    pending.expires_at = expires_at
    db.commit()

    try:
        send_verification_email(email, code)
    except Exception as exc:
        logger.error(f"Email resend failed for {email}: {exc}")
    logger.info(f"Verification code resent: {email}")
    return PendingVerificationResponse(message="Yeni dogrulama kodu gonderildi", email=email)


#login
@router.post("/login", response_model=TokenResponse)
def login(body: UserLogin, response: Response, db: Session = Depends(get_db)):
    any_user = db.execute(
        select(User).where(User.email == body.email.lower())
    ).scalar_one_or_none()

    if not any_user:
        verify_password(body.password, _DUMMY_HASH)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bu e-posta ile kayitli hesap bulunamadi")

    if any_user.deleted_at is not None:
        verify_password(body.password, _DUMMY_HASH)
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bu e-posta ile kayitli hesap bulunamadi")

    if not verify_password(body.password, any_user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-posta veya parola hatali")

    issue_auth_tokens(response, any_user.user_id)
    logger.info(f"User logged in: {any_user.username}")
    return TokenResponse(user=UserResponse.model_validate(any_user), message="Giris basarili")


#logout
@router.post("/logout", response_model=MessageResponse)
def logout(response: Response):
    clear_auth_cookies(response)
    return MessageResponse(message="Cikis yapildi")


#profile
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


#refresh_session
@router.post("/refresh", response_model=MessageResponse)
def refresh_tokens(response: Response, user: User = Depends(get_user_from_refresh)):
    issue_auth_tokens(response, user.user_id)
    return MessageResponse(message="Token yenilendi")


#change username
@router.patch("/me", response_model=UserResponse)
def update_username(
    body: UpdateUsernameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conflict = db.execute(
        select(User).where(
            func.lower(User.username) == func.lower(body.username),
            User.user_id != current_user.user_id,
            User.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if conflict:
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu kullanici adi zaten alinmis")

    current_user.username = body.username
    db.commit()
    db.refresh(current_user)
    logger.info(f"Username updated: {current_user.email} -> {body.username}")
    return UserResponse.model_validate(current_user)


#delete account
@router.delete("/me", response_model=MessageResponse)
def delete_account(
    response: Response,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.deleted_at = datetime.now(timezone.utc)
    db.commit()
    clear_auth_cookies(response)
    logger.info(f"Account deleted: {current_user.username} ({current_user.email})")
    return MessageResponse(message="Hesap silindi")
