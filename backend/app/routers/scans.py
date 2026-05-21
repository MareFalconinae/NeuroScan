import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from PIL import Image, UnidentifiedImageError
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from tensorflow.keras.applications.resnet_v2 import preprocess_input

from ..core.auth import get_current_user
from ..config import settings, BASE_DIR
from ..database import get_db
from ..models import User, Scan, TumorClass
from ..utils.pdf_report import generate_scan_report
from ..schemas import ScanResponse, ScanListItem, MessageResponse


logger = logging.getLogger("neuroscan.scans")

router = APIRouter(prefix="/scans", tags=["scans"])


class ModelState:
    model = None
    class_names: list[str] = []


model_state = ModelState()

ALLOWED_TYPES = {"image/jpeg", "image/jpg", "image/png"}
IMG_SIZE = (224, 224)


#process image
def _preprocess_image(image_bytes: bytes) -> np.ndarray:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Gecersiz goruntu dosyasi")

    img = img.resize(IMG_SIZE)
    arr = np.expand_dims(np.array(img), axis=0).astype(np.float32)
    return preprocess_input(arr)


#get scan
def _get_scan_or_404(scan_id: uuid.UUID, user_id, db: Session) -> Scan:
    scan = db.execute(
        select(Scan).where(
            Scan.scan_id == scan_id,
            Scan.user_id == user_id,
            Scan.deleted_at.is_(None),
        )
    ).scalar_one_or_none()
    if not scan:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan bulunamadi")
    return scan


#predict
@router.post("/predict", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def predict_scan(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if model_state.model is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Model henuz yuklenmedi")

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Desteklenmeyen dosya turu: {file.content_type}")

    contents = await file.read()
    if len(contents) > settings.max_file_size_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Dosya cok buyuk (max: {settings.MAX_FILE_SIZE_MB} MB)")
    if len(contents) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bos dosya gonderildi")

    arr = _preprocess_image(contents)

    try:
        preds = model_state.model.predict(arr, verbose=0)[0]
    except Exception as e:
        logger.exception("Tahmin hatasi")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Tahmin hatasi: {type(e).__name__}")

    top_idx = int(np.argmax(preds))
    top_class = model_state.class_names[top_idx]
    confidence = float(preds[top_idx])
    all_probs = {name: float(prob) for name, prob in zip(model_state.class_names, preds)}

    scan_id = uuid.uuid4()
    safe_ext = Path(file.filename or "scan.jpg").suffix.lower() or ".jpg"
    if safe_ext not in {".jpg", ".jpeg", ".png"}:
        safe_ext = ".jpg"
    saved_path = settings.upload_dir_path / f"{scan_id}{safe_ext}"

    scan = Scan(
        scan_id=scan_id,
        user_id=current_user.user_id,
        file_path=str(saved_path.relative_to(BASE_DIR)),
        original_filename=file.filename or "unknown.jpg",
        has_tumor=(top_class != TumorClass.NOTUMOR.value),
        tumor_class=TumorClass(top_class),
        confidence=confidence,
        all_probabilities=all_probs,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)
    saved_path.write_bytes(contents)

    logger.info(f"Scan {scan_id} for user={current_user.username} -> {top_class} ({confidence:.3f})")
    return ScanResponse.model_validate(scan)


#order by date
@router.get("/", response_model=list[ScanListItem])
def list_scans(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    scans = db.scalars(
        select(Scan)
        .where(Scan.user_id == current_user.user_id, Scan.deleted_at.is_(None))
        .order_by(Scan.upload_date.desc())
    ).all()
    return [ScanListItem.model_validate(s) for s in scans]


#scan details
@router.get("/{scan_id}", response_model=ScanResponse)
def get_scan(
    scan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ScanResponse.model_validate(_get_scan_or_404(scan_id, current_user.user_id, db))


#delete scan
@router.delete("/{scan_id}", response_model=MessageResponse)
def delete_scan(
    scan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scan = _get_scan_or_404(scan_id, current_user.user_id, db)
    scan.deleted_at = datetime.now(timezone.utc)
    db.commit()
    logger.info(f"Scan {scan_id} soft-deleted by user={current_user.username}")
    return MessageResponse(message="Tarama silindi")


#download pdf report
@router.get(
    "/{scan_id}/report",
    responses={
        200: {"content": {"application/pdf": {}}, "description": "PDF rapor"},
        404: {"description": "Scan bulunamadi"},
    },
)
def download_scan_report(
    scan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scan = _get_scan_or_404(scan_id, current_user.user_id, db)

    mri_path = BASE_DIR / scan.file_path
    if not mri_path.exists():
        logger.warning(f"MRI dosyasi diskde bulunamadi: {mri_path}")

    buffer = io.BytesIO()
    try:
        generate_scan_report(
            output_path_or_buffer=buffer,
            user_username=current_user.username,
            user_email=current_user.email,
            scan_id=str(scan.scan_id),
            upload_date=scan.upload_date,
            original_filename=scan.original_filename,
            mri_image_path=mri_path,
            has_tumor=scan.has_tumor,
            tumor_class=scan.tumor_class.value,
            confidence=scan.confidence,
            all_probabilities=scan.all_probabilities,
        )
    except Exception as e:
        logger.exception("PDF olusturma hatasi")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"PDF olusturma hatasi: {type(e).__name__}")

    buffer.seek(0)
    logger.info(f"PDF report downloaded: scan={scan_id} user={current_user.username}")

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="neuroscan_report_{str(scan.scan_id)[:8]}.pdf"'},
    )
