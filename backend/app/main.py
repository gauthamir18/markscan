from fastapi import FastAPI
from app.api.routers import upload
from app.database.connection import engine
from app.database.base import Base

# Import models so SQLAlchemy knows about them
from app.models.student import Student
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="MarkScan AI API",
    description="Backend API for MarkScan AI",
    version="1.0.0"
)

app.include_router(upload.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to MarkScan AI"
    }