import io
import os
from contextlib import asynccontextmanager
from pathlib import Path

import torch
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

from modules.model import LungSoundClassifier, RespiratoryAST

BASE_DIR = Path(__file__).resolve().parent

# Muat ml-service/.env secara eksplisit, bukan auto-search dari CWD.
# override=False: environment variable dari shell tetap menang.
load_dotenv(str(BASE_DIR / ".env"), override=False)


def _resolve_checkpoint_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


CHECKPOINT_PATH = _resolve_checkpoint_path(
    os.getenv("CHECKPOINT_PATH", "modules/weights/best.ckpt")
)


classifier: LungSoundClassifier | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier
    if CHECKPOINT_PATH.exists():
        device = "cuda" if torch.cuda.is_available() else "cpu"
        module = RespiratoryAST.load_from_checkpoint(str(CHECKPOINT_PATH), map_location=device, pretrained=False)
        module.to(device).eval()
        classifier = LungSoundClassifier(module)
        print(f"Model loaded from {CHECKPOINT_PATH} on {device}")
    else:
        print(f"Peringatan: checkpoint tidak ditemukan di {CHECKPOINT_PATH}, /predict akan mengembalikan 503")
    yield
    classifier = None


app = FastAPI(title="PneumaCare ML Services", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": classifier is not None}


@app.post("/predict")
async def predict(request: Request):
    if classifier is None:
        raise HTTPException(503, "Model belum dimuat. Set CHECKPOINT_PATH ke file .ckpt.")

    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("file")
        if upload is None:
            raise HTTPException(400, "Field form 'file' (wav) tidak ditemukan.")
        content = await upload.read()
        filename = getattr(upload, "filename", None)
    else:
        content = await request.body()
        filename = request.headers.get("x-filename")

    if not content:
        raise HTTPException(400, "Payload audio kosong.")

    try:
        result = classifier.predict(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(422, f"Gagal memproses audio: {e}")

    return {"filename": filename, **result}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
