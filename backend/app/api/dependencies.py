from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.faculty import Faculty
from app.models.student import Student
from app.core.security import JWT_ALGORITHM, JWT_ISSUER, JWT_SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = __import__("jwt").decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER,
        )
        user_id = int(payload.get("sub", ""))
        role = str(payload.get("role", "")).lower()
    except (InvalidTokenError, TypeError, ValueError):
        raise credentials_error

    if role == "student":
        user = db.query(Student).filter(Student.id == user_id).first()
        if user is None:
            raise credentials_error
        return {"id": user.id, "role": "student", "roll_no": user.roll_no}

    if role in {"admin", "faculty"}:
        user = db.query(Faculty).filter(Faculty.id == user_id).first()
        if user is None or str(user.role).lower() not in {"admin", "faculty"}:
            raise credentials_error
        return {"id": user.id, "role": str(user.role).lower(), "email": user.email}

    raise credentials_error


def require_staff(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user["role"] not in {"admin", "faculty"}:
        raise HTTPException(status_code=403, detail="Faculty or admin access required.")
    return current_user
