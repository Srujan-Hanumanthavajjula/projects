from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path
import uuid
import zipfile
import shutil

from app.detectors.ood_detector import detect_ood_images


router = APIRouter(
    prefix="/ood",
    tags=["OOD Detection"]
)


UPLOAD_DIR = Path("uploads/datasets")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/analyze")
async def analyze_ood(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a ZIP file containing images"
        )

    analysis_id = f"OOD-{uuid.uuid4().hex[:8].upper()}"

    zip_path = (
        UPLOAD_DIR /
        f"{analysis_id}_{file.filename}"
    )

    extract_dir = UPLOAD_DIR / analysis_id

    try:

        # Save ZIP
        with open(zip_path, "wb") as buffer:

            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        # Create extraction directory
        extract_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # Extract ZIP safely
        with zipfile.ZipFile(zip_path, "r") as zip_ref:

            for member in zip_ref.infolist():

                member_path = Path(member.filename)

                # Prevent ZIP path traversal
                if (
                    member_path.is_absolute()
                    or ".." in member_path.parts
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Unsafe ZIP file"
                    )

                target_path = extract_dir / member_path

                target_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

                if not member.is_dir():

                    with zip_ref.open(member) as source:

                        with open(target_path, "wb") as target:
                            shutil.copyfileobj(
                                source,
                                target
                            )

        # Run OOD detector
        result = detect_ood_images(
            extract_dir
        )

        return {
            "analysis_id": analysis_id,
            "status": "analysis_completed",
            "results": result
        }

    except zipfile.BadZipFile:

        raise HTTPException(
            status_code=400,
            detail="Invalid ZIP file"
        )

    finally:

        if zip_path.exists():
            zip_path.unlink()

        if extract_dir.exists():
            shutil.rmtree(extract_dir)