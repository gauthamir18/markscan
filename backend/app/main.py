import warnings
warnings.filterwarnings("ignore", message=".*automatic function calling.*")
warnings.filterwarnings("ignore", message=".*Direct use of automatic function calling.*")

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

print("\n" + "=" * 48)
print("🚀 MarkScan AI: Initializing backend...")
print("=" * 48)

from app.api.routers import upload
from app.database.connection import engine
from app.database.base import Base
from app.api.routers import auth
from app.api.routers import tests
from app.api.routers import manage
from app.api.routers import student

# Import models so SQLAlchemy knows about them
from app.models.student import Student
from app.models.faculty import Faculty
from app.models.test import Test
from app.models.mark import Mark

Base.metadata.create_all(bind=engine)
print("✅ PostgreSQL connected & schema ready.")

app = FastAPI(
    title="MarkScan AI API",
    description="Backend API for MarkScan AI",
    version="1.0.0"
)

def standardize_name(name: str) -> str:
    if not name:
        return ""
    import re
    return " ".join(re.sub(r"[^a-zA-Z\s]", " ", name).split()).strip().title()


def reverse_name_initials(name: str) -> str:
    if not name:
        return ""
    parts = name.strip().split()
    if len(parts) > 1:
        return f"{parts[-1]} {' '.join(parts[:-1])}"
    return name


def auto_bootstrap_database():
    from app.database.connection import SessionLocal
    from app.models.student import Student
    from app.models.faculty import Faculty
    from app.models.test import Test
    from sqlalchemy import inspect, text
    import csv

    # 1. Check if PostgreSQL has legacy schema
    try:
        inspector = inspect(engine)
        if "students" in inspector.get_table_names():
            cols = [c["name"] for c in inspector.get_columns("students")]
            if "roll_no" not in cols:
                print("🔄 Migrating legacy schema: dropping obsolete tables...")
                with engine.connect() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS marks CASCADE;"))
                    conn.execute(text("DROP TABLE IF EXISTS scan_sessions CASCADE;"))
                    conn.execute(text("DROP TABLE IF EXISTS students CASCADE;"))
                    conn.execute(text("DROP TABLE IF EXISTS fake_students CASCADE;"))
                    conn.execute(text("DROP TABLE IF EXISTS fake_marks CASCADE;"))
                    conn.commit()
                Base.metadata.create_all(bind=engine)
                print("✅ Re-created tables with latest schema.")
    except Exception as e:
        print(f"Schema check error: {e}")

    db = SessionLocal()
    try:
        # Admin accounts must be provisioned securely out-of-band. Never create a
        # predictable default admin password during application startup.

        # 3. Bootstrap Tests from CSV if table is empty
        if db.query(Test).count() == 0:
            tests_csv_path = Path(__file__).resolve().parent.parent / "data" / "tests.csv"
            if tests_csv_path.exists():
                with open(tests_csv_path, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        t = Test(
                            test_code=row.get("test_code") or "",
                            test_name=row.get("test_name") or "",
                            subject_name=row.get("subject_name") or "",
                            class_name=row.get("class_name") or "",
                            max_marks=float(row.get("max_marks") or 35.0),
                        )
                        db.add(t)
                db.commit()
                print(f"🌱 Auto-seeded {db.query(Test).count()} tests from tests.csv")
    except Exception as e:
        print(f"⚠️ Bootstrapping warning: {e}")
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    auto_bootstrap_database()
    print("🌟 MarkScan AI server ready and accepting traffic!")


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
app.include_router(manage.router)
app.include_router(student.router)


@app.get("/")
def root():
    return {
        "message": "Welcome to MarkScan AI"
    }