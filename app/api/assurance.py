from fastapi import APIRouter
from pydantic import BaseModel

from app.services.risk_engine import (
    calculate_risk_score,
    get_risk_status
)


router = APIRouter(
    prefix="/assurance",
    tags=["Assurance"]
)


class RiskAssessmentRequest(BaseModel):
    integrity_risk: float = 0
    duplicate_risk: float = 0
    label_risk: float = 0
    model_risk: float = 0
    inference_risk: float = 0


@router.post("/risk")
def calculate_assurance_risk(
    request: RiskAssessmentRequest
):

    risk_score = calculate_risk_score(
        integrity_risk=request.integrity_risk,
        duplicate_risk=request.duplicate_risk,
        label_risk=request.label_risk,
        model_risk=request.model_risk,
        inference_risk=request.inference_risk
    )

    status = get_risk_status(risk_score)

    return {
        "risk_score": risk_score,
        "overall_status": status,
        "recommendation": status
    }