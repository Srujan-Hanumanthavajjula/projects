from pathlib import Path
import tempfile
import zipfile

from app.detectors.duplicate_detector import analyze_duplicates
from app.detectors.ood_detector import detect_ood_images
from app.detectors.trigger_detector import detect_trigger_indicators
from app.detectors.label_anomaly_detector import detect_label_anomalies
from app.detectors.dataset_format_detector import detect_dataset_format
from app.detectors.yolo_annotation_detector import validate_yolo_annotations
from app.detectors.coco_annotation_detector import validate_coco_annotations


def _safe_extract_zip(
    zip_path: Path,
    extract_directory: Path
) -> None:
    """
    Safely extract a ZIP archive without allowing
    path traversal.
    """

    extract_directory = extract_directory.resolve()

    with zipfile.ZipFile(zip_path, "r") as archive:

        for member in archive.infolist():

            target_path = (
                extract_directory / member.filename
            ).resolve()

            if not str(target_path).startswith(
                str(extract_directory)
            ):
                raise ValueError(
                    f"Unsafe ZIP entry detected: {member.filename}"
                )

        archive.extractall(extract_directory)


def _find_labels_file(
    dataset_directory: Path
) -> Path | None:
    """
    Find labels.csv inside the extracted dataset.
    """

    matches = list(
        dataset_directory.rglob("labels.csv")
    )

    if not matches:
        return None

    return matches[0]


def run_dataset_detectors(
    dataset_path: Path
) -> dict:
    """
    Run all available dataset-level integrity detectors.

    Supports:
    - ZIP datasets
    - Image datasets
    - CSV labels
    - COCO datasets
    - YOLO datasets

    Detectors:
    1. Duplicate detection
    2. OOD detection
    3. Trigger indicator detection
    4. Dataset format detection
    5. Dataset annotation validation
    6. Label anomaly detection
    """

    with tempfile.TemporaryDirectory(
        prefix="cv_assurance_dataset_"
    ) as temporary_directory:

        extraction_directory = Path(
            temporary_directory
        )

        # --------------------------------------------------
        # Dataset extraction
        # --------------------------------------------------

        if dataset_path.suffix.lower() == ".zip":

            _safe_extract_zip(
                dataset_path,
                extraction_directory
            )

            dataset_directory = extraction_directory

        else:

            dataset_directory = dataset_path

        results = {}

        # --------------------------------------------------
        # 1. Duplicate detection
        # --------------------------------------------------

        duplicate_results = analyze_duplicates(
            dataset_directory
        )

        results.update(
            duplicate_results
        )

        # --------------------------------------------------
        # 2. OOD detection
        # --------------------------------------------------

        ood_results = detect_ood_images(
            dataset_directory
        )

        results.update(
            ood_results
        )

        # --------------------------------------------------
        # 3. Trigger indicator detection
        # --------------------------------------------------

        trigger_results = detect_trigger_indicators(
            dataset_directory
        )

        results.update(
            trigger_results
        )

        # --------------------------------------------------
        # 4. Dataset format detection
        # --------------------------------------------------

        dataset_format = detect_dataset_format(
            dataset_directory
        )

        results["dataset_format"] = dataset_format

        # --------------------------------------------------
        # 5. Dataset annotation validation
        # --------------------------------------------------

        if dataset_format["format"] == "YOLO":

            yolo_results = validate_yolo_annotations(
                dataset_directory
            )

            results[
                "yolo_annotation_validation"
            ] = yolo_results

        elif dataset_format["format"] == "COCO":

            coco_results = validate_coco_annotations(
                dataset_directory
            )

            results[
                "coco_annotation_validation"
            ] = coco_results

        # --------------------------------------------------
        # 6. Label anomaly detection
        # --------------------------------------------------

        labels_file = _find_labels_file(
            dataset_directory
        )

        if labels_file is not None:

            label_results = detect_label_anomalies(
                dataset_directory,
                labels_file
            )

            results.update(
                label_results
            )

        else:

            results.update({
                "total_label_entries": 0,
                "missing_images": [],
                "duplicate_label_entries": [],
                "suspicious_labels": [],
                "anomaly_count": 0
            })

        # --------------------------------------------------
        # Return all detector results
        # --------------------------------------------------

        return results