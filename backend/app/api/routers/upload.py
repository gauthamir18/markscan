from pathlib import Path
from uuid import uuid4

import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.image_processor import process_image
from app.services.seal_detector import detect_seal


router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.post("/")
async def upload_image(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG and PNG images are allowed."
        )

    unique_filename = f"{uuid4()}{extension}"
    file_path = UPLOAD_DIR / unique_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Basic image preprocessing
    processed_path = process_image(str(file_path))

    # Detect and crop the seal using the trained model
    seal_info = detect_seal(processed_path)

    if not seal_info["detected"]:
        return {
            "status": "no_seal_detected",
            "filename": unique_filename,
            "message": "No seal was detected in the uploaded image.",
        }

    return {
    "status": "success",
    "filename": unique_filename,
    "processed_image": processed_path,
    "seal": {
        "detected": seal_info["detected"],
        "confidence": seal_info["confidence"],
        "box": seal_info["box"],
        "crop_path": seal_info["crop_path"],
        "crop_url": "/" + seal_info["crop_path"],
    },
}
