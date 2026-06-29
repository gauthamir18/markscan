from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
from pathlib import Path
from uuid import uuid4

from app.services.image_processor import process_image
from app.services.ocr import extract_text

router = APIRouter(
    prefix="/upload",
    tags=["Upload"]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.post("/")
async def upload_image(file: UploadFile = File(...)):

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

    processed_path = process_image(str(file_path))

    ocr_text = extract_text(processed_path)

    return {
        "status": "success",
        "filename": unique_filename,
        "processed_image": processed_path,
        "ocr": ocr_text
    }