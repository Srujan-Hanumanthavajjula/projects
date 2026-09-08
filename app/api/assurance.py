from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from pathlib import Path

from app.services.risk_engine import (
    calculate_risk_score,
    get_risk_status
)

from app.services.assurance_report import (
    generate_assurance_report
)

from app.services.assurance_orchestrator import (
    generate_assurance_decision
)

from app.services.dataset_assurance import (
    run_dataset_detectors
)

from app.services.hashing import (
    calculate_sha256
)

from app.services.finding_service import (
    findings_from_detector_results,
    save_findings
)

from app.services.audit_service import (
    record_audit_event
)

from app.database.connection import get_db
from app.database.crud import create_assurance_assessment
from app.database.models import Dataset

import uuid


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
# UNIFIED ASSURANCE REPORT REQUEST
# ============================================================

class AssuranceReportRequest(BaseModel):
    integrity_risk: float = Field(default=0, ge=0, le=100)
    duplicate_risk: float = Field(default=0, ge=0, le=100)
    label_risk: float = Field(default=0, ge=0, le=100)
    model_risk: float = Field(default=0, ge=0, le=100)
    inference_risk: float = Field(default=0, ge=0, le=100)

    findings: list[FindingRequest] = []


# ============================================================
# ORCHESTRATOR REQUEST
# ============================================================

class OrchestratorRequest(BaseModel):
    detector_results: dict
    findings: list[FindingRequest] = []


# ============================================================
# BASIC RISK API
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


# ============================================================
# ASSURANCE ORCHESTRATOR
# ============================================================

@router.post("/orchestrate")
def orchestrate_assurance(
    request: OrchestratorRequest
):

    findings = [
        finding.model_dump()
        for finding in request.findings
    ]

    result = generate_assurance_decision(
        detector_results=request.detector_results,
        findings=findings
    )

    return {
        "status": "assurance_completed",
        "results": result
    }


# ============================================================
# DATASET ASSURANCE
# ============================================================

@router.post("/dataset/{dataset_id}")
def run_dataset_assurance(
    dataset_id: str,
    db: Session = Depends(get_db)
):
    """
    Run the complete dataset assurance pipeline.

    Pipeline:

    Registered Dataset
            ↓
    SHA-256 Integrity Verification
            ↓
    Dataset Detectors
            ↓
    Findings
            ↓
    Risk Assessment
            ↓
    Assurance Decision
            ↓
    Database + Audit Trail
    """

    # --------------------------------------------------------
    # Find registered dataset
    # --------------------------------------------------------

    dataset = (
        db.query(Dataset)
        .filter(Dataset.dataset_id == dataset_id)
        .first()
    )

    if dataset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset '{dataset_id}' not found"
        )

    # --------------------------------------------------------
    # Locate dataset file
    # --------------------------------------------------------

    dataset_path = (
        Path("uploads")
        / "datasets"
        / f"{dataset.dataset_id}_{dataset.filename}"
    )

    if not dataset_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Dataset file not found: {dataset_path}"
        )

    # --------------------------------------------------------
    # Verify dataset SHA-256 integrity
    # --------------------------------------------------------

    actual_sha256 = calculate_sha256(
        dataset_path
    )

    expected_sha256 = dataset.sha256

    integrity_verified = (
        actual_sha256.lower()
        == expected_sha256.lower()
    )

    integrity_status = (
        "VERIFIED"
        if integrity_verified
        else "TAMPERED"
    )

    # --------------------------------------------------------
    # Run dataset detectors
    # --------------------------------------------------------

    results = run_dataset_detectors(
        dataset_path
    )

    # --------------------------------------------------------
    # Add integrity evidence to detector results
    # --------------------------------------------------------

    results["integrity_status"] = integrity_status

    results["expected_sha256"] = expected_sha256

    results["actual_sha256"] = actual_sha256

    results["integrity_verified"] = integrity_verified

    # --------------------------------------------------------
    # Generate findings
    # --------------------------------------------------------

    findings = findings_from_detector_results(
        asset_type="dataset",
        asset_id=dataset_id,
        detector_results=results
    )

    # --------------------------------------------------------
    # Add dataset tampering finding
    # --------------------------------------------------------

    if not integrity_verified:

        findings.append(
            {
                "asset_type": "dataset",
                "asset_id": dataset_id,
                "severity": "HIGH",
                "reason": "Dataset SHA-256 hash does not match the registered hash",
                "evidence": (
                    f"Expected SHA-256: {expected_sha256}; "
                    f"Actual SHA-256: {actual_sha256}"
                ),
                "confidence": 1.0,
                "recommendation": "QUARANTINE"
            }
        )

    # --------------------------------------------------------
    # Save findings
    # --------------------------------------------------------

    saved_findings = save_findings(
        db=db,
        findings=findings
    )

    # --------------------------------------------------------
    # Generate assurance decision
    # --------------------------------------------------------

    decision = generate_assurance_decision(
        detector_results=results,
        findings=findings
    )

    # --------------------------------------------------------
    # Create assurance ID
    # --------------------------------------------------------

    assurance_id = (
        f"ASSURE-{uuid.uuid4().hex[:8].upper()}"
    )

    # --------------------------------------------------------
    # Save assurance assessment
    # --------------------------------------------------------

    create_assurance_assessment(
        db=db,
        assurance_id=assurance_id,
        overall_status=decision["overall_status"],
        risk_score=decision["risk_score"]
    )

    # --------------------------------------------------------
    # Record audit event
    # --------------------------------------------------------

    record_audit_event(
        db=db,
        event_type="DATASET_ASSURANCE_COMPLETED",
        asset_type="dataset",
        asset_id=dataset_id
    )

    # --------------------------------------------------------
    # Return complete assurance result
    # --------------------------------------------------------

    return {
        "status": "dataset_assurance_completed",

        "assurance_id": assurance_id,

        "dataset": {
            "dataset_id": dataset_id,
            "filename": dataset.filename,

            "registered_sha256": expected_sha256,

            "current_sha256": actual_sha256,

            "integrity_status": integrity_status,

            "integrity_verified": integrity_verified
        },

        "detector_results": results,

        "findings": [
            {
                "finding_id": finding.id,
                "asset_type": finding.asset_type,
                "asset_id": finding.asset_id,
                "severity": finding.severity,
                "reason": finding.reason,
                "evidence": finding.evidence,
                "confidence": finding.confidence,
                "recommendation": finding.recommendation
            }
            for finding in saved_findings
        ],

        "assurance_decision": decision,

        "database_saved": True,

        "audit_event_recorded": True
    }