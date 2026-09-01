from sqlalchemy import Column, Integer, String

from app.database.base import Base


class Test(Base):
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    test_code = Column(String, unique=True, nullable=False, index=True)
    test_name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    max_marks = Column(Integer, nullable=False, default=20)