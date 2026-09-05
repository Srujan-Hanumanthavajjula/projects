from pathlib import Path

from app.detectors.label_anomaly_detector import detect_label_anomalies


dataset_path = Path("label-test/images")
labels_path = Path("label-test/labels.csv")


result = detect_label_anomalies(
    dataset_path,
    labels_path
)

print(result)