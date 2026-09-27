import os
import glob
import csv
import cv2
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "dataset"
OUT_DIR = BASE_DIR / "dataset_ocr"

FIELDS = {
    "name": (275, 15, 655, 88),
    "marks": (800, 185, 990, 350),
}


def process_split(split_name: str, records: list):
    img_dir = DATASET_DIR / "images" / split_name
    lbl_dir = DATASET_DIR / "labels" / split_name

    img_files = sorted(glob.glob(str(img_dir / "*.jpg")) + glob.glob(str(img_dir / "*.jpeg")) + glob.glob(str(img_dir / "*.png")))
    print(f"[{split_name}] Found {len(img_files)} images.")

    for img_path in img_files:
        stem = Path(img_path).stem
        lbl_path = lbl_dir / f"{stem}.txt"

        if not lbl_path.exists():
            print(f"  Warning: Missing label for {stem}")
            continue

        img = cv2.imread(img_path)
        if img is None:
            print(f"  Warning: Failed to load {img_path}")
            continue

        h, w = img.shape[:2]

        with open(lbl_path, "r") as f:
            lines = [l.strip() for l in f if l.strip()]

        if not lines:
            continue

        # Parse first bounding box (seal)
        parts = list(map(float, lines[0].split()[1:5]))
        xc, yc, bw, bh = parts

        x1 = max(0, int((xc - bw / 2.0) * w))
        y1 = max(0, int((yc - bh / 2.0) * h))
        x2 = min(w, int((xc + bw / 2.0) * w))
        y2 = min(h, int((yc + bh / 2.0) * h))

        seal_crop = img[y1:y2, x1:x2]
        if seal_crop.size == 0:
            continue

        # Standardize orientation: seal width must be greater than height
        if seal_crop.shape[0] > seal_crop.shape[1]:
            seal_crop = cv2.rotate(seal_crop, cv2.ROTATE_90_CLOCKWISE)

        # Standardize template resolution to 1000 x 500
        std_seal = cv2.resize(seal_crop, (1000, 500), interpolation=cv2.INTER_LANCZOS4)

        for field_name, (fx1, fy1, fx2, fy2) in FIELDS.items():
            field_crop = std_seal[fy1:fy2, fx1:fx2]
            if field_crop.size == 0:
                continue

            crop_subfolder = OUT_DIR / "crops" / field_name
            crop_subfolder.mkdir(parents=True, exist_ok=True)

            out_filename = f"{stem}_{field_name}.jpg"
            out_file_path = crop_subfolder / out_filename
            cv2.imwrite(str(out_file_path), field_crop)

            records.append({
                "image_path": str(out_file_path.relative_to(BASE_DIR)),
                "split": split_name,
                "field": field_name,
                "raw_image": Path(img_path).name,
                "text": ""
            })


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = []

    for split in ["train", "val"]:
        process_split(split, records)

    csv_path = OUT_DIR / "annotations.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "split", "field", "raw_image", "text"])
        writer.writeheader()
        writer.writerows(records)

    field_counts = {}
    split_counts = {}
    for r in records:
        field_counts[r["field"]] = field_counts.get(r["field"], 0) + 1
        split_counts[r["split"]] = split_counts.get(r["split"], 0) + 1

    print(f"\nSuccessfully extracted {len(records)} field crops!")
    print(f"Summary by field: {field_counts}")
    print(f"Summary by split: {split_counts}")
    print(f"Annotations file saved to: {csv_path}")


if __name__ == "__main__":
    main()
