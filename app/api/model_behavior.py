from fastapi import APIRouter
from pydantic import BaseModel

from app.detectors.model_behavior_detector import analyze_model_behavior


router = APIRouter(
    prefix="/model-behavior",
    tags=["Model Behavior"]
)


class Prediction(BaseModel):
    image: str
    prediction: str
    confidence: float


class ModelBehaviorRequest(BaseModel):
    predictions: list[Prediction]
    confidence_threshold: float = 0.5


@router.post("/analyze")
def analyze_behavior(request: ModelBehaviorRequest):

    predictions = [
        {
            "image": item.image,
            "prediction": item.prediction,
            "confidence": item.confidence
        }
        for item in request.predictions
    ]

    result = analyze_model_behavior(
        predictions=predictions,
        confidence_threshold=request.confidence_threshold
    )

    return {
        "status": "analysis_completed",
        "results": result
    }