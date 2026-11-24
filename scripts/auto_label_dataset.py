import os
import csv
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.services.ocr import extract_text

CSV_PATH = BASE_DIR / "dataset_ocr" / "annotations.csv"

def auto_label():
    if not CSV_PATH.exists():
        print(f"Error: {CSV_PATH} does not exist. Run prepare_ocr_dataset.py first.")
        return

    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))

    print(f"Found {len(reader)} entries in {CSV_PATH}")
    updated = 0

    for i, row in enumerate(reader):
        # Only process rows that do not already have text
        if row.get("text", "").strip():
            continue

        img_path = BASE_DIR / row["image_path"]
        if not img_path.exists():
            continue

        try:
            texts = extract_text(str(img_path))
            combined_text = " ".join(texts).strip()
            row["text"] = combined_text
            updated += 1
            if updated % 20 == 0 or updated == len(reader):
                print(f"  Processed {updated} crops...")
        except Exception as e:
            print(f"  Error on {img_path}: {e}")

    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_path", "split", "field", "raw_image", "text"])
        writer.writeheader()
        writer.writerows(reader)

    print(f"\nCompleted! Auto-labeled {updated} items in {CSV_PATH}")

if __name__ == "__main__":
    auto_label()
