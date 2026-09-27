from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from app.database.base import Base


class FakeMark(Base):
    __tablename__ = "fake_marks"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("fake_students.id"),
        nullable=True,
    )

    raw_ocr_name = Column(String, nullable=True)
    matched_name = Column(String, nullable=True)
    match_confidence = Column(Float, nullable=True)

    test_code = Column(String, nullable=True)

    raw_ocr_marks = Column(String, nullable=True)
    marks_obtained = Column(Float, nullable=True)
    total_marks = Column(Float, nullable=True)

    seal_image_url = Column(String, nullable=True)

    status = Column(
        String,
        nullable=False,
        default="SCANNED",
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )
