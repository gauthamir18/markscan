#!/usr/bin/env python3
"""
One-time script to authenticate with your personal Google Drive account.
This uses your own account's 15 GB storage quota instead of service account limits.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
]

def authenticate():
    # Find client_secret / credentials.json
    candidates = [
        BASE_DIR / "client_secret.json",
        BASE_DIR / "credentials.json",
        BASE_DIR.parent / "client_secret.json",
        BASE_DIR.parent / "credentials.json",
        Path.home() / "Downloads" / "credentials.json",
    ]
    client_secret_path = None
    for p in candidates:
        if p.exists():
            client_secret_path = p
            break

    if not client_secret_path:
        print("❌ Could not find 'credentials.json' or 'client_secret.json'.")
        print("\nTo get this file:")
        print("1. Go to https://console.cloud.google.com/apis/credentials")
        print("2. Click 'Create Credentials' > 'OAuth client ID'")
        print("3. Application type: 'Desktop app' > Click 'Create'")
        print("4. Download the JSON, rename it to 'credentials.json', and place it in the backend/ folder.")
        return

    print(f"🔑 Using OAuth credentials from: {client_secret_path}")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
    creds = flow.run_local_server(port=0)

    token_path = BASE_DIR / "token.json"
    with open(token_path, "w") as token_file:
        token_file.write(creds.to_json())

    print(f"\n✅ Authentication successful! Saved personal access token to {token_path}")
    print("Now all app uploads and dataset transfers will upload directly to your personal Google Drive with 15 GB quota!")

if __name__ == "__main__":
    authenticate()
