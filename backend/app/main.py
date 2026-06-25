from fastapi import FastAPI

app = FastAPI(
    title="MarkScan AI API",
    description="Backend API for MarkScan AI",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to MarkScan AI"
    }