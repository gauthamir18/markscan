#!/usr/bin/env python3
"""
Migrate existing local uploaded photos in backend/uploads to Google Drive
and delete local copies to free up disk space.
"""
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from app.services.google_drive import is_drive_configured, upload_file_to_drive, get_folder_id

def migrate():
    if not is_drive_configured():
        print("❌ Google Drive is not configured yet!")
        print("Please ensure service_account.json is in backend/ and GOOGLE_DRIVE_FOLDER_ID is set.")
        return

    folder_id = get_folder_id()
    print(f"🚀 Starting migration to Google Drive folder: {folder_id}")

    uploads_dir = BASE_DIR / "uploads"
    images = list(uploads_dir.glob("*.jpg")) + list(uploads_dir.glob("*.jpeg")) + list(uploads_dir.glob("*.png"))
    print(f"Found {len(images)} local images to upload.\n")

    count = 0
    errors = 0
    for img in images:
        res = upload_file_to_drive(img, delete_local=True)
        if res:
            count += 1
            print(f"[{count}/{len(images)}] Migrated: {img.name} -> Drive ID: {res['id']}")
        else:
            errors += 1
            print(f"❌ Failed to migrate {img.name}")

    print(f"\n✅ Migration finished! {count} files uploaded to Google Drive and deleted locally. ({errors} errors)")

if __name__ == "__main__":
    migrate()
