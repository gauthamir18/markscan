import cv2
from pathlib import Path
from app.services.document_scanner import scan_document


PROCESSED_DIR = Path("processed")
PROCESSED_DIR.mkdir(exist_ok=True)


def process_image(image_path: str):

    # Read image
    image = cv2.imread(image_path)

    if image is None:
        raise Exception("Unable to read image")

    # Step 1 - Rotate if needed
    image = scan_document(image)
    # Step 2 - Convert to Grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 3 - Remove Noise
    denoised = cv2.GaussianBlur(gray, (5, 5), 0)

    # Step 4 - Adaptive Threshold
    threshold = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )

    # Save processed image
    output_path = PROCESSED_DIR / Path(image_path).name

    cv2.imwrite(str(output_path), threshold)

    return str(output_path)
  