from pathlib import Path

from app.detectors.ood_detector import detect_ood_images


def test_ood_detector():

    dataset_directory = Path("tests/test_ood_data")

    result = detect_ood_images(
        dataset_directory
    )

    assert "total_images" in result
    assert "ood_count" in result
    assert "ood_images" in result
    assert "invalid_images" in result