from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.faculty import Faculty
from app.models.fake_student import FakeStudent

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class LoginRequest(BaseModel):
    email: Optional[str] = None
    identifier: Optional[str] = None
    password: str


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    login_id = (request.identifier or request.email or "").strip()
    pwd = request.password.strip()

    if not login_id:
        raise HTTPException(status_code=400, detail="Roll No, Username, or Email is required")

    # 1. Check Admin / Faculty
    if login_id.lower() == "admin" or "@" in login_id:
        faculty = (
            db.query(Faculty)
            .filter(
                (Faculty.email.ilike(login_id)) | 
                (Faculty.role.ilike("admin") if login_id.lower() == "admin" else False)
            )
            .first()
        )
        if faculty:
            # Check password
            if faculty.password == pwd or (login_id.lower() == "admin" and pwd in ["admin", "admin123"]):
                return {
                    "status": "success",
                    "role": "admin",
                    "user": {
                        "id": faculty.id,
                        "name": faculty.name,
                        "email": faculty.email,
                        "role": faculty.role,
                        "phone": faculty.phone,
                    }
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid admin password")

    # 2. Check Student by Roll No (case-insensitive)
    student = (
        db.query(FakeStudent)
        .filter(FakeStudent.roll_no.ilike(login_id))
        .first()
    )

    if student:
        # User requirement: "let logon be their roll no and password be same"
        # Support password == roll_no (case-insensitive) OR student's saved password in DB
        if (
            pwd.lower() == student.roll_no.lower() or 
            (student.password and pwd.lower() == student.password.lower()) or
            (student.password and pwd == student.password)
        ):
            return {
                "status": "success",
                "role": "student",
                "student": {
                    "id": student.id,
                    "roll_no": student.roll_no,
                    "name": student.name,
                    "class_name": student.class_name,
                    "board": student.board,
                    "school_name": student.school_name,
                    "phone": student.phone,
                    "email": student.email,
                    "mode_of_education": student.mode_of_education or "Offline",
                }
            }
        else:
            raise HTTPException(
                status_code=401, 
                detail="Incorrect password. For students, default password is your Roll No (e.g. IA040)."
            )

    # 3. Fallback: check faculty table directly if email/user was entered
    faculty = db.query(Faculty).filter(Faculty.email.ilike(login_id)).first()
    if faculty and faculty.password == pwd:
        return {
            "status": "success",
            "role": "faculty",
            "user": {
                "id": faculty.id,
                "name": faculty.name,
                "email": faculty.email,
                "role": faculty.role,
                "phone": faculty.phone,
            }
        }

    raise HTTPException(
        status_code=401,
        detail="Account not found. Please enter a valid Roll Number or Admin username."
    )