from pathlib import Path

import cv2

def find_model_path():
    candidates = [
        Path(__file__).resolve().parents[2] / "runs" / "detect" / "markscan_seal_v2" / "weights" / "best.pt",
        Path(__file__).resolve().parents[3] / "runs" / "detect" / "markscan_seal_v2" / "weights" / "best.pt",
        Path("runs/detect/markscan_seal_v2/weights/best.pt").resolve(),
        Path("/app/runs/detect/markscan_seal_v2/weights/best.pt"),
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

MODEL_PATH = find_model_path()

model = None


def get_model():
    global model

    if model is None:
        path = find_model_path()
        if not path.exists():
            print(f"⚠️ YOLO seal detector weights not found at {path}. OCR will proceed without YOLO seal detection.")
            return None
        print(f"Loading YOLO seal detector from {path}...")
        try:
            from ultralytics import YOLO
            model = YOLO(str(path))
            print("YOLO seal detector loaded.")
        except Exception as e:
            print(f"⚠️ Failed to load YOLO seal detector: {e}")
            return None

    return model


def detect_seal(image_path: str, confidence: float = 0.5, crop_source_path: str | None = None):
    image = cv2.imread(image_path)

    crop_source = cv2.imread(crop_source_path) if crop_source_path else image
    if crop_source is None:
        raise ValueError(f"Could not read crop source: {crop_source_path}")

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    detector = get_model()
    if detector is None:
        return {
            "detected": False,
            "confidence": None,
            "box": None,
            "crop_path": None,
        }

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

    height, width = crop_source.shape[:2]

    x1 = max(0, min(x1, width - 1))
    y1 = max(0, min(y1, height - 1))
    x2 = max(x1 + 1, min(x2, width))
    y2 = max(y1 + 1, min(y2, height))

    crop = crop_source[y1:y2, x1:x2]

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
