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

def auto_bootstrap_database():
    from app.database.connection import SessionLocal
    from app.models.student import Student
    from app.models.faculty import Faculty
    import csv

    db = SessionLocal()
    try:
        admin = db.query(Faculty).filter(Faculty.role == "admin").first()
        if not admin:
            new_admin = Faculty(
                name="Admin",
                email="admin@markscan.edu",
                password="admin",
                role="admin"
            )
            db.add(new_admin)
            db.commit()
            print("🌱 Created initial admin account (admin / admin)")

        if db.query(Student).count() == 0:
            csv_path = Path(__file__).resolve().parent.parent / "data" / "students.csv"
            if csv_path.exists():
                from app.services.student_matcher import standardize_name, reverse_name_initials
                with open(csv_path, mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        raw_name = (row.get("name") or "").strip()
                        roll_no = (row.get("roll_no") or "").strip()
                        class_name = (row.get("class") or "").strip().replace('"', '')
                        board = (row.get("board") or "").strip()
                        phone = (row.get("phone") or "").strip()
                        email = (row.get("email") or "").strip()
                        school = (row.get("school_name") or "").strip()
                        pwd = (row.get("password") or "").strip().replace('"', '') or roll_no
                        mode = (row.get("mode_of_education") or "Offline").strip()
                        std_name = standardize_name(raw_name)
                        rev_name = reverse_name_initials(raw_name)

                        st = Student(
                            roll_no=roll_no,
                            name=raw_name,
                            standardized_name=std_name,
                            reversed_name=rev_name,
                            class_name=class_name,
                            board=board,
                            phone=phone,
                            email=email,
                            school_name=school,
                            password=pwd,
                            mode_of_education=mode,
                        )
                        db.add(st)
                db.commit()
                print(f"🌱 Auto-seeded {db.query(Student).count()} students from students.csv")

        # 3. Bootstrap Tests from CSV if table is empty
        from app.models.test import Test
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
    from app.services.seal_detector import get_model
    from app.services.ocr import get_easyocr_reader
    print("⏳ Pre-warming YOLO seal detector...")
    get_model()
    print("⏳ Pre-warming EasyOCR reader...")
    get_easyocr_reader()
    print("🌟 All AI models pre-warmed and ready to serve!")


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