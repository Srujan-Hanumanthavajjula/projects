from pathlib import Path
import zipfile

from PIL import Image

from app.services.dataset_assurance import run_dataset_detectors
from app.services.finding_service import findings_from_detector_results


def test_run_dataset_detectors_with_zip(tmp_path: Path):
    # Create temporary dataset directory
    source_dir = tmp_path / "source"
    source_dir.mkdir()

    # Create two identical images
    image1 = source_dir / "cat.jpg"
    image2 = source_dir / "cat_copy.jpg"

    image = Image.new("RGB", (100, 100), (120, 120, 120))
    image.save(image1)
    image.save(image2)

    # Create labels.csv
    labels_file = source_dir / "labels.csv"

    labels_file.write_text(
        "filename,label\n"
        "cat.jpg,cat\n"
        "cat_copy.jpg,cat\n",
        encoding="utf-8"
    )

    # Create ZIP dataset
    dataset_zip = tmp_path / "dataset.zip"

    with zipfile.ZipFile(dataset_zip, "w") as archive:
        archive.write(image1, arcname="cat.jpg")
        archive.write(image2, arcname="cat_copy.jpg")
        archive.write(labels_file, arcname="labels.csv")

    # Run unified detector service
    results = run_dataset_detectors(dataset_zip)

    # Verify detector outputs exist
    assert "exact_duplicate_count" in results
    assert "near_duplicate_count" in results
    assert "ood_count" in results
    assert "suspicious_count" in results
    assert "anomaly_count" in results

    # Two identical images should be detected
    assert results["exact_duplicate_count"] >= 1

    # Labels should be detected
    assert results["total_label_entries"] == 2

    print("\nUnified dataset assurance results:")
    print(results)
from app.services.finding_service import findings_from_detector_results


def test_detector_anomalies_create_findings():

    detector_results = {
        "missing_images": [
            {
                "filename": "missing.jpg",
                "label": "cat"
            }
        ],
        "duplicate_label_entries": [
            "image1.jpg"
        ],
        "suspicious_labels": [],
        "ood_images": [],
        "suspicious_images": [],
        "exact_duplicates": [],
        "near_duplicates": []
    }

    findings = findings_from_detector_results(
        asset_type="dataset",
        asset_id="DS-TEST",
        detector_results=detector_results
    )

    assert len(findings) == 2

    # Missing image finding
    assert any(
        finding["reason"]
        == "Label references an image that does not exist"
        for finding in findings
    )

    # Duplicate label finding
    assert any(
        finding["reason"]
        == "Duplicate label entry detected"
        for finding in findings
    )
def test_yolo_anomalies_create_findings():

    detector_results = {
        "yolo_annotation_validation": {
            "total_annotation_files": 1,
            "valid_annotation_count": 0,
            "invalid_annotation_count": 1,
            "invalid_annotations": [
                {
                    "filename": "image1.txt",
                    "line": 1,
                    "content": "0 1.5 0.5 0.4 0.4",
                    "reason": "x_center must be between 0 and 1"
                }
            ],
            "annotations_valid": False
        }
    }

    findings = findings_from_detector_results(
        asset_type="dataset",
        asset_id="DS-YOLO-TEST",
        detector_results=detector_results
    )

    assert len(findings) == 1

    assert findings[0]["severity"] == "HIGH"

    assert (
        findings[0]["reason"]
        == "x_center must be between 0 and 1"
    )

    assert findings[0]["recommendation"] == "REVIEW"
from app.services.assurance_orchestrator import (
    generate_assurance_decision
)


def test_invalid_yolo_annotation_increases_assurance_risk():

    detector_results = {
        "integrity_status": "VERIFIED",

        "total_images": 10,

        "exact_duplicate_count": 0,
        "near_duplicate_count": 0,

        "ood_count": 0,
        "suspicious_count": 0,

        "yolo_annotation_validation": {
            "total_annotation_files": 5,
            "valid_annotation_count": 4,
            "invalid_annotation_count": 1,
            "invalid_annotations": [
                {
                    "filename": "image5.txt",
                    "line": 1,
                    "content": "0 1.5 0.5 0.4 0.4",
                    "reason": "x_center must be between 0 and 1"
                }
            ],
            "annotations_valid": False
        },

        "behavior_anomalies": [],

        "inference_status": "VERIFIED",
        "replay_detected": False
    }

    decision = generate_assurance_decision(
        detector_results=detector_results,
        findings=[]
    )

    assert decision["component_risks"]["integrity_risk"] == 20

    assert decision["risk_score"] > 0

    assert decision["overall_status"] == "ACCEPT"
def test_many_invalid_yolo_annotations_trigger_quarantine():

    detector_results = {
        "integrity_status": "VERIFIED",

        "total_images": 10,

        "exact_duplicate_count": 0,
        "near_duplicate_count": 0,

        "ood_count": 0,
        "suspicious_count": 0,

        "yolo_annotation_validation": {
            "total_annotation_files": 10,
            "valid_annotation_count": 0,
            "invalid_annotation_count": 10,
            "invalid_annotations": [
                {
                    "filename": f"image{i}.txt",
                    "line": 1,
                    "content": "0 1.5 0.5 0.4 0.4",
                    "reason": "x_center must be between 0 and 1"
                }
                for i in range(10)
            ],
            "annotations_valid": False
        },

        "behavior_anomalies": [],

        "inference_status": "VERIFIED",
        "replay_detected": False
    }

    decision = generate_assurance_decision(
        detector_results=detector_results,
        findings=[]
    )

    assert decision["component_risks"]["integrity_risk"] == 100

    assert decision["risk_score"] == 25

    assert decision["overall_status"] == "QUARANTINE"