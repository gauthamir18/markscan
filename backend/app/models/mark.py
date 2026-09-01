from sqlalchemy import Column, Integer, String, ForeignKey

from app.database.base import Base


class Mark(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False,
    )

    test_id = Column(
        Integer,
        ForeignKey("tests.id"),
        nullable=False,
    )

    session_id = Column(
        Integer,
        ForeignKey("scan_sessions.id"),
        nullable=True,
    )

    marks = Column(Integer, nullable=False)

    status = Column(
        String,
        nullable=False,
        default="SCANNED",
    )