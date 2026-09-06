import hashlib
import json


def calculate_inference_hash(inference_record: dict) -> str:
    """
    Calculate a SHA-256 hash for an inference record.
    """

    canonical_record = json.dumps(
        inference_record,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        canonical_record.encode("utf-8")
    ).hexdigest()


def verify_inference_integrity(
    inference_record: dict,
    expected_sha256: str
) -> dict:
    """
    Verify whether an inference record matches
    its trusted SHA-256 hash.
    """

    actual_sha256 = calculate_inference_hash(
        inference_record
    )

    is_valid = (
        actual_sha256.lower()
        == expected_sha256.strip().lower()
    )

    return {
        "expected_sha256": expected_sha256,
        "actual_sha256": actual_sha256,
        "integrity_verified": is_valid,
        "status": "VERIFIED" if is_valid else "TAMPERED"
    }