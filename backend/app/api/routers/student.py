from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.fake_student import FakeStudent
from app.models.fake_mark import FakeMark
from app.models.test import Test

router = APIRouter(
    prefix="/student",
    tags=["Student Portal"]
)


@router.get("/{roll_no}/profile_and_marks")
def get_student_profile_and_marks(
    roll_no: str,
    month: Optional[str] = Query(None, description="Month in YYYY-MM format"),
    db: Session = Depends(get_db),
):
    clean_roll = roll_no.strip()
    student = db.query(FakeStudent).filter(FakeStudent.roll_no.ilike(clean_roll)).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 1. Fetch all tests for this student's class and board
    tests = (
        db.query(Test)
        .filter(
            (Test.class_name.ilike(f"%{student.class_name}%")) |
            (Test.class_name.ilike(f"%{student.board or ''}%"))
        )
        .order_by(Test.id.asc())
        .all()
    )

    # 2. Fetch all fake_marks recorded for this student
    marks_entries = (
        db.query(FakeMark)
        .filter(FakeMark.student_id == student.id)
        .order_by(FakeMark.created_at.desc(), FakeMark.id.desc())
        .all()
    )

    # Map test_code (lowercased) -> mark entry
    mark_by_code = {}
    for m in marks_entries:
        if m.test_code:
            code_key = m.test_code.strip().lower()
            if code_key not in mark_by_code:
                mark_by_code[code_key] = m

    # 3. Build test history rows (similar to the Next.js attendance rows)
    attendance_rows = []
    
    # First, add all tests that have marks recorded
    seen_tests = set()
    for m in marks_entries:
        if not m.test_code:
            continue
        code_key = m.test_code.strip().lower()
        if code_key in seen_tests:
            continue
        seen_tests.add(code_key)

        # Find matching test meta if available
        test_meta = next((t for t in tests if t.test_code.strip().lower() == code_key), None)
        subj = test_meta.subject_name if test_meta and test_meta.subject_name else ("Physics" if "P" in m.test_code else "Maths")
        subj_id = 2 if "physic" in subj.lower() else 1
        t_name = test_meta.test_name if test_meta else m.test_code

        date_str = m.created_at.strftime("%Y-%m-%d") if m.created_at else datetime.now().strftime("%Y-%m-%d")
        is_absent = (m.status == "ABSENT" or m.marks_obtained is None)

        attendance_rows.append({
            "mark_id": m.id,
            "test_code": m.test_code,
            "test_name": t_name,
            "subject_id": subj_id,
            "subject_name": subj,
            "attendance_date": date_str,
            "test_date": date_str,
            "marks_obtained": m.marks_obtained,
            "total_marks": m.total_marks or (float(test_meta.max_marks) if test_meta else 35.0),
            "status": "absent" if is_absent else "present",
        })

    # Second, for any tests in tests table for this class that have no marks yet, include them as not entered / absent
    for t in tests:
        code_key = t.test_code.strip().lower()
        if code_key not in seen_tests:
            seen_tests.add(code_key)
            subj = t.subject_name or ("Physics" if "P" in t.test_code else "Maths")
            subj_id = 2 if "physic" in subj.lower() else 1
            attendance_rows.append({
                "mark_id": None,
                "test_code": t.test_code,
                "test_name": t.test_name,
                "subject_id": subj_id,
                "subject_name": subj,
                "attendance_date": datetime.now().strftime("%Y-%m-%d"),
                "test_date": datetime.now().strftime("%Y-%m-%d"),
                "marks_obtained": None,
                "total_marks": float(t.max_marks) if t.max_marks else 35.0,
                "status": "not_entered",
            })

    # Sort descending by date
    attendance_rows.sort(key=lambda x: x["attendance_date"], reverse=True)

    # Filter by month if provided (e.g. "2026-09")
    if month:
        filtered_rows = [
            r for r in attendance_rows
            if r["attendance_date"].startswith(month)
        ]
    else:
        filtered_rows = attendance_rows

    present_count = len([r for r in filtered_rows if r["status"] == "present"])
    absent_count = len([r for r in filtered_rows if r["status"] == "absent"])
    not_entered_count = len([r for r in filtered_rows if r["status"] == "not_entered"])

    last_updated = filtered_rows[0]["attendance_date"] if filtered_rows else None

    return {
        "status": "success",
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
        },
        "selected_month": month,
        "summary": {
            "total": len(filtered_rows),
            "present": present_count,
            "absent": absent_count,
            "not_entered": not_entered_count,
            "last_updated": last_updated,
        },
        "attendance": filtered_rows,
        "marks": filtered_rows,
    }
