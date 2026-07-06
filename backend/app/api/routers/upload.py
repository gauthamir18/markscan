from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
from pathlib import Path
from uuid import uuid4

from app.services.image_processor import process_image
from backend.app.services.seal_detector import detect_table
from app.services.document_scanner import scan_header
from app.services.field_extractor import extract_fields
# from app.services.ocr import extract_text

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

    # --------------------------------------------------
    # Step 1 : Basic preprocessing
    # --------------------------------------------------
    processed_path = process_image(str(file_path))

    # --------------------------------------------------
    # Step 2 : Detect table
    # --------------------------------------------------
    table_info = detect_table(processed_path)

    # --------------------------------------------------
    # Step 3 : Perspective correction
    # --------------------------------------------------
    scanned_header = scan_header(
        processed_path,
        table_info["table_box"]
    )

    # --------------------------------------------------
    # Step 4 : Extract fields
    # --------------------------------------------------
    field_images = extract_fields(scanned_header)

    # --------------------------------------------------
    # Step 5 : OCR (Later)
    # --------------------------------------------------
    # ocr_text = extract_text(scanned_header)

    return {
        "status": "success",
        "filename": unique_filename,
        "processed_image": processed_path,
        "table_debug": table_info,
        "scanned_header": scanned_header,
        "fields": field_images
    }