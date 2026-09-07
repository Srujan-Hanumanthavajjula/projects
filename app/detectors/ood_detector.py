from pathlib import Path
from PIL import Image
import statistics


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".avif"
}


def calculate_image_features(image_path: Path) -> dict:
    """
    Calculate basic statistical features for an image.
    """

    with Image.open(image_path) as image:

        image = image.convert("RGB")

        width, height = image.size

        pixels = list(image.getdata())

        brightness_values = [
            (r + g + b) / 3
            for r, g, b in pixels
        ]

        brightness_mean = statistics.mean(
            brightness_values
        )

        brightness_std = (
            statistics.pstdev(brightness_values)
            if len(brightness_values) > 1
            else 0
        )

        return {
            "width": width,
            "height": height,
            "brightness_mean": round(
                brightness_mean,
                2
            ),
            "brightness_std": round(
                brightness_std,
                2
            )
        }


def detect_ood_images(
    dataset_directory: Path,
    brightness_threshold: float = 60.0
) -> dict:
    """
    Detect potentially out-of-distribution images
    using basic image statistics.

    This is a baseline detector and does not require
    model retraining.
    """

    images = [
        path
        for path in dataset_directory.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower()
            in SUPPORTED_EXTENSIONS
        )
    ]

    features = []
    invalid_images = []

    for image_path in images:

        try:

            image_features = calculate_image_features(
                image_path
            )

            image_features["filename"] = image_path.name

            features.append(image_features)

        except Exception as error:

            invalid_images.append({
                "filename": image_path.name,
                "error": str(error)
            })

    if not features:

        return {
            "total_images": 0,
            "ood_count": 0,
            "ood_images": [],
            "invalid_images": invalid_images
        }

    brightness_values = [
        item["brightness_mean"]
        for item in features
    ]

    dataset_brightness_mean = statistics.mean(
        brightness_values
    )

    ood_images = []

    for item in features:

        brightness_difference = abs(
            item["brightness_mean"]
            - dataset_brightness_mean
        )

        if brightness_difference > brightness_threshold:

            ood_images.append({
                "filename": item["filename"],
                "brightness_mean": item[
                    "brightness_mean"
                ],
                "dataset_brightness_mean": round(
                    dataset_brightness_mean,
                    2
                ),
                "brightness_difference": round(
                    brightness_difference,
                    2
                ),
                "reason": (
                    "Image brightness differs "
                    "significantly from dataset distribution"
                )
            })

    return {
        "total_images": len(features),
        "ood_count": len(ood_images),
        "dataset_brightness_mean": round(
            dataset_brightness_mean,
            2
        ),
        "ood_images": ood_images,
        "invalid_images": invalid_images
    }