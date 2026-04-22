import io
import json
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware 
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet_v2 import preprocess_input
from contextlib import asynccontextmanager

MODEL_PATH = "ResNet50V2_neuroscan.h5"
CLASSES_PATH = "ResNet50V2_neuroscan_classes.json"
IMG_SIZE = (224, 224)

class State:
    model = None
    class_names = []

state = State()

@asynccontextmanager
async def lifespan(app: FastAPI):
    state.model = load_model(MODEL_PATH)
    with open(CLASSES_PATH) as f:
        state.class_names = json.load(f)['class_names']
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        img = Image.open(io.BytesIO(contents)).convert('RGB')
    except Exception:
        raise HTTPException(status_code=400, detail="Geçersiz görüntü dosyası")

    img = img.resize(IMG_SIZE)
    img_array = np.expand_dims(np.array(img), axis=0).astype(np.float32)
    img_array = preprocess_input(img_array)

    predictions = state.model.predict(img_array, verbose=0)[0]
    top_index = np.argmax(predictions)
    predicted_class = state.class_names[top_index]
    confidence = float(predictions[top_index])

    return {
    "filename": file.filename,
    "prediction": predicted_class,
    "confidence": confidence,
    "has_tumor": predicted_class != "notumor",
    "all_probabilities": {name: float(prob) for name, prob in zip(state.class_names, predictions)}
}