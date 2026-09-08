from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.services.audit_service import record_audit_event

from app.services.inference_integrity import (
    calculate_inference_hash,
    verify_inference_integrity,
    calculate_inference_binding_hash,
    verify_inference_binding
)

from app.database.connection import get_db

from app.database.crud import (
    create_inference,
    create_finding
)


router = APIRouter(
    prefix="/inference",
    tags=["Inference Integrity"]
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class InferenceRequest(BaseModel):
    image: str
    prediction: str
    confidence: float
    model_hash: str


# ============================================================
# CREATE INFERENCE RECORD
# ============================================================

@router.post("/create")
def create_inference_record(
    request: InferenceRequest,
    db: Session = Depends(get_db)
):

    inference_id = f"INF-{uuid.uuid4().hex[:8].upper()}"

    inference_record = {
        "image": request.image,
        "prediction": request.prediction,
        "confidence": request.confidence
    }

    # --------------------------------------------------------
    # Calculate input hash
    # --------------------------------------------------------

    input_hash = calculate_inference_hash({
        "image": request.image
    })

    # --------------------------------------------------------
    # Calculate output hash
    # --------------------------------------------------------

    output_hash = calculate_inference_hash(
        inference_record
    )

    # --------------------------------------------------------
    # Bind input + model + output together
    # --------------------------------------------------------

    binding_hash = calculate_inference_binding_hash(
        input_hash=input_hash,
        model_hash=request.model_hash,
        output_hash=output_hash
    )

    # --------------------------------------------------------
    # Save inference evidence to PostgreSQL
    # --------------------------------------------------------

    create_inference(
        db=db,
        inference_id=inference_id,
        input_hash=input_hash,
        model_hash=request.model_hash,
        output_hash=output_hash,
        integrity_status="VERIFIED",
        replay_detected=False
    )

    # --------------------------------------------------------
    # Record audit event
    # --------------------------------------------------------

    record_audit_event(
        db=db,
        event_type="INFERENCE_CREATED",
        asset_type="inference",
        asset_id=inference_id
    )

    return {
        "inference_id": inference_id,
        "image": request.image,
        "prediction": request.prediction,
        "confidence": request.confidence,
        "model_hash": request.model_hash,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "binding_hash": binding_hash,
        "integrity_status": "VERIFIED",
        "database_saved": True,
        "audit_event_recorded": True
    }


# ============================================================
# VERIFY INFERENCE INTEGRITY
# ============================================================

@router.post("/verify")
def verify_inference(
    request: InferenceRequest,
    expected_sha256: str,
    db: Session = Depends(get_db)
):

    inference_record = {
        "image": request.image,
        "prediction": request.prediction,
        "confidence": request.confidence
    }

    # --------------------------------------------------------
    # Verify inference hash
    # --------------------------------------------------------

    result = verify_inference_integrity(
        inference_record,
        expected_sha256
    )

    # --------------------------------------------------------
    # Generate verification ID
    # --------------------------------------------------------

    inference_id = f"VERIFY-{uuid.uuid4().hex[:8].upper()}"

    finding_saved = False
    audit_recorded = False

    # --------------------------------------------------------
    # Handle tampering
    # --------------------------------------------------------

    if not result["integrity_verified"]:

        create_finding(
            db=db,
            asset_type="inference",
            asset_id=inference_id,
            severity="HIGH",
            reason="Inference output integrity verification failed",
            evidence=(
                f"Expected SHA-256: {result['expected_sha256']}; "
                f"Actual SHA-256: {result['actual_sha256']}"
            ),
            confidence=1.0,
            recommendation="QUARANTINE"
        )

        finding_saved = True

        # ----------------------------------------------------
        # Record tampering event in audit chain
        # ----------------------------------------------------

        record_audit_event(
            db=db,
            event_type="INFERENCE_TAMPER_DETECTED",
            asset_type="inference",
            asset_id=inference_id
        )

        audit_recorded = True

    return {
        "inference_id": inference_id,
        "expected_sha256": result["expected_sha256"],
        "actual_sha256": result["actual_sha256"],
        "integrity_verified": result["integrity_verified"],
        "status": result["status"],
        "finding_saved": finding_saved,
        "audit_event_recorded": audit_recorded
    }


# ============================================================
# VERIFY INPUT + MODEL + OUTPUT BINDING
# ============================================================

@router.post("/verify-binding")
def verify_binding(
    input_hash: str,
    model_hash: str,
    output_hash: str,
    expected_binding_hash: str,
    db: Session = Depends(get_db)
):

    result = verify_inference_binding(
        input_hash=input_hash,
        model_hash=model_hash,
        output_hash=output_hash,
        expected_binding_hash=expected_binding_hash
    )

    binding_id = f"BIND-{uuid.uuid4().hex[:8].upper()}"

    finding_saved = False
    audit_recorded = False

    # --------------------------------------------------------
    # Handle binding tampering
    # --------------------------------------------------------

    if not result["binding_verified"]:

        create_finding(
            db=db,
            asset_type="inference",
            asset_id=binding_id,
            severity="HIGH",
            reason="Inference input-model-output binding verification failed",
            evidence=(
                f"Expected binding hash: "
                f"{result['expected_binding_hash']}; "
                f"Actual binding hash: "
                f"{result['actual_binding_hash']}"
            ),
            confidence=1.0,
            recommendation="QUARANTINE"
        )

        finding_saved = True

        # ----------------------------------------------------
        # Record audit event
        # ----------------------------------------------------

        record_audit_event(
            db=db,
            event_type="INFERENCE_BINDING_TAMPER_DETECTED",
            asset_type="inference",
            asset_id=binding_id
        )

        audit_recorded = True

    return {
        "binding_id": binding_id,
        "expected_binding_hash": result["expected_binding_hash"],
        "actual_binding_hash": result["actual_binding_hash"],
        "binding_verified": result["binding_verified"],
        "status": result["status"],
        "finding_saved": finding_saved,
        "audit_event_recorded": audit_recorded
    }