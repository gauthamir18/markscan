from sqlalchemy import Column, Integer, String
from app.database.base import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    roll_no = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    standardized_name = Column(String, index=True, nullable=False)
    reversed_name = Column(String, index=True, nullable=True)
    class_name = Column(String, nullable=True)
    board = Column(String, nullable=True)
    school_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    password = Column(String, nullable=True)
    mode_of_education = Column(String, nullable=True, default="Offline")


# Backward compatibility alias
FakeStudent = Student
