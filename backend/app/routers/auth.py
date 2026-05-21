import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

#dummy_hash
_DUMMY_HASH = "$2b$12$" + "x" * 53

from ..core.auth import (
    issue_auth_tokens,
    clear_auth_cookies,
    hash_password,
    verify_password,
    get_current_user,
    get_user_from_refresh,
)
from ..database import get_db
from ..models import User
from ..schemas import (
    UserRegister,
    UserLogin,
    UpdateUsernameRequest,
    UserResponse,
    TokenResponse,
    MessageResponse,
)


logger = logging.getLogger("neuroscan.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


#register
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: UserRegister, response: Response, db: Session = Depends(get_db)):
    if db.execute(
        select(User).where(
            func.lower(User.username) == func.lower(body.username),
            User.deleted_at.is_(None),
        )
    ).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu kullanici adi zaten alinmis")

    deleted = db.execute(
        select(User).where(
            User.email == body.email.lower(),
            User.deleted_at.isnot(None),
        )
    ).scalar_one_or_none()
    if deleted:
        db.delete(deleted)
        db.commit()

    new_user = User(
        email=body.email.lower(),
        username=body.username,
        password_hash=hash_password(body.password),
        email_verified=True,
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu e-posta zaten kayitli")

    issue_auth_tokens(response, new_user.user_id)
    logger.info(f"User registered: {new_user.username} ({new_user.email})")
    return TokenResponse(user=UserResponse.model_validate(new_user), message="Kayit basarili")


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

    user = any_user

    issue_auth_tokens(response, user.user_id)
    logger.info(f"User logged in: {user.username}")
    return TokenResponse(user=UserResponse.model_validate(user), message="Giris basarili")


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
