from sqlalchemy import Column, Integer, String, ForeignKey

from app.database.base import Base


class ScanSession(Base):
    __tablename__ = "scan_sessions"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=False)
    class_name = Column(String, nullable=False)
    test_code = Column(String, nullable=False)
    status = Column(String, nullable=False, default="ACTIVE")