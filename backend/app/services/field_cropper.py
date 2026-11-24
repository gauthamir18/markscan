from pathlib import Path
import cv2
import numpy as np

FIELDS_DIR = Path("uploads") / "fields"
FIELDS_DIR.mkdir(parents=True, exist_ok=True)

TEMPLATE_WIDTH = 1000
TEMPLATE_HEIGHT = 500

FIELDS = {
    "name": (235, 10, 640, 130),
    "marks": (600, 140, 990, 330),
    "qp_code": (235, 290, 510, 400),
}

TEMPLATE_KEYWORDS = {"name", "date", "class", "board", "subject", "marks", "mark", "comments", "code", "physic", "test"}


def detect_upright_rotation(image):
    """
    Ensures seal is in landscape orientation for template cropping.
    Avoids loading heavy EasyOCR models when Vision AI is active.
    """
    if image is None:
        return image

    h, w = image.shape[:2]
    if h > w:
        return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    import os
    if os.getenv("GEMINI_API_KEY") or os.getenv("DISABLE_LOCAL_OCR") == "1":
        return image

    rotations = [
        (0, image),
        (90, cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)),
        (180, cv2.rotate(image, cv2.ROTATE_180)),
        (270, cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)),
    ]

    # Only consider orientations where width > height (standard seal is landscape)
    landscape_candidates = [(deg, r) for deg, r in rotations if r.shape[1] > r.shape[0]]
    if not landscape_candidates:
        landscape_candidates = rotations

    best_deg = 0
    best_img = image
    best_score = -1

    try:
        from app.services.ocr import get_easyocr_reader
        reader = get_easyocr_reader()
        if reader is not None:
            for deg, r in landscape_candidates:
                thumb = cv2.resize(r, (500, 250), interpolation=cv2.INTER_AREA)
                try:
                    detections = reader.readtext(thumb, detail=0)
                    words = [w.lower() for w in detections]
                    score = sum(1 for w in words for kw in TEMPLATE_KEYWORDS if kw in w)
                    if score > best_score:
                        best_score = score
                        best_deg = deg
                        best_img = r
                except Exception:
                    continue
    except Exception:
        pass

    print(f"[AutoOrient] Selected rotation: {best_deg} deg (keyword matches: {best_score})")
    return best_img


def tighten_seal_border(image):
    """
    Trims dead background margins around the seal using the blue/purple stamped grid ink.
    """
    if image is None:
        return image
    h, w = image.shape[:2]
    b, g, r = cv2.split(image)
    # Stamped seal grid is blue/purple ink
    blue_mask = ((b.astype(int) - r.astype(int) > 12) & (b.astype(int) - g.astype(int) > 8)).astype(np.uint8) * 255
    y_idx, x_idx = np.where(blue_mask > 0)
    if len(y_idx) > 1000:
        y1, y2 = int(np.percentile(y_idx, 0.5)), int(np.percentile(y_idx, 99.5))
        x1, x2 = int(np.percentile(x_idx, 0.5)), int(np.percentile(x_idx, 99.5))
        # Add small safety padding (5px)
        y1 = max(0, y1 - 5)
        y2 = min(h, y2 + 5)
        x1 = max(0, x1 - 5)
        x2 = min(w, x2 + 5)
        # Ensure detected box is at least 50% of the image size
        if (y2 - y1) > h * 0.5 and (x2 - x1) > w * 0.5:
            return image[y1:y2, x1:x2]
    return image


def isolate_red_ink(crop_img):
    """
    Enhances red ink handwriting while suppressing background grid lines.
    """
    b, g, r = cv2.split(crop_img)
    diff_rg = r.astype(int) - g.astype(int)
    diff_rb = r.astype(int) - b.astype(int)
    red_mask = (diff_rg > 15) & (diff_rb > 15) & (r > 80)

    # If significant red ink is detected, create a high-contrast binary image
    if np.sum(red_mask) > 50:
        binary = np.full(crop_img.shape[:2], 255, dtype=np.uint8)
        binary[red_mask] = 0
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        binary = cv2.erode(binary, kernel, iterations=1)
        return cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    return crop_img


def crop_fields(seal_path: str):
    image = cv2.imread(seal_path)

    if image is None:
        raise ValueError(f"Could not read seal image: {seal_path}")

    # 1. 4-Way Auto-Orientation to ensure seal is upright
    oriented_seal = detect_upright_rotation(image)

    # 1b. Tighten to seal outer border to remove background table/paper margins
    tight_seal = tighten_seal_border(oriented_seal)

    # Overwrite seal file with the upright version so frontend displays it right-side up
    cv2.imwrite(seal_path, tight_seal)

    # 2. Standardize to 1000 x 500 template size
    std_seal = cv2.resize(tight_seal, (TEMPLATE_WIDTH, TEMPLATE_HEIGHT), interpolation=cv2.INTER_LANCZOS4)

    crop_paths = {}

    for field, (x1, y1, x2, y2) in FIELDS.items():
        crop = std_seal[y1:y2, x1:x2]

        # Keep natural color crop for frontend display; OCR service handles ink-channel enhancements
        output_path = FIELDS_DIR / f"{Path(seal_path).stem}_{field}.jpg"
        cv2.imwrite(str(output_path), crop)
        crop_paths[field] = str(output_path)

    return crop_paths

