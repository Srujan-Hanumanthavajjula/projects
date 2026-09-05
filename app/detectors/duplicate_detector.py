from pathlib import Path
import hashlib

from PIL import Image
import imagehash


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
    ".avif"
}


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of an image file.
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            sha256.update(chunk)

    return sha256.hexdigest()


def calculate_perceptual_hash(file_path: Path):
    """
    Calculate perceptual hash of an image.
    """
    with Image.open(file_path) as image:
        return imagehash.phash(image)


def analyze_duplicates(dataset_directory: Path):
    """
    Detect exact and visually similar duplicate images.
    """

    images = [
        path
        for path in dataset_directory.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    exact_hashes = {}
    perceptual_hashes = {}

    exact_duplicates = []
    near_duplicates = []
    invalid_images = []

    # Analyze every image
    for image_path in images:

        try:
            file_hash = calculate_file_hash(image_path)
            perceptual_hash = calculate_perceptual_hash(image_path)

            # Exact duplicate detection
            if file_hash in exact_hashes:
                exact_duplicates.append({
                    "original": str(exact_hashes[file_hash].name),
                    "duplicate": str(image_path.name),
                    "sha256": file_hash
                })
            else:
                exact_hashes[file_hash] = image_path

            # Store perceptual hash
            perceptual_hashes[image_path] = perceptual_hash

        except Exception as error:
            invalid_images.append({
                "filename": image_path.name,
                "error": str(error)
            })

    # Near-duplicate detection
    image_paths = list(perceptual_hashes.keys())

    for i in range(len(image_paths)):
        for j in range(i + 1, len(image_paths)):

            image_a = image_paths[i]
            image_b = image_paths[j]

            hash_a = perceptual_hashes[image_a]
            hash_b = perceptual_hashes[image_b]

            distance = hash_a - hash_b

            # Lower distance = more visually similar
            if 0 < distance <= 10:
                near_duplicates.append({
                    "image_1": image_a.name,
                    "image_2": image_b.name,
                    "hash_distance": int(distance)
                })

    return {
        "total_images": len(images),
        "exact_duplicate_count": len(exact_duplicates),
        "near_duplicate_count": len(near_duplicates),
        "invalid_image_count": len(invalid_images),
        "exact_duplicates": exact_duplicates,
        "near_duplicates": near_duplicates,
        "invalid_images": invalid_images
    }