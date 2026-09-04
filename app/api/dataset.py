from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import hashlib
import uuid

router = APIRouter(
    prefix="/dataset",
    tags=["Dataset Integrity"]
)

UPLOAD_DIR = Path("uploads/datasets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


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