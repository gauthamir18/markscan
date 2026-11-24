#!/usr/bin/env python3
"""
Move the training and validation dataset to Google Drive inside a dedicated
'training_dataset' folder, then delete the local folders from the PC.
"""
import os
import sys
import shutil
import zipfile
import mimetypes
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from googleapiclient.http import MediaFileUpload
from app.services.google_drive import is_drive_configured, get_drive_service, get_folder_id


def create_drive_folder(service, name: str, parent_id: str) -> str:
    """Create a folder inside the parent Google Drive folder and return its ID."""
    # Check if folder already exists
    query = f"'{parent_id}' in parents and name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    res = service.files().list(q=query, fields="files(id, name)").execute()
    files = res.get("files", [])
    if files:
        print(f"📁 Found existing Google Drive folder '{name}' (ID: {files[0]['id']})")
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=metadata, fields="id, name").execute()
    print(f"📁 Created Google Drive folder '{name}' (ID: {folder['id']})")
    return folder["id"]


def upload_single_file(service, local_path: Path, parent_id: str, custom_name: str = None) -> dict:
    upload_name = custom_name or local_path.name
    mimetype, _ = mimetypes.guess_type(str(local_path))
    if not mimetype:
        mimetype = "application/octet-stream"

    metadata = {
        "name": upload_name,
        "parents": [parent_id],
    }
    media = MediaFileUpload(str(local_path), mimetype=mimetype, resumable=True)
    f = service.files().create(body=metadata, media_body=media, fields="id, name, webViewLink").execute()
    return f


def main():
    if not is_drive_configured():
        print("❌ Google Drive is not configured! Check service_account.json.")
        sys.exit(1)

    service = get_drive_service()
    markscan_folder_id = get_folder_id()
    print(f"🚀 Moving training and validating dataset to Google Drive: markscan ({markscan_folder_id})\n")

    # 1. Create main 'training_dataset' folder in Drive
    training_folder_id = create_drive_folder(service, "training_dataset", markscan_folder_id)

    # 2. Create complete ZIP archive of dataset and dataset_ocr
    zip_path = ROOT_DIR / "markscan_full_training_dataset.zip"
    print(f"📦 Creating comprehensive backup archive: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        dataset_dir = ROOT_DIR / "dataset"
        if dataset_dir.exists():
            for root, _, files in os.walk(dataset_dir):
                for file in files:
                    full_p = Path(root) / file
                    arcname = full_p.relative_to(ROOT_DIR)
                    zf.write(full_p, arcname)

        dataset_ocr_dir = ROOT_DIR / "dataset_ocr"
        if dataset_ocr_dir.exists():
            for root, _, files in os.walk(dataset_ocr_dir):
                for file in files:
                    full_p = Path(root) / file
                    arcname = full_p.relative_to(ROOT_DIR)
                    zf.write(full_p, arcname)

    print(f"⬆️ Uploading complete dataset archive ({zip_path.stat().st_size / (1024*1024):.1f} MB)...")
    zip_res = upload_single_file(service, zip_path, training_folder_id)
    print(f"✅ Uploaded ZIP to Drive! (ID: {zip_res['id']})\n")

    # Clean up the local temp zip
    zip_path.unlink(missing_ok=True)

    # 3. Create 'train' and 'val' subfolders in Drive and upload images
    train_folder_id = create_drive_folder(service, "train", training_folder_id)
    val_folder_id = create_drive_folder(service, "val", training_folder_id)

    train_img_dir = ROOT_DIR / "dataset" / "images" / "train"
    val_img_dir = ROOT_DIR / "dataset" / "images" / "val"

    train_images = list(train_img_dir.glob("*.*")) if train_img_dir.exists() else []
    val_images = list(val_img_dir.glob("*.*")) if val_img_dir.exists() else []

    print(f"⬆️ Uploading {len(train_images)} training images to Drive 'train/' folder...")
    train_success = 0
    for idx, img in enumerate(train_images, 1):
        if img.name.startswith("."):
            continue
        try:
            upload_single_file(service, img, train_folder_id)
            train_success += 1
            if train_success % 25 == 0 or train_success == len(train_images):
                print(f"   [{train_success}/{len(train_images)}] Training images uploaded...")
        except Exception as e:
            print(f"   ⚠️ Error uploading {img.name}: {e}")

    print(f"⬆️ Uploading {len(val_images)} validating images to Drive 'val/' folder...")
    val_success = 0
    for idx, img in enumerate(val_images, 1):
        if img.name.startswith("."):
            continue
        try:
            upload_single_file(service, img, val_folder_id)
            val_success += 1
            if val_success % 10 == 0 or val_success == len(val_images):
                print(f"   [{val_success}/{len(val_images)}] Validating images uploaded...")
        except Exception as e:
            print(f"   ⚠️ Error uploading {img.name}: {e}")

    # 4. Now that everything is safely in Google Drive, delete local dataset folders!
    print("\n🗑️ Removing local dataset directories from PC...")
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
        print("✅ Deleted local 'dataset/' folder.")
    if dataset_ocr_dir.exists():
        shutil.rmtree(dataset_ocr_dir)
        print("✅ Deleted local 'dataset_ocr/' folder.")

    print("\n🎉 Done! All training and validating images are now safely in Google Drive and cleared from your local Mac.")

if __name__ == "__main__":
    main()
