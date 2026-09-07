from pathlib import Path
from PIL import Image
import statistics

SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".webp", ".avif"
}


def calculate_image_statistics(image_path: Path) -> dict:
    with Image.open(image_path) as image:
        image = image.convert("RGB")

        width, height = image.size
        pixels = list(image.getdata())

        red_values = [pixel[0] for pixel in pixels]
        green_values = [pixel[1] for pixel in pixels]
        blue_values = [pixel[2] for pixel in pixels]

        return {
            "width": width,
            "height": height,
            "red_mean": statistics.mean(red_values),
            "green_mean": statistics.mean(green_values),
            "blue_mean": statistics.mean(blue_values)
        }


def detect_trigger_indicators(
    dataset_directory: Path,
    color_threshold: float = 220.0
) -> dict:

    images = [
        path for path in dataset_directory.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    suspicious_images = []
    invalid_images = []

    for image_path in images:
        try:
            stats = calculate_image_statistics(image_path)

            # Detect images dominated by an extreme color.
            red_dominant = (
                stats["red_mean"] > color_threshold
                and stats["red_mean"] > stats["green_mean"] + 30
                and stats["red_mean"] > stats["blue_mean"] + 30
            )

            blue_dominant = (
                stats["blue_mean"] > color_threshold
                and stats["blue_mean"] > stats["red_mean"] + 30
                and stats["blue_mean"] > stats["green_mean"] + 30
            )

            green_dominant = (
                stats["green_mean"] > color_threshold
                and stats["green_mean"] > stats["red_mean"] + 30
                and stats["green_mean"] > stats["blue_mean"] + 30
            )

            if red_dominant or blue_dominant or green_dominant:

                if red_dominant:
                    trigger_type = "extreme_red_pattern"
                elif blue_dominant:
                    trigger_type = "extreme_blue_pattern"
                else:
                    trigger_type = "extreme_green_pattern"

                suspicious_images.append({
                    "filename": image_path.name,
                    "trigger_indicator": trigger_type,
                    "reason": "Image contains an unusually dominant extreme color pattern"
                })

        except Exception as error:
            invalid_images.append({
                "filename": image_path.name,
                "error": str(error)
            })

    return {
        "total_images": len(images),
        "suspicious_count": len(suspicious_images),
        "suspicious_images": suspicious_images,
        "invalid_images": invalid_images
    }