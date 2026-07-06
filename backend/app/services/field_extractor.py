import cv2
from pathlib import Path

FIELDS_DIR = Path("fields")
FIELDS_DIR.mkdir(exist_ok=True)


def extract_fields(image_path: str):

    image = cv2.imread(image_path)

    if image is None:
        raise Exception("Unable to read image")

    h, w = image.shape[:2]
    print(f"Width = {w}, Height = {h}")

    # Temporary debugging only
    cv2.imwrite(str(FIELDS_DIR / "debug.jpg"), image)

    return {}