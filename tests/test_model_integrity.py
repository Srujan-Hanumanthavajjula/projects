from pathlib import Path

from app.detectors.model_integrity_detector import (
    calculate_model_hash,
    verify_model_integrity
)


model_path = Path("test-model.txt")


# Calculate the trusted hash
trusted_hash = calculate_model_hash(model_path)

print("Trusted SHA-256:")
print(trusted_hash)


# Test 1: Correct hash
verified_result = verify_model_integrity(
    model_path,
    trusted_hash
)

print("\nCorrect Hash Test:")
print(verified_result)


# Test 2: Wrong hash
tampered_result = verify_model_integrity(
    model_path,
    "0000000000000000000000000000000000000000000000000000000000000000"
)

print("\nWrong Hash Test:")
print(tampered_result)