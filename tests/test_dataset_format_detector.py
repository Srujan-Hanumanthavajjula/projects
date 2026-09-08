from pathlib import Path

from app.detectors.dataset_format_detector import (
    detect_dataset_format
)


def test_detect_coco_format(tmp_path: Path):

    coco_file = tmp_path / "annotations.json"

    coco_file.write_text(
        """
        {
            "images": [],
            "annotations": [],
            "categories": []
        }
        """,
        encoding="utf-8"
    )

    result = detect_dataset_format(tmp_path)

    assert result["format"] == "COCO"
    assert result["confidence"] == 1.0


def test_detect_yolo_format(tmp_path: Path):

    yolo_file = tmp_path / "image1.txt"

    yolo_file.write_text(
    "0 0.5 0.5 0.4 0.4\n",
    encoding="utf-8"
)

    result = detect_dataset_format(tmp_path)

    assert result["format"] == "YOLO"
    assert result["confidence"] == 1.0


def test_detect_csv_labels_format(tmp_path: Path):

    labels_file = tmp_path / "labels.csv"

    labels_file.write_text(
        "filename,label\\nimage1.jpg,cat\\n",
        encoding="utf-8"
    )

    result = detect_dataset_format(tmp_path)

    assert result["format"] == "CSV_LABELS"
    assert result["confidence"] == 1.0


def test_detect_unknown_format(tmp_path: Path):

    unknown_file = tmp_path / "readme.md"

    unknown_file.write_text(
        "# Dataset",
        encoding="utf-8"
    )

    result = detect_dataset_format(tmp_path)

    assert result["format"] == "UNKNOWN"
    assert result["confidence"] == 0.0