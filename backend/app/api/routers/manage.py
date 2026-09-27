from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.connection import get_db
from app.models.fake_student import FakeStudent
from app.models.fake_mark import FakeMark
from app.models.test import Test

router = APIRouter(
    prefix="/manage",
    tags=["Manage Marks"]
)


class MarkUpdateRequest(BaseModel):
    student_id: int
    test_code: str
    marks_obtained: Optional[float] = None
    is_absent: Optional[bool] = False
    total_marks: Optional[float] = None


@router.get("/class_marks")
def get_class_marks(
    class_name: str = Query(..., description="Class e.g. 12, 11, 10"),
    board: str = Query(..., description="Board e.g. State Board, CBSE, ISC, ICSE"),
    test_code: str = Query(..., description="Test Code e.g. S12P35C1"),
    db: Session = Depends(get_db),
):
    cls_clean = class_name.strip()
    board_clean = board.strip()
    test_code_clean = test_code.strip()

    # 1. Fetch test details (max marks, subject)
    test_obj = db.query(Test).filter(Test.test_code.ilike(test_code_clean)).first()
    max_marks = float(test_obj.max_marks) if test_obj and test_obj.max_marks else None
    subject_name = test_obj.subject_name if test_obj else None
    test_title = test_obj.test_name if test_obj else test_code_clean

    # 2. Fetch all students for this class and board
    students = (
        db.query(FakeStudent)
        .filter(
            FakeStudent.class_name == cls_clean,
            FakeStudent.board.ilike(f"%{board_clean}%"),
        )
        .order_by(FakeStudent.name.asc())
        .all()
    )

    if not students:
        # Fallback without trailing spaces or case differences
        all_students = (
            db.query(FakeStudent)
            .filter(FakeStudent.class_name == cls_clean)
            .order_by(FakeStudent.name.asc())
            .all()
        )
        students = [
            s for s in all_students
            if s.board and (board_clean.lower() in s.board.lower() or s.board.lower() in board_clean.lower())
        ]

    # 3. Query fake_marks for this test code
    marks_entries = (
        db.query(FakeMark)
        .filter(FakeMark.test_code.ilike(test_code_clean))
        .order_by(FakeMark.id.desc())
        .all()
    )

    # Map student_id -> latest mark entry
    mark_by_student_id = {}
    for m in marks_entries:
        if m.student_id is not None and m.student_id not in mark_by_student_id:
            mark_by_student_id[m.student_id] = m

    # 4. Construct roster response
    student_records = []
    present_count = 0
    absent_count = 0

    for s in students:
        mark_entry = mark_by_student_id.get(s.id)

        # Check if student has posted marks
        if mark_entry and mark_entry.status != "ABSENT" and mark_entry.marks_obtained is not None:
            marks_val = mark_entry.marks_obtained
            t_marks = mark_entry.total_marks or max_marks
            is_absent = False
            present_count += 1
            mark_id = mark_entry.id
            status = mark_entry.status
        else:
            # If not posted, automatically assign Absent
            marks_val = None
            t_marks = max_marks
            is_absent = True
            absent_count += 1
            mark_id = mark_entry.id if mark_entry else None
            status = "ABSENT"

        student_records.append({
            "student_id": s.id,
            "roll_no": s.roll_no,
            "name": s.name,
            "class_name": s.class_name,
            "board": s.board,
            "mark_id": mark_id,
            "marks_obtained": marks_val,
            "total_marks": t_marks,
            "is_absent": is_absent,
            "status": status,
        })

    return {
        "status": "success",
        "class_name": cls_clean,
        "board": board_clean,
        "test_code": test_code_clean,
        "test_title": test_title,
        "subject_name": subject_name,
        "max_marks": max_marks,
        "total_students": len(student_records),
        "present_count": present_count,
        "absent_count": absent_count,
        "students": student_records,
    }


@router.post("/update_mark")
def update_mark(
    req: MarkUpdateRequest,
    db: Session = Depends(get_db),
):
    student = db.query(FakeStudent).filter(FakeStudent.id == req.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Find existing mark record for this student and test
    existing = (
        db.query(FakeMark)
        .filter(
            FakeMark.student_id == req.student_id,
            FakeMark.test_code.ilike(req.test_code.strip())
        )
        .order_by(FakeMark.id.desc())
        .first()
    )

    if req.is_absent or req.marks_obtained is None:
        # Mark as absent
        if existing:
            existing.status = "ABSENT"
            existing.marks_obtained = None
            db.commit()
            db.refresh(existing)
            mark_obj = existing
        else:
            mark_obj = FakeMark(
                student_id=req.student_id,
                matched_name=student.name,
                test_code=req.test_code.strip(),
                marks_obtained=None,
                total_marks=req.total_marks,
                status="ABSENT",
            )
            db.add(mark_obj)
            db.commit()
            db.refresh(mark_obj)
    else:
        # Update or create with submitted marks
        if existing:
            existing.marks_obtained = float(req.marks_obtained)
            if req.total_marks is not None:
                existing.total_marks = float(req.total_marks)
            existing.status = "SUBMITTED"
            existing.matched_name = student.name
            db.commit()
            db.refresh(existing)
            mark_obj = existing
        else:
            mark_obj = FakeMark(
                student_id=req.student_id,
                matched_name=student.name,
                test_code=req.test_code.strip(),
                marks_obtained=float(req.marks_obtained),
                total_marks=req.total_marks,
                status="SUBMITTED",
            )
            db.add(mark_obj)
            db.commit()
            db.refresh(mark_obj)

    return {
        "status": "success",
        "mark_id": mark_obj.id,
        "student_id": req.student_id,
        "student_name": student.name,
        "marks_obtained": mark_obj.marks_obtained,
        "total_marks": mark_obj.total_marks,
        "status_label": mark_obj.status,
    }
