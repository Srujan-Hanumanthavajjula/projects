from pathlib import Path
import csv


def load_labels(labels_file: Path) -> dict[str, str]:
    """
    Load filename -> label mappings from labels.csv.
    """

    labels = {}

    with open(labels_file, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        required_columns = {"filename", "label"}

        if not required_columns.issubset(reader.fieldnames or set()):
            raise ValueError(
                "labels.csv must contain 'filename' and 'label' columns"
            )

        for row in reader:
            filename = row["filename"].strip()
            label = row["label"].strip()

            if filename and label:
                labels[filename] = label

    return labels


def detect_label_anomalies(
    dataset_directory: Path,
    labels_file: Path
) -> dict:

    labels = load_labels(labels_file)

    missing_images = []
    duplicate_entries = []
    suspicious_labels = []

    # Check every label entry
    for filename, label in labels.items():

        # Search recursively so ZIPs containing folders also work
        image_matches = list(dataset_directory.rglob(filename))

        if image_matches:
            image_path = image_matches[0]
        else:
            image_path = dataset_directory / filename

        if not image_path.exists():
            missing_images.append({
                "filename": filename,
                "label": label
            })

    # Detect duplicate filename entries
    with open(labels_file, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        seen = set()

        for row in reader:
            filename = row["filename"].strip()

            if filename in seen:
                duplicate_entries.append(filename)

            seen.add(filename)

    # Detect suspicious labels using filename hints.
    # This is a lightweight baseline detector.
    for filename, label in labels.items():

        filename_lower = filename.lower()
        label_lower = label.lower()

        common_mismatch_pairs = [
            ("cat", "dog"),
            ("dog", "cat"),
            ("car", "bike"),
            ("bike", "car"),
            ("person", "animal"),
            ("animal", "person")
        ]

        for word_a, word_b in common_mismatch_pairs:

            if word_a in filename_lower and label_lower == word_b:
                suspicious_labels.append({
                    "filename": filename,
                    "provided_label": label,
                    "reason": (
                        f"Filename suggests '{word_a}' "
                        f"but label is '{word_b}'"
                    )
                })

    return {
        "total_label_entries": len(labels),
        "missing_images": missing_images,
        "duplicate_label_entries": duplicate_entries,
        "suspicious_labels": suspicious_labels,
        "anomaly_count": (
            len(missing_images)
            + len(duplicate_entries)
            + len(suspicious_labels)
        )
    }