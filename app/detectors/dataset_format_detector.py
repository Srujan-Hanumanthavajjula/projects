from pathlib import Path


def detect_dataset_format(dataset_directory: Path) -> dict:
    """
    Detect common computer-vision dataset annotation formats.

    Supported baseline formats:
    - COCO JSON
    - YOLO TXT
    - CSV labels
    - Unknown
    """

    json_files = list(
        dataset_directory.rglob("*.json")
    )

    txt_files = list(
        dataset_directory.rglob("*.txt")
    )

    csv_files = list(
        dataset_directory.rglob("*.csv")
    )

    # --------------------------------------------------------
    # COCO detection
    # --------------------------------------------------------

    coco_files = []

    for json_file in json_files:

        try:
            import json

            with open(
                json_file,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if (
                isinstance(data, dict)
                and "images" in data
                and "annotations" in data
                and "categories" in data
            ):
                coco_files.append(
                    json_file.name
                )

        except Exception:
            continue

    if coco_files:

        return {
            "format": "COCO",
            "confidence": 1.0,
            "annotation_files": coco_files,
            "reason": "COCO dataset structure detected"
        }

    # --------------------------------------------------------
    # YOLO detection
    # --------------------------------------------------------

    yolo_files = []

    for txt_file in txt_files:

        try:

            with open(
                txt_file,
                "r",
                encoding="utf-8"
            ) as file:

                lines = [
                    line.strip()
                    for line in file
                    if line.strip()
                ]

            valid_yolo = True

            for line in lines:

                parts = line.split()

                if len(parts) != 5:
                    valid_yolo = False
                    break

                try:

                    int(parts[0])

                    values = [
                        float(value)
                        for value in parts[1:]
                    ]

                    if not all(
                        0 <= value <= 1
                        for value in values
                    ):
                        valid_yolo = False
                        break

                except ValueError:

                    valid_yolo = False
                    break

            if valid_yolo and lines:
                yolo_files.append(
                    txt_file.name
                )

        except Exception:
            continue

    if yolo_files:

        return {
            "format": "YOLO",
            "confidence": 1.0,
            "annotation_files": yolo_files,
            "reason": "YOLO annotation structure detected"
        }

    # --------------------------------------------------------
    # CSV labels
    # --------------------------------------------------------

    if csv_files:

        for csv_file in csv_files:

            if csv_file.name.lower() == "labels.csv":

                return {
                    "format": "CSV_LABELS",
                    "confidence": 1.0,
                    "annotation_files": [
                        csv_file.name
                    ],
                    "reason": "labels.csv detected"
                }

    # --------------------------------------------------------
    # Unknown format
    # --------------------------------------------------------

    return {
        "format": "UNKNOWN",
        "confidence": 0.0,
        "annotation_files": [],
        "reason": "No supported dataset annotation format detected"
    }