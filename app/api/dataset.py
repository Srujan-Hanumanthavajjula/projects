from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid

from app.services.hashing import calculate_sha256


router = APIRouter(
    prefix="/dataset",
    tags=["Dataset Integrity"]
)


UPLOAD_DIR = Path("uploads/datasets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )

    dataset_id = f"DS-{uuid.uuid4().hex[:8].upper()}"

    file_path = UPLOAD_DIR / f"{dataset_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    sha256_hash = calculate_sha256(file_path)

    file_size = file_path.stat().st_size

    return {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "size_bytes": file_size,
        "sha256": sha256_hash,
        "status": "uploaded"
    }


@router.post("/verify")
async def verify_dataset(
    file: UploadFile = File(...),
    expected_sha256: str = ""
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )

    if not expected_sha256:
        raise HTTPException(
            status_code=400,
            detail="Expected SHA-256 hash is required"
        )

    verification_id = f"VER-{uuid.uuid4().hex[:8].upper()}"

    temp_path = UPLOAD_DIR / f"verify_{verification_id}_{file.filename}"

    with open(temp_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    actual_sha256 = calculate_sha256(temp_path)

    # Remove temporary verification file
    temp_path.unlink(missing_ok=True)

    is_valid = actual_sha256.lower() == expected_sha256.strip().lower()

    return {
        "verification_id": verification_id,
        "filename": file.filename,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "integrity_verified": is_valid,
        "status": "VERIFIED" if is_valid else "TAMPERED"
    }