from app.services.inference_integrity import (
    calculate_inference_hash,
    verify_inference_integrity
)


inference_record = {
    "image": "car.jpg",
    "prediction": "car",
    "confidence": 0.97
}


# Create the trusted hash
trusted_hash = calculate_inference_hash(
    inference_record
)

print("Trusted SHA-256:")
print(trusted_hash)


# Test 1: Correct inference record
verified_result = verify_inference_integrity(
    inference_record,
    trusted_hash
)

print("\nCorrect Record Test:")
print(verified_result)


# Test 2: Modified inference record
modified_record = {
    "image": "car.jpg",
    "prediction": "bike",
    "confidence": 0.97
}

tampered_result = verify_inference_integrity(
    modified_record,
    trusted_hash
)

print("\nModified Record Test:")
print(tampered_result)