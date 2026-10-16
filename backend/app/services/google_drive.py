import os
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]

DEFAULT_FOLDER_ID = "1gjf9mhN37IZPX51pORITJyPNVPtcZboe"


def get_token_path() -> Optional[Path]:
    """Find the OAuth2 token.json file."""
    candidates = [
        Path(__file__).resolve().parents[2] / "token.json",
        Path(__file__).resolve().parents[3] / "token.json",
        Path("token.json").resolve(),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def get_service_account_path() -> Optional[Path]:
    """Find the service account credentials JSON file."""
    env_path = os.getenv("GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    candidates = [
        Path(__file__).resolve().parents[2] / "service_account.json",
        Path(__file__).resolve().parents[3] / "service_account.json",
        Path("service_account.json").resolve(),
        Path("credentials.json").resolve(),
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def get_folder_id() -> str:
    """Return the configured Google Drive folder ID."""
    return os.getenv("GOOGLE_DRIVE_FOLDER_ID", DEFAULT_FOLDER_ID).strip()


def is_drive_configured() -> bool:
    """Check if either OAuth token or Service Account is configured."""
    has_token = get_token_path() is not None
    has_sa = get_service_account_path() is not None
    return (has_token or has_sa) and bool(get_folder_id())


def get_drive_service():
    """Build and return an authorized Google Drive API client service."""
    # 1. Prefer user OAuth2 token (has full user storage quota)
    token_path = get_token_path()
    if token_path and token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, "w") as token_file:
                    token_file.write(creds.to_json())
            if creds and creds.valid:
                return build("drive", "v3", credentials=creds)
        except Exception as e:
            print(f"⚠️ OAuth token loading error: {e}")

    # 2. Fallback to Service Account
    sa_path = get_service_account_path()
    if sa_path and sa_path.exists():
        creds = service_account.Credentials.from_service_account_file(
            str(sa_path), scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)

    raise FileNotFoundError(
        "Google Drive credentials not found. Place token.json or service_account.json in the backend/ folder."
    )


def upload_file_to_drive(
    file_path: str | Path,
    filename: Optional[str] = None,
    folder_id: Optional[str] = None,
    delete_local: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Upload a local image file to Google Drive and optionally delete the local file.
    
    Returns:
        dict with keys: id, name, webViewLink, webContentLink
        or None if upload failed or Drive is not configured.
    """
    path_obj = Path(file_path)
    if not path_obj.exists():
        print(f"⚠️ upload_file_to_drive: File does not exist at {file_path}")
        return None

    if not is_drive_configured():
        print("⚠️ Google Drive integration is not configured. File will remain locally.")
        return None

    try:
        service = get_drive_service()
        target_folder = folder_id or get_folder_id()
        upload_name = filename or path_obj.name

        mimetype, _ = mimetypes.guess_type(str(path_obj))
        if not mimetype:
            mimetype = "image/jpeg"

        file_metadata = {
            "name": upload_name,
            "parents": [target_folder] if target_folder else [],
        }

        media = MediaFileUpload(str(path_obj), mimetype=mimetype, resumable=True)

        drive_file = (
            service.files()
            .create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink, webContentLink",
            )
            .execute()
        )

        file_id = drive_file.get("id")
        web_link = drive_file.get("webViewLink")

        print(f"☁️ Uploaded to Google Drive: {upload_name} (ID: {file_id})")

        # Delete local copy if requested
        if delete_local:
            try:
                path_obj.unlink(missing_ok=True)
                print(f"🗑️ Deleted local copy to save space: {path_obj}")
            except Exception as del_err:
                print(f"⚠️ Could not delete local file {path_obj}: {del_err}")

        return {
            "id": file_id,
            "name": drive_file.get("name"),
            "webViewLink": web_link,
            "webContentLink": drive_file.get("webContentLink"),
        }

    except Exception as e:
        print(f"❌ Failed to upload to Google Drive: {e}")
        return None
