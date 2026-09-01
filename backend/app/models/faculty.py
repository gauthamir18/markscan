from sqlalchemy import Column, Integer, String

from app.database.base import Base


class Faculty(Base):
    __tablename__ = "faculty"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=False)