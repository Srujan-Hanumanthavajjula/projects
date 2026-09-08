from fastapi import FastAPI

from app.api.dataset import router as dataset_router
from app.api.model import router as model_router
from app.api.inference import router as inference_router
from app.api.assurance import router as assurance_router
from app.api.ood import router as ood_router
from app.api.trigger import router as trigger_router
from app.api.model_behavior import router as model_behavior_router
from app.api.replay import router as replay_router
from app.api.audit import router as audit_router
from app.api.findings import router as findings_router
from app.api.contributor import router as contributor_router

from app.database.connection import Base, engine
from app.database import models


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="SIH 26228 - Computer Vision Integrity Assurance",
    description="Integrity assurance framework for datasets, models and inference outputs",
    version="1.0.0"
)


# Register API routers
app.include_router(dataset_router)
app.include_router(model_router)
app.include_router(inference_router)
app.include_router(assurance_router)
app.include_router(ood_router)
app.include_router(trigger_router)
app.include_router(model_behavior_router)
app.include_router(replay_router)
app.include_router(audit_router)
app.include_router(findings_router)
app.include_router(contributor_router)


@app.get("/")
def root():
    return {
        "message": "SIH 26228 Integrity Assurance Backend",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }