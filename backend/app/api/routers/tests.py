from typing import Optional
from fastapi import APIRouter, Query
from sqlalchemy import text

from app.database.connection import engine

router = APIRouter(
    prefix="/tests",
    tags=["Tests"]
)


@router.get("/")
def get_tests(
    class_name: Optional[str] = Query(None),
    board: Optional[str] = Query(None),
    subject: Optional[str] = Query(None),
):
    query_str = """
        SELECT
            id,
            test_code,
            test_name,
            class_name,
            board,
            subject_name,
            max_marks
        FROM tests
        WHERE 1=1
    """
    params = {}

    if class_name and class_name.strip() and class_name.strip().lower() not in ["all", "all classes"]:
        digits = "".join([c for c in class_name if c.isdigit()])
        if digits:
            query_str += " AND class_name ILIKE :class_digit"
            params["class_digit"] = f"%{digits}%"
        else:
            query_str += " AND class_name ILIKE :class_name"
            params["class_name"] = f"%{class_name.strip()}%"

    if board and board.strip() and board.strip().lower() not in ["all", "all boards"]:
        b_clean = board.strip()
        prefix = "SB%" if "state" in b_clean.lower() else f"%{b_clean}%"
        query_str += " AND (board ILIKE :board OR class_name ILIKE :board_prefix)"
        params["board"] = f"%{b_clean}%"
        params["board_prefix"] = prefix

    if subject and subject.strip() and subject.strip().lower() not in ["all", "all subjects"]:
        query_str += " AND subject_name ILIKE :subject"
        params["subject"] = f"%{subject.strip()}%"

    query_str += " ORDER BY id"

    with engine.connect() as connection:
        result = connection.execute(text(query_str), params).mappings().all()

    return {
        "status": "success",
        "tests": [dict(row) for row in result]
    }