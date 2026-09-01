from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text

from app.database.connection import engine

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(request: LoginRequest):

    query = text("""
        SELECT id, name, role, phone, email
        FROM faculty
        WHERE email = :email
        AND password = :password
    """)

    with engine.connect() as connection:
        result = connection.execute(
            query,
            {
                "email": request.email,
                "password": request.password,
            }
        ).mappings().first()

    if not result:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "status": "success",
        "faculty": dict(result)
    }