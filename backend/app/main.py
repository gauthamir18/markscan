from fastapi import FastAPI
from app.api.routers import upload

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