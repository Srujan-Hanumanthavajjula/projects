from app.services.risk_engine import (
    calculate_risk_score,
    get_risk_status
)


def calculate_component_risk(
    detector_results: dict
) -> dict:
    """
    Convert detector results into normalized 0-100
    risk values for the assurance engine.
    """

    integrity_risk = 0
    duplicate_risk = 0
    label_risk = 0
    model_risk = 0
    inference_risk = 0

    # --------------------------------------------------------
    # Integrity
    # --------------------------------------------------------

    if detector_results.get(
        "integrity_status"
    ) == "TAMPERED":

        integrity_risk = 100

    # --------------------------------------------------------
    # Duplicate detection
    # --------------------------------------------------------

    exact_duplicates = detector_results.get(
        "exact_duplicate_count",
        0
    )

    near_duplicates = detector_results.get(
        "near_duplicate_count",
        0
    )

    if exact_duplicates > 0:

        duplicate_risk = min(
            100,
            50 + exact_duplicates * 10
        )

    elif near_duplicates > 0:

        duplicate_risk = min(
            100,
            near_duplicates * 10
        )

    # --------------------------------------------------------
    # Label anomalies
    # --------------------------------------------------------

    label_anomalies = detector_results.get(
        "anomaly_count",
        0
    )

    if label_anomalies > 0:

        label_risk = min(
            100,
            label_anomalies * 20
        )

    # --------------------------------------------------------
    # OOD Detection
    # --------------------------------------------------------

    ood_count = detector_results.get(
        "ood_count",
        0
    )

    total_images = detector_results.get(
        "total_images",
        0
    )

    if ood_count > 0:

        if total_images > 0:

            ood_ratio = ood_count / total_images

            ood_risk = min(
                100,
                ood_ratio * 100
            )

        else:

            ood_risk = 50

        # OOD is treated as an integrity/data-quality
        # risk signal.
        integrity_risk = max(
            integrity_risk,
            round(ood_risk, 2)
        )

    # --------------------------------------------------------
    # Trigger / Backdoor Indicators
    # --------------------------------------------------------

    suspicious_count = detector_results.get(
        "suspicious_count",
        0
    )

    if suspicious_count > 0:

        # Trigger detector provides an indicator,
        # not proof of a backdoor.
        #
        # Therefore we assign a high risk signal
        # without declaring the dataset malicious.

        trigger_risk = min(
            100,
            70 + suspicious_count * 10
        )

        integrity_risk = max(
            integrity_risk,
            trigger_risk
        )

    # --------------------------------------------------------
    # Annotation validation risk
    # --------------------------------------------------------

    yolo_validation = detector_results.get(
        "yolo_annotation_validation"
    )

    coco_validation = detector_results.get(
        "coco_annotation_validation"
    )

    annotation_risk = 0

    # YOLO annotation risk
    if yolo_validation:

        invalid_count = yolo_validation.get(
            "invalid_annotation_count",
            0
        )

        if invalid_count > 0:

            annotation_risk = min(
                100,
                invalid_count * 20
            )

    # COCO annotation risk
    if coco_validation:

        invalid_count = coco_validation.get(
            "invalid_annotation_count",
            0
        )

        if invalid_count > 0:

            annotation_risk = max(
                annotation_risk,
                min(
                    100,
                    invalid_count * 20
                )
            )

    integrity_risk = max(
        integrity_risk,
        annotation_risk
    )

    # --------------------------------------------------------
    # Model integrity
    # --------------------------------------------------------

    if detector_results.get(
        "model_integrity_status"
    ) == "TAMPERED":

        model_risk = 100

    # --------------------------------------------------------
    # Model behavior
    # --------------------------------------------------------

    behavior_anomalies = detector_results.get(
        "behavior_anomalies",
        []
    )

    if behavior_anomalies:

        model_risk = max(
            model_risk,
            min(
                100,
                len(behavior_anomalies) * 30
            )
        )

    # --------------------------------------------------------
    # Inference integrity
    # --------------------------------------------------------

    if detector_results.get(
        "inference_status"
    ) == "TAMPERED":

        inference_risk = 100

    # --------------------------------------------------------
    # Replay detection
    # --------------------------------------------------------

    if detector_results.get(
        "replay_detected"
    ) is True:

        inference_risk = max(
            inference_risk,
            70
        )

    # --------------------------------------------------------
    # Return component risks
    # --------------------------------------------------------

    return {
        "integrity_risk": integrity_risk,
        "duplicate_risk": duplicate_risk,
        "label_risk": label_risk,
        "model_risk": model_risk,
        "inference_risk": inference_risk
    }


def generate_assurance_decision(
    detector_results: dict,
    findings: list[dict] | None = None
) -> dict:

    if findings is None:
        findings = []

    # --------------------------------------------------------
    # Calculate component risks
    # --------------------------------------------------------

    risks = calculate_component_risk(
        detector_results
    )

    # --------------------------------------------------------
    # Calculate weighted risk score
    # --------------------------------------------------------

    risk_score = calculate_risk_score(
        integrity_risk=risks["integrity_risk"],
        duplicate_risk=risks["duplicate_risk"],
        label_risk=risks["label_risk"],
        model_risk=risks["model_risk"],
        inference_risk=risks["inference_risk"]
    )

    # --------------------------------------------------------
    # Determine final assurance status
    #
    # Critical integrity/model/inference risk
    # overrides the weighted average.
    # --------------------------------------------------------

    overall_status = get_risk_status(
        risk_score,
        integrity_risk=risks["integrity_risk"],
        model_risk=risks["model_risk"],
        inference_risk=risks["inference_risk"]
    )

    # --------------------------------------------------------
    # Final assurance decision
    # --------------------------------------------------------

    return {
        "risk_score": risk_score,
        "overall_status": overall_status,
        "recommendation": overall_status,
        "component_risks": risks,
        "findings": findings,
        "finding_count": len(findings)
    }