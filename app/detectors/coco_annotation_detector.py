from pathlib import Path
import json


def validate_coco_annotations(
    dataset_directory: Path
) -> dict:
    """
    Validate basic COCO annotation structure.

    Checks:
    - Required top-level fields
    - Image IDs
    - Annotation image_id references
    - Annotation category_id references
    - Bounding-box structure
    - Bounding-box values
    """

    json_files = list(
        dataset_directory.rglob("*.json")
    )

    coco_files = []
    invalid_annotations = []

    for json_file in json_files:

        try:
            with open(
                json_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

        except Exception as error:

            invalid_annotations.append({
                "filename": json_file.name,
                "reason": f"Invalid JSON file: {error}"
            })

            continue

        # Check whether this is a COCO file
        required_fields = {
            "images",
            "annotations",
            "categories"
        }

        if not required_fields.issubset(data.keys()):
            continue

        coco_files.append(json_file.name)

        images = data["images"]
        annotations = data["annotations"]
        categories = data["categories"]

        # --------------------------------------------------
        # Validate top-level structures
        # --------------------------------------------------

        if not isinstance(images, list):

            invalid_annotations.append({
                "filename": json_file.name,
                "reason": "'images' must be a list"
            })

            continue

        if not isinstance(annotations, list):

            invalid_annotations.append({
                "filename": json_file.name,
                "reason": "'annotations' must be a list"
            })

            continue

        if not isinstance(categories, list):

            invalid_annotations.append({
                "filename": json_file.name,
                "reason": "'categories' must be a list"
            })

            continue

        # --------------------------------------------------
        # Build valid IDs
        # --------------------------------------------------

        image_ids = set()
        category_ids = set()

        for image in images:

            if "id" not in image:

                invalid_annotations.append({
                    "filename": json_file.name,
                    "reason": "Image is missing required 'id'"
                })

                continue

            image_ids.add(image["id"])

        for category in categories:

            if "id" not in category:

                invalid_annotations.append({
                    "filename": json_file.name,
                    "reason": "Category is missing required 'id'"
                })

                continue

            category_ids.add(category["id"])

        # --------------------------------------------------
        # Validate annotations
        # --------------------------------------------------

        for index, annotation in enumerate(
            annotations
        ):

            if "id" not in annotation:

                invalid_annotations.append({
                    "filename": json_file.name,
                    "annotation_index": index,
                    "reason": "Annotation is missing required 'id'"
                })

                continue

            if "image_id" not in annotation:

                invalid_annotations.append({
                    "filename": json_file.name,
                    "annotation_index": index,
                    "reason": "Annotation is missing 'image_id'"
                })

                continue

            if annotation["image_id"] not in image_ids:

                invalid_annotations.append({
                    "filename": json_file.name,
                    "annotation_id": annotation["id"],
                    "reason": (
                        "Annotation references an image "
                        "ID that does not exist"
                    )
                })

                continue

            if "category_id" not in annotation:

                invalid_annotations.append({
                    "filename": json_file.name,
                    "annotation_id": annotation["id"],
                    "reason": "Annotation is missing 'category_id'"
                })

                continue

            if annotation["category_id"] not in category_ids:

                invalid_annotations.append({
                    "filename": json_file.name,
                    "annotation_id": annotation["id"],
                    "reason": (
                        "Annotation references a category "
                        "ID that does not exist"
                    )
                })

                continue

            # --------------------------------------------------
            # Validate bounding box
            # --------------------------------------------------

            if "bbox" in annotation:

                bbox = annotation["bbox"]

                if not isinstance(bbox, list) or len(bbox) != 4:

                    invalid_annotations.append({
                        "filename": json_file.name,
                        "annotation_id": annotation["id"],
                        "reason": (
                            "Bounding box must contain "
                            "exactly 4 values"
                        )
                    })

                    continue

                try:

                    x, y, width, height = [
                        float(value)
                        for value in bbox
                    ]

                except (TypeError, ValueError):

                    invalid_annotations.append({
                        "filename": json_file.name,
                        "annotation_id": annotation["id"],
                        "reason": (
                            "Bounding box contains "
                            "non-numeric values"
                        )
                    })

                    continue

                if width < 0 or height < 0:

                    invalid_annotations.append({
                        "filename": json_file.name,
                        "annotation_id": annotation["id"],
                        "reason": (
                            "Bounding box width and height "
                            "cannot be negative"
                        )
                    })

                    continue

    return {
        "total_json_files": len(json_files),
        "coco_files": coco_files,
        "coco_file_count": len(coco_files),
        "invalid_annotation_count": len(
            invalid_annotations
        ),
        "invalid_annotations": invalid_annotations,
        "annotations_valid": (
            len(invalid_annotations) == 0
        )
    }