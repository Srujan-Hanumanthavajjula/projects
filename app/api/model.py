from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends
)

from app.services.audit_service import record_audit_event

from app.database.models import Model

from pathlib import Path
import uuid

from sqlalchemy.orm import Session

from app.detectors.model_integrity_detector import (
    calculate_model_hash
)

from app.services.model_assurance import (
    run_model_assurance
)

from app.services.assurance_orchestrator import (
    generate_assurance_decision
)

from app.database.crud import (
    create_model,
    create_assurance_assessment,
    create_finding
)

from app.database.connection import get_db


router = APIRouter(
    prefix="/model",
    tags=["Model Integrity"]
)


MODEL_DIR = Path("uploads/models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# MODEL UPLOAD
# ============================================================

@router.post("/upload")
async def upload_model(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No model filename provided"
        )

    model_id = (
        f"MODEL-{uuid.uuid4().hex[:8].upper()}"
    )

    model_path = (
        MODEL_DIR /
        f"{model_id}_{file.filename}"
    )

    # --------------------------------------------------------
    # Save uploaded model
    # --------------------------------------------------------

    with open(
        model_path,
        "wb"
    ) as buffer:

        while chunk := await file.read(
            1024 * 1024
        ):
            buffer.write(chunk)

    # --------------------------------------------------------
    # Calculate SHA-256
    # --------------------------------------------------------

    model_hash = calculate_model_hash(
        model_path
    )

    # --------------------------------------------------------
    # Save model evidence to PostgreSQL
    # --------------------------------------------------------

    create_model(
        db=db,
        model_id=model_id,
        filename=file.filename,
        sha256=model_hash,
        integrity_status="VERIFIED"
    )

    # --------------------------------------------------------
    # Record model upload in audit trail
    # --------------------------------------------------------

    record_audit_event(
        db=db,
        event_type="MODEL_UPLOADED",
        asset_type="model",
        asset_id=model_id
    )

    return {
        "model_id": model_id,
        "filename": file.filename,
        "sha256": model_hash,
        "status": "uploaded",
        "database_saved": True,
        "audit_event_recorded": True
    }


# ============================================================
# MODEL VERIFICATION
# ============================================================

@router.post("/verify")
async def verify_model(
    model_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No model filename provided"
        )

    # --------------------------------------------------------
    # Find registered model
    # --------------------------------------------------------

    model = db.query(Model).filter(
        Model.model_id == model_id
    ).first()

    if not model:
        raise HTTPException(
            status_code=404,
            detail="Model ID not found"
        )

    verification_id = (
        f"MODEL-VER-{uuid.uuid4().hex[:8].upper()}"
    )

    temp_path = (
        MODEL_DIR /
        f"verify_{verification_id}_{file.filename}"
    )

    try:

        # ----------------------------------------------------
        # Save temporary verification model
        # ----------------------------------------------------

        with open(
            temp_path,
            "wb"
        ) as buffer:

            while chunk := await file.read(
                1024 * 1024
            ):
                buffer.write(chunk)

        # ----------------------------------------------------
        # Calculate submitted model hash
        # ----------------------------------------------------

        actual_sha256 = calculate_model_hash(
            temp_path
        )

        # ----------------------------------------------------
        # Retrieve trusted hash
        # ----------------------------------------------------

        expected_sha256 = model.sha256

        # ----------------------------------------------------
        # Compare hashes
        # ----------------------------------------------------

        is_valid = (
            actual_sha256.lower()
            == expected_sha256.lower()
        )

        # ----------------------------------------------------
        # Record verification
        # ----------------------------------------------------

        record_audit_event(
            db=db,
            event_type="MODEL_VERIFIED",
            asset_type="model",
            asset_id=model_id
        )

        return {
            "verification_id": verification_id,
            "model_id": model_id,
            "filename": file.filename,
            "registered_filename": model.filename,
            "expected_sha256": expected_sha256,
            "actual_sha256": actual_sha256,
            "integrity_verified": is_valid,
            "status": (
                "VERIFIED"
                if is_valid
                else "TAMPERED"
            ),
            "audit_event_recorded": True
        }

    finally:

        # ----------------------------------------------------
        # Remove temporary verification model
        # ----------------------------------------------------

        temp_path.unlink(
            missing_ok=True
        )


# ============================================================
# MODEL ASSURANCE
# ============================================================

@router.post("/assurance")
async def model_assurance(
    file: UploadFile = File(...)
):
    """
    Perform model-format detection and structural validation.

    Checks:
    - Model format
    - Structural validity
    - Model risk
    - Findings
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No model filename provided"
        )

    assurance_id = (
        f"MODEL-AS-{uuid.uuid4().hex[:8].upper()}"
    )

    temp_path = (
        MODEL_DIR /
        f"assurance_{assurance_id}_{file.filename}"
    )

    try:

        # ----------------------------------------------------
        # Save temporary model
        # ----------------------------------------------------

        with open(
            temp_path,
            "wb"
        ) as buffer:

            while chunk := await file.read(
                1024 * 1024
            ):
                buffer.write(chunk)

        # ----------------------------------------------------
        # Run model assurance
        # ----------------------------------------------------

        assurance_result = run_model_assurance(
            temp_path
        )

        # ----------------------------------------------------
        # Return assurance result
        # ----------------------------------------------------

        return {
            "assurance_id": assurance_id,
            "filename": file.filename,

            "model_format": assurance_result[
                "model_format"
            ],

            "format_confidence": assurance_result[
                "format_confidence"
            ],

            "format_valid": assurance_result[
                "format_valid"
            ],

            "format_reason": assurance_result[
                "format_reason"
            ],

            "model_risk": assurance_result[
                "model_risk"
            ],

            "findings": assurance_result[
                "findings"
            ],

            "status": (
                "QUARANTINE"
                if assurance_result["model_risk"] >= 100
                else "REVIEW"
                if assurance_result["model_risk"] > 0
                else "ACCEPT"
            )
        }

    finally:

        # ----------------------------------------------------
        # Remove temporary assurance model
        # ----------------------------------------------------

        temp_path.unlink(
            missing_ok=True
        )


# ============================================================
# FULL MODEL ASSURANCE
# ============================================================

@router.post("/full-assurance")
async def full_model_assurance(
    model_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Perform complete assurance of a submitted model.

    Checks:
    - Registered model existence
    - SHA-256 integrity
    - Model format
    - Structural validation
    - Model risk
    - Findings
    - PostgreSQL persistence
    - Audit trail
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No model filename provided"
        )

    # --------------------------------------------------------
    # Find registered model
    # --------------------------------------------------------

    model = db.query(Model).filter(
        Model.model_id == model_id
    ).first()

    if not model:
        raise HTTPException(
            status_code=404,
            detail="Model ID not found"
        )

    assurance_id = (
        f"MODEL-FULL-{uuid.uuid4().hex[:8].upper()}"
    )

    temp_path = (
        MODEL_DIR /
        f"full_assurance_{assurance_id}_{file.filename}"
    )

    try:

        # ----------------------------------------------------
        # Save submitted model
        # ----------------------------------------------------

        with open(
            temp_path,
            "wb"
        ) as buffer:

            while chunk := await file.read(
                1024 * 1024
            ):
                buffer.write(chunk)

        # ----------------------------------------------------
        # SHA-256 integrity verification
        # ----------------------------------------------------

        actual_sha256 = calculate_model_hash(
            temp_path
        )

        expected_sha256 = model.sha256

        integrity_verified = (
            actual_sha256.lower()
            == expected_sha256.lower()
        )

        integrity_status = (
            "VERIFIED"
            if integrity_verified
            else "TAMPERED"
        )

        # ----------------------------------------------------
        # Model format and structural assurance
        # ----------------------------------------------------

        model_assurance = run_model_assurance(
            temp_path
        )

        # ----------------------------------------------------
        # Combine detector results
        # ----------------------------------------------------

        detector_results = {

            "integrity_status": integrity_status,

            "model_integrity_status": integrity_status,

            "format": model_assurance.get(
                "model_format"
            ),

            "format_valid": model_assurance.get(
                "format_valid"
            ),

            "format_confidence": model_assurance.get(
                "format_confidence"
            ),

            "format_reason": model_assurance.get(
                "format_reason"
            ),

            "behavior_anomalies": [],

            "inference_status": "VERIFIED",

            "replay_detected": False
        }

        # ----------------------------------------------------
        # Generate findings
        # ----------------------------------------------------

        findings = []

        # ----------------------------------------------------
        # SHA-256 mismatch finding
        # ----------------------------------------------------

        if not integrity_verified:

            findings.append(
                {
                    "asset_type": "model",
                    "asset_id": model_id,
                    "severity": "HIGH",
                    "reason": (
                        "Submitted model SHA-256 does not "
                        "match the registered model hash"
                    ),
                    "evidence": (
                        f"Expected SHA-256: {expected_sha256}; "
                        f"Actual SHA-256: {actual_sha256}"
                    ),
                    "confidence": 1.0,
                    "recommendation": "QUARANTINE"
                }
            )

        # ----------------------------------------------------
        # Model format / validation findings
        # ----------------------------------------------------

        for item in model_assurance.get(
            "findings",
            []
        ):

            findings.append(
                {
                    "asset_type": "model",
                    "asset_id": model_id,
                    "severity": item.get(
                        "severity",
                        "MEDIUM"
                    ),
                    "reason": item.get(
                        "reason",
                        "Model assurance finding"
                    ),
                    "evidence": item.get(
                        "evidence"
                    ),
                    "confidence": item.get(
                        "confidence"
                    ),
                    "recommendation": item.get(
                        "recommendation"
                    )
                }
            )

        # ----------------------------------------------------
        # Central assurance decision
        # ----------------------------------------------------

        decision = generate_assurance_decision(
            detector_results=detector_results,
            findings=findings
        )

        # ----------------------------------------------------
        # Save findings to PostgreSQL
        # ----------------------------------------------------

        for finding in findings:

            create_finding(
                db=db,
                asset_type=finding["asset_type"],
                asset_id=finding["asset_id"],
                severity=finding["severity"],
                reason=finding["reason"],
                evidence=finding.get("evidence"),
                confidence=finding.get("confidence"),
                recommendation=finding.get(
                    "recommendation"
                )
            )

        # ----------------------------------------------------
        # Save assurance assessment to PostgreSQL
        # ----------------------------------------------------

        create_assurance_assessment(
            db=db,
            assurance_id=assurance_id,
            overall_status=decision["overall_status"],
            risk_score=decision["risk_score"]
        )

        # ----------------------------------------------------
        # Record audit event
        # ----------------------------------------------------

        record_audit_event(
            db=db,
            event_type="MODEL_FULL_ASSURANCE",
            asset_type="model",
            asset_id=model_id
        )

        # ----------------------------------------------------
        # Final response
        # ----------------------------------------------------

        return {

            "assurance_id": assurance_id,

            "model_id": model_id,

            "filename": file.filename,

            "registered_filename": model.filename,

            "expected_sha256": expected_sha256,

            "actual_sha256": actual_sha256,

            "integrity_verified": integrity_verified,

            "integrity_status": integrity_status,

            "model_format": model_assurance.get(
                "model_format"
            ),

            "format_confidence": model_assurance.get(
                "format_confidence"
            ),

            "format_valid": model_assurance.get(
                "format_valid"
            ),

            "format_reason": model_assurance.get(
                "format_reason"
            ),

            "model_risk": model_assurance.get(
                "model_risk"
            ),

            "risk_score": decision.get(
                "risk_score"
            ),

            "overall_status": decision.get(
                "overall_status"
            ),

            "recommendation": decision.get(
                "recommendation"
            ),

            "component_risks": decision.get(
                "component_risks"
            ),

            "findings": findings,

            "finding_count": len(findings),

            "database_findings_saved": True,

            "database_assessment_saved": True,

            "audit_event_recorded": True
        }

    finally:

        # ----------------------------------------------------
        # Remove temporary submitted model
        # ----------------------------------------------------

        temp_path.unlink(
            missing_ok=True
        )