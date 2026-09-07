from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from app.services.inference_integrity import (
    calculate_inference_hash,
    verify_inference_integrity
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

    # Calculate hash of inference data
    output_hash = calculate_inference_hash(
        inference_record
    )

    # Save inference evidence to PostgreSQL
    create_inference(
        db=db,
        inference_id=inference_id,
        input_hash=calculate_inference_hash({
            "image": request.image
        }),
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
        "output_hash": output_hash,
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