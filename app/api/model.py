from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pathlib import Path
import uuid

from sqlalchemy.orm import Session

from app.detectors.model_integrity_detector import (
    calculate_model_hash,
    verify_model_integrity
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

    model_path = MODEL_DIR / f"{model_id}_{file.filename}"

    # Save uploaded model
    with open(model_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    # Calculate SHA-256
    model_hash = calculate_model_hash(model_path)

    # Save model evidence to PostgreSQL
    create_model(
        db=db,
        model_id=model_id,
        filename=file.filename,
        sha256=model_hash,
        integrity_status="VERIFIED"
    )

    return {
        "model_id": model_id,
        "filename": file.filename,
        "sha256": model_hash,
        "status": "uploaded",
        "database_saved": True
    }


# ============================================================
# MODEL VERIFICATION
# ============================================================

@router.post("/verify")
async def verify_model(
    file: UploadFile = File(...),
    expected_sha256: str = ""
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No model filename provided"
        )

    if not expected_sha256:
        raise HTTPException(
            status_code=400,
            detail="Expected SHA-256 hash is required"
        )

    verification_id = f"MODEL-VER-{uuid.uuid4().hex[:8].upper()}"

    temp_path = MODEL_DIR / f"verify_{verification_id}_{file.filename}"

    try:
        # Save temporary model
        with open(temp_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        # Verify model integrity
        result = verify_model_integrity(
            temp_path,
            expected_sha256
        )

        return {
            "verification_id": verification_id,
            "status": result["status"],
            "integrity_verified": result["integrity_verified"],
            "expected_sha256": result["expected_sha256"],
            "actual_sha256": result["actual_sha256"],
            "filename": result["model_filename"]
        }

    finally:
        # Remove temporary verification file
        temp_path.unlink(missing_ok=True)