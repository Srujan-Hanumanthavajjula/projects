from fastapi import FastAPI
from app.api.dataset import router as dataset_router
from app.api.model import router as model_router


app = FastAPI(
    title="SIH 26228 - Computer Vision Integrity Assurance",
    description="Integrity assurance framework for datasets, models and inference outputs",
    version="1.0.0"
)


# Register API routers
app.include_router(dataset_router)
app.include_router(model_router)


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