from sqlalchemy import Column, Integer, String

from app.database.base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    student_name = Column(String, nullable=False)
    register_number = Column(String, unique=True, nullable=False)
    department = Column(String)
    year = Column(Integer)
    