import os
import json
import logging

from contextlib import asynccontextmanager
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

from pathlib import Path
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tensorflow.keras.models import load_model

from .config import settings, BASE_DIR
from .routers.auth import router as auth_router
from .routers.scans import router as scan_router, model_state


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger("neuroscan")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NeuroScan backend basliyor...")

    settings.upload_dir_path
    logger.info(f"Upload dir: {settings.upload_dir_path}")

    model_path = BASE_DIR / settings.MODEL_PATH
    classes_path = BASE_DIR / settings.CLASSES_PATH

    if not model_path.exists():
        raise RuntimeError(f"Model bulunamadi: {model_path}")
    if not classes_path.exists():
        raise RuntimeError(f"Classes bulunamadi: {classes_path}")

    logger.info(f"Model yukleniyor: {model_path}")
    model_state.model = load_model(str(model_path))

    with open(classes_path) as f:
        meta = json.load(f)
    model_state.class_names = meta["class_names"]
    logger.info(f"Siniflar: {model_state.class_names}")

    dummy = np.random.rand(1, 224, 224, 3).astype(np.float32)
    model_state.model.predict(dummy, verbose=0)
    logger.info("Model hazir.")

    yield

    logger.info("NeuroScan kapaniyor")


app = FastAPI(
    title="NeuroScan API",
    description="Beyin tumoru MRI siniflandirma sistemi.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_urls_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(scan_router)


@app.get("/", tags=["meta"])
def root():
    return {"service": "NeuroScan API", "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    return {
        "status": "ok",
        "model_loaded": model_state.model is not None,
        "classes": model_state.class_names,
    }
