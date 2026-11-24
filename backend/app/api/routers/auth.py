from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.faculty import Faculty
from app.models.student import Student
from app.core.security import create_access_token, verify_password_and_upgrade

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: Optional[str] = None
    identifier: Optional[str] = None
    password: str


def _success_response(user_id: int, role: str, user_data: dict) -> dict:
    return {
        "status": "success",
        "role": role,
        "access_token": create_access_token(user_id, role),
        "token_type": "bearer",
        **user_data,
    }


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    login_id = (request.identifier or request.email or "").strip()
    password = request.password

    if not login_id or not password:
        raise HTTPException(status_code=400, detail="Username, email or roll number and password are required.")

    # Admin may sign in using the legacy username alias or the account email.
    if login_id.lower() == "admin":
        faculty = db.query(Faculty).filter(Faculty.role.ilike("admin")).first()
    else:
        faculty = db.query(Faculty).filter(Faculty.email.ilike(login_id)).first()

    if faculty is not None:
        valid, replacement = verify_password_and_upgrade(password, faculty.password)
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid username or password.")
        if replacement:
            faculty.password = replacement
            db.commit()
        role = str(faculty.role).lower()
        return _success_response(
            faculty.id,
            role,
            {"user": {
                "id": faculty.id,
                "name": faculty.name,
                "email": faculty.email,
                "role": faculty.role,
                "phone": faculty.phone,
            }},
        )

    student = db.query(Student).filter(Student.roll_no.ilike(login_id)).first()
    if student is not None:
        valid, replacement = verify_password_and_upgrade(password, student.password or "")
        if not valid:
            raise HTTPException(status_code=401, detail="Invalid username or password.")
        if replacement:
            student.password = replacement
            db.commit()
        return _success_response(
            student.id,
            "student",
            {"student": {
                "id": student.id,
                "roll_no": student.roll_no,
                "name": student.name,
                "class_name": student.class_name,
                "board": student.board,
                "school_name": student.school_name,
                "phone": student.phone,
                "email": student.email,
                "mode_of_education": student.mode_of_education or "Offline",
            }},
        )

    raise HTTPException(status_code=401, detail="Invalid username or password.")
