from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.contributor_risk import calculate_contributor_risk


router = APIRouter(
    prefix="/contributor",
    tags=["Contributor Risk"]
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class ContributorFinding(BaseModel):
    asset_type: str
    asset_id: str
    severity: str
    reason: str | None = None
    evidence: str | None = None
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0
    )
    recommendation: str | None = None


class ContributorRiskRequest(BaseModel):
    contributor_id: str
    findings: list[ContributorFinding] = []


# ============================================================
# CONTRIBUTOR RISK ASSESSMENT
# ============================================================

@router.post("/risk")
def calculate_risk(
    request: ContributorRiskRequest
):

    findings = [
        finding.model_dump()
        for finding in request.findings
    ]

    result = calculate_contributor_risk(
        contributor_id=request.contributor_id,
        findings=findings
    )

    return {
        "status": "contributor_risk_assessment_completed",
        "result": result
    }