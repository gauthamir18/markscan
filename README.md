# MarkScan AI

An AI-assisted exam-mark entry system that reads handwritten information from photographed exam seals and prepares structured mark records for faculty verification.

> **Project status:** Academic/prototype project. Do not deploy with real student data until the security issues documented in the project audit are remediated. In particular, remove exposed student records, replace plaintext-password authentication, and protect write APIs.

## Project overview

MarkScan AI combines a Flutter faculty application with a FastAPI service. A faculty member uploads a photograph of an exam seal. The backend locates the seal, extracts student and marks information using vision/OCR, matches the name against PostgreSQL student records, and returns a proposed result for review.

The upload workflow records a scan for verification. Faculty can correct extracted fields and submit the confirmed marks through the API.

## System architecture

~~~mermaid
flowchart LR
  A[Flutter faculty app] -->|multipart image + class/test context| B[FastAPI]
  B --> C[YOLOv8 seal detector]
  C --> D[OpenCV orientation and crop processing]
  D --> E[Vision extraction]
  E --> F[Gemini API]
  E --> G[Qwen via local Ollama]
  E --> H[Local OCR fallback]
  H --> I[RapidFuzz student matching]
  F --> I
  G --> I
  I <--> J[(PostgreSQL)]
  I -->|structured scan result| A
  A -->|faculty confirmation| B
  B --> J
~~~

The vision provider order in the current implementation is Gemini, then Qwen, followed by local OCR when a vision model does not return a result.

## Tech stack

| Layer | Technology |
|---|---|
| Mobile frontend | Flutter, Dart |
| API backend | Python, FastAPI, Uvicorn |
| Database | PostgreSQL, SQLAlchemy |
| Seal detection | Ultralytics YOLOv8 |
| Image processing | OpenCV, Pillow |
| Handwriting / OCR | Google Gemini vision, Qwen2.5-VL (Ollama-compatible endpoint), EasyOCR/local OCR |
| Student matching | RapidFuzz |
| Configuration | python-dotenv |

## Key features

- Flutter-based faculty interface for login, scanning, confirmation and marks management.
- Image upload through a multipart API.
- YOLOv8 detection of the exam-seal region.
- OpenCV preprocessing, orientation handling and field cropping.
- Vision-model extraction of student name, marks, test code and orientation.
- Fallback path to local OCR when cloud/local vision extraction is unavailable.
- PostgreSQL candidate lookup and fuzzy student-name matching.
- Confidence information and a verification flag to help faculty review uncertain matches.
- Separate scan/confirmation/submission stages in the backend workflow.

## Repository structure

~~~text
backend/
  app/
    api/routers/       # auth, upload, tests, marks management, student routes
    database/          # SQLAlchemy connection and base
    models/            # Student, Faculty, Test and Mark models
    services/          # YOLO, OpenCV, OCR, Gemini, Qwen and matching logic
  data/                # seed CSV files (do not use real personal data here)
  models/              # model assets
  runs/                # YOLO training output / weights
  requirements.txt
  .env.example
frontend/
  lib/
    screens/           # Flutter application screens
    services/          # API client
    widgets/
~~~

## Setup and installation

### Prerequisites

- Python 3.10+ (use a version supported by the installed PyTorch/Ultralytics packages)
- PostgreSQL
- Flutter SDK
- A Gemini API key for cloud vision (optional if using another configured vision provider)
- Ollama with a compatible Qwen vision model, if using the local Qwen fallback

### 1. Configure the backend

~~~bash
git clone https://github.com/gauthamir18/markscan.git
cd markscan/backend

python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
~~~

Edit backend/.env with your own local or hosted values:

~~~dotenv
DATABASE_URL=postgresql://DB_USER:DB_PASSWORD@DB_HOST:5432/DB_NAME
GEMINI_API_KEY=replace_with_your_key
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT=30
VISION_PROVIDER=gemini
QWEN_BASE_URL=http://localhost:11434
QWEN_MODEL=qwen2.5vl:3b
QWEN_TIMEOUT=60
GOOGLE_DRIVE_FOLDER_ID=
GOOGLE_DRIVE_SERVICE_ACCOUNT_FILE=service_account.json
~~~

Never commit .env, service-account JSON, OAuth tokens, database URLs with passwords, or real student datasets. The committed .env.example is a template only; replace all sample values.

### 2. Provision the first administrator

The application no longer creates a predictable default admin account or imports student credentials from a CSV at startup. After setting DATABASE_URL and JWT_SECRET_KEY, run this from the backend/ directory:

```bash
python scripts/create_admin.py
```

Choose a unique password of at least 12 characters. Existing legacy accounts are upgraded to Argon2id hashes after a successful login; because earlier credentials were exposed in the repository, arrange a password reset for every existing student and faculty account. Reset an account from the backend directory with `python scripts/reset_account_password.py`; enter the faculty email or student roll number when prompted. Repeat for each account and distribute new credentials privately.

Start the API from the backend directory:

~~~bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
~~~

FastAPI's interactive API documentation is available at http://localhost:8000/docs.

### 2. Configure and run the Flutter app

Open a second terminal:

~~~bash
cd markscan/frontend
flutter pub get
flutter run
~~~

Set the backend base URL in lib/services/api_service.dart to the address reachable from the device or emulator. Do not use localhost from a physical phone to refer to your development computer.

## API documentation

The API is implemented in backend/app/main.py and the router modules under backend/app/api/routers/. The live OpenAPI/Swagger page at /docs is the authoritative source for request and response schemas.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /auth/login | Faculty/student login |
| POST | /upload/ | Upload an exam-seal image and extract proposed data |
| POST | /upload/confirm | Confirm or correct one scanned mark |
| POST | /upload/submit_batch | Submit a batch of mark records |
| GET | /tests/ | Retrieve available tests |
| GET | /manage/class_marks | Retrieve class mark data |
| POST | /manage/update_mark | Update a mark |
| GET | /student/{roll_no}/profile_and_marks | Retrieve student profile and marks |

For POST /upload/, send a multipart form with the image field file. Optional context fields include selected_class, test_code, subject and board.

## Security and data handling

The current security-hardening branch adds Argon2id password hashing, short-lived signed bearer tokens, role checks on protected API routes, and secure token storage in the Flutter app. Configure a unique JWT_SECRET_KEY in the backend deployment environment before starting the API. The key must be at least 32 characters; generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))".


The student credential CSV has been removed from the current branch snapshot, and the main and security-hardening branch histories have been reset. The v0.1.0 tag still points to the earlier history and must be deleted before historical exposure can be considered cleared. GitHub may retain unreachable objects or cached views for a period; contact GitHub Support if the old commit remains accessible. Treat all previously exposed passwords as compromised and reset them.

- Remove real student data and passwords from tracked files and Git history; rotate/reset exposed credentials.
- Hash passwords with a modern password-hashing algorithm such as Argon2id or bcrypt; never compare or store plaintext passwords.
- Remove default admin credentials and hardcoded password fallbacks.
- Require authentication and role/ownership authorization on upload, confirmation, batch submission, marks-management and student endpoints.
- Add upload-size limits, content-type/content-signature validation, rate limits and safe file retention.
- Keep API keys and database credentials in deployment secrets or ignored local environment files.
- Restrict CORS to trusted frontend origins.

## Notes

- Model weights are large binary artifacts. Consider Git LFS or a controlled model-artifact store for future versions.
- Use synthetic/anonymized sample data in a public portfolio repository.
- Do not claim fully automated mark publication: the current workflow includes faculty review/confirmation.
