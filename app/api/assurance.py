from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.services.risk_engine import (
    calculate_risk_score,
    get_risk_status
)

from app.services.assurance_report import (
    generate_assurance_report
)

from app.database.connection import get_db
from app.database.crud import create_assurance_assessment


router = APIRouter(
    prefix="/assurance",
    tags=["Assurance"]
)


# ============================================================
# RISK ASSESSMENT REQUEST
# ============================================================

class RiskAssessmentRequest(BaseModel):
    integrity_risk: float = Field(default=0, ge=0, le=100)
    duplicate_risk: float = Field(default=0, ge=0, le=100)
    label_risk: float = Field(default=0, ge=0, le=100)
    model_risk: float = Field(default=0, ge=0, le=100)
    inference_risk: float = Field(default=0, ge=0, le=100)


# ============================================================
# FINDING SCHEMA
# ============================================================

class FindingRequest(BaseModel):
    asset_type: str
    asset_id: str
    severity: str
    reason: str
    evidence: str | None = None
    confidence: float | None = None
    recommendation: str | None = None


# ============================================================
# UNIFIED ASSURANCE REQUEST
# ============================================================

class AssuranceReportRequest(BaseModel):
    integrity_risk: float = Field(default=0, ge=0, le=100)
    duplicate_risk: float = Field(default=0, ge=0, le=100)
    label_risk: float = Field(default=0, ge=0, le=100)
    model_risk: float = Field(default=0, ge=0, le=100)
    inference_risk: float = Field(default=0, ge=0, le=100)

    findings: list[FindingRequest] = []


# ============================================================
# EXISTING RISK API
# ============================================================

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


# ============================================================
# UNIFIED ASSURANCE REPORT
# ============================================================

@router.post("/report")
def create_assurance_report(
    request: AssuranceReportRequest,
    db: Session = Depends(get_db)
):

    findings = [
        finding.model_dump()
        for finding in request.findings
    ]

    report = generate_assurance_report(
        integrity_risk=request.integrity_risk,
        duplicate_risk=request.duplicate_risk,
        label_risk=request.label_risk,
        model_risk=request.model_risk,
        inference_risk=request.inference_risk,
        findings=findings
    )

    import uuid

    assurance_id = (
        f"ASSURE-{uuid.uuid4().hex[:8].upper()}"
    )

    create_assurance_assessment(
        db=db,
        assurance_id=assurance_id,
        overall_status=report["overall_status"],
        risk_score=report["risk_score"]
    )

    report["assurance_id"] = assurance_id
    report["database_saved"] = True

    return report