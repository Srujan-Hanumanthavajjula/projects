from pathlib import Path

from app.detectors.coco_annotation_detector import (
    validate_coco_annotations
)


def test_valid_coco_annotations(tmp_path: Path):

    coco_file = tmp_path / "annotations.json"

    coco_file.write_text(
        """
        {
            "images": [
                {
                    "id": 1,
                    "file_name": "image1.jpg"
                }
            ],
            "annotations": [
                {
                    "id": 1,
                    "image_id": 1,
                    "category_id": 1,
                    "bbox": [10, 20, 50, 40]
                }
            ],
            "categories": [
                {
                    "id": 1,
                    "name": "cat"
                }
            ]
        }
        """,
        encoding="utf-8"
    )

    result = validate_coco_annotations(tmp_path)

    assert result["coco_file_count"] == 1
    assert result["invalid_annotation_count"] == 0
    assert result["annotations_valid"] is True


def test_coco_invalid_image_reference(tmp_path: Path):

    coco_file = tmp_path / "annotations.json"

    coco_file.write_text(
        """
        {
            "images": [
                {
                    "id": 1,
                    "file_name": "image1.jpg"
                }
            ],
            "annotations": [
                {
                    "id": 1,
                    "image_id": 999,
                    "category_id": 1,
                    "bbox": [10, 20, 50, 40]
                }
            ],
            "categories": [
                {
                    "id": 1,
                    "name": "cat"
                }
            ]
        }
        """,
        encoding="utf-8"
    )

    result = validate_coco_annotations(tmp_path)

    assert result["invalid_annotation_count"] == 1
    assert result["annotations_valid"] is False


def test_coco_invalid_category_reference(tmp_path: Path):

    coco_file = tmp_path / "annotations.json"

    coco_file.write_text(
        """
        {
            "images": [
                {
                    "id": 1,
                    "file_name": "image1.jpg"
                }
            ],
            "annotations": [
                {
                    "id": 1,
                    "image_id": 1,
                    "category_id": 999,
                    "bbox": [10, 20, 50, 40]
                }
            ],
            "categories": [
                {
                    "id": 1,
                    "name": "cat"
                }
            ]
        }
        """,
        encoding="utf-8"
    )

    result = validate_coco_annotations(tmp_path)

    assert result["invalid_annotation_count"] == 1
    assert result["annotations_valid"] is False


def test_coco_invalid_bbox(tmp_path: Path):

    coco_file = tmp_path / "annotations.json"

    coco_file.write_text(
        """
        {
            "images": [
                {
                    "id": 1,
                    "file_name": "image1.jpg"
                }
            ],
            "annotations": [
                {
                    "id": 1,
                    "image_id": 1,
                    "category_id": 1,
                    "bbox": [10, 20, -50, 40]
                }
            ],
            "categories": [
                {
                    "id": 1,
                    "name": "cat"
                }
            ]
        }
        """,
        encoding="utf-8"
    )

    result = validate_coco_annotations(tmp_path)

    assert result["invalid_annotation_count"] == 1
    assert result["annotations_valid"] is False


def test_non_coco_json_is_ignored(tmp_path: Path):

    json_file = tmp_path / "config.json"

    json_file.write_text(
        """
        {
            "name": "test",
            "version": 1
        }
        """,
        encoding="utf-8"
    )

    result = validate_coco_annotations(tmp_path)

    assert result["coco_file_count"] == 0
    assert result["invalid_annotation_count"] == 0