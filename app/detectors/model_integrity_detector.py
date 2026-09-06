from pathlib import Path
import hashlib


def calculate_model_hash(model_path: Path) -> str:
    """
    Calculate SHA-256 hash of a trained model file.
    """

    sha256 = hashlib.sha256()

    with open(model_path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def verify_model_integrity(
    model_path: Path,
    expected_sha256: str
) -> dict:
    """
    Verify whether a model file matches its trusted SHA-256 hash.
    """

    actual_sha256 = calculate_model_hash(model_path)

    is_valid = (
        actual_sha256.lower()
        == expected_sha256.strip().lower()
    )

    return {
        "model_filename": model_path.name,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "integrity_verified": is_valid,
        "status": "VERIFIED" if is_valid else "TAMPERED"
    }