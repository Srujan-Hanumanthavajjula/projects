from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.database.models import Finding
from app.services.finding_service import save_finding


router = APIRouter(
    prefix="/findings",
    tags=["Findings"]
)


# ============================================================
# FINDING REQUEST
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
# SAVE FINDING
# ============================================================

@router.post("/save")
def save_finding_api(
    request: FindingRequest,
    db: Session = Depends(get_db)
):

    finding = save_finding(
        db=db,
        asset_type=request.asset_type,
        asset_id=request.asset_id,
        severity=request.severity,
        reason=request.reason,
        evidence=request.evidence,
        confidence=request.confidence,
        recommendation=request.recommendation
    )

    return {
        "status": "finding_saved",
        "finding": {
            "finding_id": finding.id,
            "asset_type": finding.asset_type,
            "asset_id": finding.asset_id,
            "severity": finding.severity,
            "reason": finding.reason,
            "evidence": finding.evidence,
            "confidence": finding.confidence,
            "recommendation": finding.recommendation
        },
        "database_saved": True
    }


# ============================================================
# GET ALL FINDINGS
# ============================================================

@router.get("/")
def get_findings(
    db: Session = Depends(get_db)
):

    findings = (
        db.query(Finding)
        .order_by(Finding.id.desc())
        .all()
    )

    return {
        "total_findings": len(findings),
        "findings": [
            {
                "finding_id": finding.id,
                "asset_type": finding.asset_type,
                "asset_id": finding.asset_id,
                "severity": finding.severity,
                "reason": finding.reason,
                "evidence": finding.evidence,
                "confidence": finding.confidence,
                "recommendation": finding.recommendation,
                "created_at": finding.created_at
            }
            for finding in findings
        ]
    }