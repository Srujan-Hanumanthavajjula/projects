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
def calculate_inference_binding_hash(
    input_hash: str,
    model_hash: str,
    output_hash: str
) -> str:
    """
    Creates a cryptographic binding between the input,
    model and inference output.
    """

    import hashlib
    import json

    binding_record = {
        "input_hash": input_hash,
        "model_hash": model_hash,
        "output_hash": output_hash
    }

    canonical_record = json.dumps(
        binding_record,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        canonical_record.encode("utf-8")
    ).hexdigest()
def verify_inference_binding(
    input_hash: str,
    model_hash: str,
    output_hash: str,
    expected_binding_hash: str
) -> dict:

    actual_binding_hash = calculate_inference_binding_hash(
        input_hash,
        model_hash,
        output_hash
    )

    is_valid = (
        actual_binding_hash.lower()
        == expected_binding_hash.strip().lower()
    )

    return {
        "expected_binding_hash": expected_binding_hash,
        "actual_binding_hash": actual_binding_hash,
        "binding_verified": is_valid,
        "status": "VERIFIED" if is_valid else "TAMPERED"
    }