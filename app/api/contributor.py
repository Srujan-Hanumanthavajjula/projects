from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db

from app.database.crud import (
    create_contributor_asset,
    get_contributor_assets,
    get_findings_for_assets
)

from app.services.contributor_risk import (
    calculate_contributor_risk
)


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


class ContributorAssetRequest(BaseModel):
    contributor_id: str
    asset_type: str
    asset_id: str


# ============================================================
# MANUAL CONTRIBUTOR RISK ASSESSMENT
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


# ============================================================
# REGISTER ASSET TO CONTRIBUTOR
# ============================================================

@router.post("/asset")
def register_contributor_asset(
    request: ContributorAssetRequest,
    db: Session = Depends(get_db)
):

    asset = create_contributor_asset(
        db=db,
        contributor_id=request.contributor_id,
        asset_type=request.asset_type,
        asset_id=request.asset_id
    )

    return {
        "status": "contributor_asset_registered",
        "mapping_id": asset.id,
        "contributor_id": asset.contributor_id,
        "asset_type": asset.asset_type,
        "asset_id": asset.asset_id,
        "database_saved": True
    }


# ============================================================
# GET CONTRIBUTOR RISK FROM DATABASE
# ============================================================

@router.get("/{contributor_id}/risk")
def contributor_risk(
    contributor_id: str,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Find assets belonging to contributor
    # --------------------------------------------------------

    assets = get_contributor_assets(
        db=db,
        contributor_id=contributor_id
    )

    if not assets:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No assets registered for "
                f"contributor '{contributor_id}'"
            )
        )

    # --------------------------------------------------------
    # Find findings belonging to those assets
    # --------------------------------------------------------

    database_findings = get_findings_for_assets(
        db=db,
        assets=assets
    )

    # --------------------------------------------------------
    # Convert database findings to risk-engine format
    # --------------------------------------------------------

    findings = []

    for finding in database_findings:

        findings.append({
            "asset_type": finding.asset_type,
            "asset_id": finding.asset_id,
            "severity": finding.severity,
            "reason": finding.reason,
            "evidence": finding.evidence,
            "confidence": (
                finding.confidence
                if finding.confidence is not None
                else 1.0
            ),
            "recommendation": finding.recommendation
        })

    # --------------------------------------------------------
    # Calculate contributor risk
    # --------------------------------------------------------

    result = calculate_contributor_risk(
        contributor_id=contributor_id,
        findings=findings
    )

    # --------------------------------------------------------
    # Return complete contributor assurance
    # --------------------------------------------------------

    return {
        "status": "contributor_risk_assessment_completed",

        "result": result,

        "registered_assets": [
            {
                "asset_type": asset.asset_type,
                "asset_id": asset.asset_id
            }
            for asset in assets
        ],

        "findings": findings,

        "database_findings_count": len(findings)
    }