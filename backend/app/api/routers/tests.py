from fastapi import APIRouter
from sqlalchemy import text

from app.database.connection import engine

router = APIRouter(
    prefix="/tests",
    tags=["Tests"]
)


@router.get("/")
def get_tests():

    query = text("""
        SELECT
            id,
            test_code,
            test_name,
            class_name,
            max_marks
        FROM tests
        ORDER BY id
    """)

    with engine.connect() as connection:
        result = connection.execute(query).mappings().all()

    return {
        "status": "success",
        "tests": [dict(row) for row in result]
    }