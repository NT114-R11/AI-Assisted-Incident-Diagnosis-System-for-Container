from fastapi import FastAPI

from app.routers.webhook import router as webhook_router


app = FastAPI(
    title="AI Incident Diagnosis Service",
    version="0.1.0",
)


app.include_router(webhook_router)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ai-diagnosis-service",
    }


@app.get("/ready")
def ready():
    return {
        "status": "ready",
        "service": "ai-diagnosis-service",
    }