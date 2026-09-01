from pathlib import Path

import cv2
from ultralytics import YOLO


MODEL_PATH = (
    Path(__file__).resolve().parents[3]
    / "runs"
    / "runs"
    / "seal_detector"
    / "weights"
    / "best.pt"
)

model = None


def get_model():
    global model

    if model is None:
        print("Loading YOLO seal detector...")
        model = YOLO(str(MODEL_PATH))
        print("YOLO seal detector loaded.")

    return model


def detect_seal(image_path: str, confidence: float = 0.5):
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    detector = get_model()

    results = detector(
        image,
        conf=confidence,
        verbose=False,
    )

    if not results or len(results[0].boxes) == 0:
        return {
            "detected": False,
            "confidence": None,
            "box": None,
            "crop_path": None,
        }

    boxes = results[0].boxes

    best_index = int(boxes.conf.argmax())

    box = boxes.xyxy[best_index].cpu().numpy()
    score = float(boxes.conf[best_index].cpu())

    x1, y1, x2, y2 = map(int, box)

    height, width = image.shape[:2]

    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(x1 + 1, min(x2, width))
    y2 = max(y1 + 1, min(y2, height))

    crop = image[y1:y2, x1:x2]

    crop_dir = Path("uploads") / "seals"
    crop_dir.mkdir(parents=True, exist_ok=True)

    crop_path = crop_dir / f"{Path(image_path).stem}_seal.jpg"

    cv2.imwrite(str(crop_path), crop)

    return {
        "detected": True,
        "confidence": score,
        "box": [x1, y1, x2, y2],
        "crop_path": str(crop_path),
    }
