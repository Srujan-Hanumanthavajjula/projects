from pathlib import Path

from app.detectors.yolo_annotation_detector import (
    validate_yolo_annotations
)


def test_valid_yolo_annotation(tmp_path: Path):

    label_file = tmp_path / "image1.txt"

    label_file.write_text(
        "0 0.5 0.5 0.4 0.4\n",
        encoding="utf-8"
    )

    result = validate_yolo_annotations(tmp_path)

    assert result["total_annotation_files"] == 1
    assert result["valid_annotation_count"] == 1
    assert result["invalid_annotation_count"] == 0
    assert result["annotations_valid"] is True


def test_invalid_yolo_coordinates(tmp_path: Path):

    label_file = tmp_path / "image1.txt"

    label_file.write_text(
        "0 1.5 0.5 0.4 0.4\n",
        encoding="utf-8"
    )

    result = validate_yolo_annotations(tmp_path)

    assert result["invalid_annotation_count"] == 1
    assert result["annotations_valid"] is False


def test_invalid_yolo_structure(tmp_path: Path):

    label_file = tmp_path / "image1.txt"

    label_file.write_text(
        "0 0.5 0.5\n",
        encoding="utf-8"
    )

    result = validate_yolo_annotations(tmp_path)

    assert result["invalid_annotation_count"] == 1
    assert result["annotations_valid"] is False


def test_invalid_class_id(tmp_path: Path):

    label_file = tmp_path / "image1.txt"

    label_file.write_text(
        "-1 0.5 0.5 0.4 0.4\n",
        encoding="utf-8"
    )

    result = validate_yolo_annotations(tmp_path)

    assert result["invalid_annotation_count"] == 1
    assert result["annotations_valid"] is False


def test_class_id_out_of_range(tmp_path: Path):

    label_file = tmp_path / "image1.txt"

    label_file.write_text(
        "5 0.5 0.5 0.4 0.4\n",
        encoding="utf-8"
    )

    result = validate_yolo_annotations(
        tmp_path,
        num_classes=5
    )

    assert result["invalid_annotation_count"] == 1
    assert result["annotations_valid"] is False