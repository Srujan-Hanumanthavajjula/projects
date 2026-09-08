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
    calculate_model_hash,
    verify_model_integrity
)

from app.services.model_assurance import (
    run_model_assurance
)

from app.database.connection import get_db
from app.database.crud import create_model


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

    model_id = f"MODEL-{uuid.uuid4().hex[:8].upper()}"

    model_path = (
        MODEL_DIR /
        f"{model_id}_{file.filename}"
    )

    # Save uploaded model
    with open(model_path, "wb") as buffer:

        while chunk := await file.read(
            1024 * 1024
        ):
            buffer.write(chunk)

    # Calculate SHA-256
    model_hash = calculate_model_hash(
        model_path
    )

    # Save model evidence to PostgreSQL
    create_model(
        db=db,
        model_id=model_id,
        filename=file.filename,
        sha256=model_hash,
        integrity_status="VERIFIED"
    )

    # Record model upload in tamper-evident audit trail
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

    # Find the registered model
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

        # Save temporary verification model
        with open(
            temp_path,
            "wb"
        ) as buffer:

            while chunk := await file.read(
                1024 * 1024
            ):
                buffer.write(chunk)

        # Calculate hash of newly submitted model
        actual_sha256 = calculate_model_hash(
            temp_path
        )

        # Retrieve trusted hash from PostgreSQL
        expected_sha256 = model.sha256

        # Compare hashes
        is_valid = (
            actual_sha256.lower()
            == expected_sha256.lower()
        )

        # Record verification in audit trail
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

        # Remove temporary verification model
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

    This endpoint does not modify the registered model.

    It checks:
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