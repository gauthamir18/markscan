from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routers import upload
from app.database.connection import engine
from app.database.base import Base
from app.api.routers import auth
from app.api.routers import tests

# Import models so SQLAlchemy knows about them
from app.models.student import Student
from app.models.faculty import Faculty
from app.models.test import Test
from app.models.mark import Mark
from app.models.scan_session import ScanSession


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="MarkScan AI API",
    description="Backend API for MarkScan AI",
    version="1.0.0"
)


# Serve uploaded images/cropped seals to the Flutter app
BASE_DIR = Path(__file__).resolve().parents[1]
UPLOADS_DIR = BASE_DIR / "uploads"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOADS_DIR)),
    name="uploads",
)


app.include_router(upload.router)
app.include_router(auth.router)
app.include_router(tests.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to MarkScan AI"
    }