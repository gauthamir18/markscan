import cv2
from pathlib import Path
from app.templates.intellekt import FIELDS
FIELDS_DIR = Path("fields")
FIELDS_DIR.mkdir(exist_ok=True)


def extract_fields(image_path: str):
    print("===== FIELD EXTRACTOR CALLED =====")
    image = cv2.imread(image_path)

    if image is None:
        raise Exception("Unable to read image")

    h, w = image.shape[:2]
    print(f"Image size: {w} x {h}")
    
    

    output = {}
    print(FIELDS)
    for field, (x1, y1, x2, y2) in FIELDS.items():
        print(field)
        crop = image[y1:y2, x1:x2]
        print(crop.shape)
        save_path = FIELDS_DIR / f"{field}.jpg"

        cv2.imwrite(str(save_path), crop)
        print(save_path)
        output[field] = str(save_path)

    return output