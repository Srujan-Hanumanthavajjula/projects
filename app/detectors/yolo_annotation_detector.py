from pathlib import Path


def validate_yolo_annotations(
    dataset_directory: Path,
    num_classes: int | None = None
) -> dict:
    """
    Validate YOLO annotation TXT files.

    Expected YOLO format per line:

        class_id x_center y_center width height

    Coordinates and dimensions must normally be
    between 0 and 1.
    """

    txt_files = list(
        dataset_directory.rglob("*.txt")
    )

    total_files = len(txt_files)

    invalid_annotations = []
    valid_annotation_count = 0

    for txt_file in txt_files:

        try:
            with open(
                txt_file,
                "r",
                encoding="utf-8"
            ) as file:

                lines = file.readlines()

        except Exception as error:

            invalid_annotations.append({
                "filename": txt_file.name,
                "line": 0,
                "reason": f"Unable to read annotation file: {error}"
            })

            continue

        for line_number, raw_line in enumerate(
            lines,
            start=1
        ):

            line = raw_line.strip()

            # Ignore empty lines
            if not line:
                continue

            parts = line.split()

            # YOLO requires exactly 5 values
            if len(parts) != 5:

                invalid_annotations.append({
                    "filename": txt_file.name,
                    "line": line_number,
                    "content": line,
                    "reason": "YOLO annotation must contain exactly 5 values"
                })

                continue

            try:

                class_id = int(parts[0])

                x_center = float(parts[1])
                y_center = float(parts[2])
                width = float(parts[3])
                height = float(parts[4])

            except ValueError:

                invalid_annotations.append({
                    "filename": txt_file.name,
                    "line": line_number,
                    "content": line,
                    "reason": "YOLO annotation contains non-numeric values"
                })

                continue

            # Validate class ID
            if class_id < 0:

                invalid_annotations.append({
                    "filename": txt_file.name,
                    "line": line_number,
                    "content": line,
                    "reason": "Class ID cannot be negative"
                })

                continue

            # Validate class ID against known number of classes
            if (
                num_classes is not None
                and class_id >= num_classes
            ):

                invalid_annotations.append({
                    "filename": txt_file.name,
                    "line": line_number,
                    "content": line,
                    "reason": (
                        f"Class ID {class_id} is outside "
                        f"the valid range 0-{num_classes - 1}"
                    )
                })

                continue

            # Validate normalized coordinates
            values = {
                "x_center": x_center,
                "y_center": y_center,
                "width": width,
                "height": height
            }

            invalid_value = False

            for name, value in values.items():

                if not 0 <= value <= 1:

                    invalid_annotations.append({
                        "filename": txt_file.name,
                        "line": line_number,
                        "content": line,
                        "reason": (
                            f"{name} must be between 0 and 1"
                        )
                    })

                    invalid_value = True
                    break

            if invalid_value:
                continue

            # Valid annotation
            valid_annotation_count += 1

    return {
        "total_annotation_files": total_files,
        "valid_annotation_count": valid_annotation_count,
        "invalid_annotation_count": len(
            invalid_annotations
        ),
        "invalid_annotations": invalid_annotations,
        "annotations_valid": len(
            invalid_annotations
        ) == 0
    }