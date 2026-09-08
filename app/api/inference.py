from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.services.audit_service import record_audit_event
import uuid

from app.services.inference_integrity import (
    calculate_inference_hash,
    verify_inference_integrity,
    calculate_inference_binding_hash,
    verify_inference_binding
)

from app.database.connection import get_db
from app.database.crud import create_inference


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

    # Calculate input hash
    input_hash = calculate_inference_hash({
        "image": request.image
    })

    # Calculate output hash
    output_hash = calculate_inference_hash(
        inference_record
    )

    # Bind input + model + output together
    binding_hash = calculate_inference_binding_hash(
        input_hash=input_hash,
        model_hash=request.model_hash,
        output_hash=output_hash
    )

    # Save inference evidence to PostgreSQL
    create_inference(
        db=db,
        inference_id=inference_id,
        input_hash=input_hash,
        model_hash=request.model_hash,
        output_hash=output_hash,
        integrity_status="VERIFIED",
        replay_detected=False
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
        "database_saved": True
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

    result = verify_inference_integrity(
        inference_record,
        expected_sha256
    )

    return {
        "expected_sha256": result["expected_sha256"],
        "actual_sha256": result["actual_sha256"],
        "integrity_verified": result["integrity_verified"],
        "status": result["status"]
    }


# ============================================================
# VERIFY INPUT + MODEL + OUTPUT BINDING
# ============================================================

@router.post("/verify-binding")
def verify_binding(
    input_hash: str,
    model_hash: str,
    output_hash: str,
    expected_binding_hash: str
):

    result = verify_inference_binding(
        input_hash=input_hash,
        model_hash=model_hash,
        output_hash=output_hash,
        expected_binding_hash=expected_binding_hash
    )

    return {
        "expected_binding_hash": result["expected_binding_hash"],
        "actual_binding_hash": result["actual_binding_hash"],
        "binding_verified": result["binding_verified"],
        "status": result["status"]
    }