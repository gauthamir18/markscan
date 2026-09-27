import os
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.fake_student import FakeStudent
from app.services.gemini_reader import analyze_seal_vision
from app.services.student_matcher import clean_ocr_name

def decide_hybrid(
    seal_image_path: str,
    yolo_confidence: float,
    local_student: Optional[FakeStudent],
    local_score: float,
    local_display_name: str,
    top_candidates: List[Dict[str, Any]],
    local_marks: Dict[str, Any],
    local_qp_code: str,
    selected_class: Optional[str] = None,
    test_code: Optional[str] = None,
    db: Optional[Session] = None,
) -> Dict[str, Any]:
    """
    Hybrid Decision Engine:
    Combines YOLO detection, Local OCR + Database Candidate matching, and Vision AI verification.
    """
    vision_ai_used = False
    vision_reasoning = ""
    vision_model = ""

    final_student = local_student
    final_student_name = local_display_name
    final_confidence = local_score
    needs_verification = (local_score < 75.0 or local_student is None)

    final_obtained = local_marks.get("obtained")
    final_total = local_marks.get("total")
    final_test_code = test_code or local_qp_code or ""

    # 1. Attempt Vision AI analysis if seal crop exists
    if seal_image_path and os.path.exists(seal_image_path):
        vision_res = analyze_seal_vision(
            seal_image_path=seal_image_path,
            candidate_students=top_candidates,
            selected_class=selected_class,
            default_test_code=test_code,
        )

        if vision_res is not None:
            vision_ai_used = True
            vision_reasoning = vision_res.get("reasoning", "")
            vision_model = vision_res.get("model_used", "")
            v_name = vision_res.get("student_name", "").strip()

            # Resolve Vision AI student name against PostgreSQL
            matched_db_student = None
            if v_name and db is not None:
                # Direct check against top candidates
                for c in top_candidates:
                    if c["name"].lower() == v_name.lower():
                        matched_db_student = db.query(FakeStudent).filter(FakeStudent.id == c["id"]).first()
                        break
                
                # Broad check against database
                if matched_db_student is None:
                    matched_db_student = db.query(FakeStudent).filter(FakeStudent.name.ilike(v_name)).first()
                if matched_db_student is None:
                    # Check first name token
                    first_tok = v_name.split()[0]
                    matched_db_student = db.query(FakeStudent).filter(FakeStudent.name.ilike(f"%{first_tok}%")).first()

            if matched_db_student is not None:
                final_student = matched_db_student
                final_student_name = matched_db_student.name
                final_confidence = max(95.0, round(vision_res.get("confidence", 0.98) * 100.0, 1))
                needs_verification = False
            elif v_name:
                final_student_name = v_name
                final_confidence = round(vision_res.get("confidence", 0.90) * 100.0, 1)

            # Vision AI Marks
            v_obtained = vision_res.get("marks_obtained")
            v_total = vision_res.get("marks_total")

            if v_obtained is not None:
                final_obtained = v_obtained
            if v_total is not None:
                final_total = v_total

            # Vision AI QP Code (only if test_code was not specified)
            v_qp = vision_res.get("qp_code", "").strip()
            if v_qp and not (test_code and test_code.strip()):
                final_test_code = v_qp

    # If test code is detected, resolve against tests table in database
    if final_test_code and db is not None:
        try:
            from sqlalchemy import text as sa_text
            t_row = db.execute(
                sa_text("SELECT test_code, max_marks FROM tests WHERE test_code ILIKE :tc OR :tc ILIKE ('%' || test_code || '%') LIMIT 1"),
                {"tc": final_test_code.strip()}
            ).fetchone()
            if t_row:
                final_test_code = t_row[0]
                if (final_total is None or final_total == 0) and t_row[1] is not None:
                    final_total = float(t_row[1])
        except Exception:
            pass

    # Clamping
    final_confidence = min(100.0, max(0.0, final_confidence))

    return {
        "student": final_student,
        "student_name": final_student_name,
        "matched_student_id": final_student.id if final_student else None,
        "match_confidence": final_confidence,
        "needs_verification": needs_verification,
        "obtained_marks": final_obtained,
        "total_marks": final_total,
        "test_code": final_test_code,
        "top_candidates": top_candidates,
        "vision_ai_used": vision_ai_used,
        "vision_model": vision_model,
        "vision_reasoning": vision_reasoning,
    }
