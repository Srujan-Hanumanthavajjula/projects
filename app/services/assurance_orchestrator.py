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

    if detector_results.get("integrity_status") == "TAMPERED":
        integrity_risk = 100

    # --------------------------------------------------------
    # Duplicate detection
    # --------------------------------------------------------

    exact_duplicates = detector_results.get(
        "exact_duplicate_count", 0
    )

    near_duplicates = detector_results.get(
        "near_duplicate_count", 0
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
        "anomaly_count", 0
    )

    if label_anomalies > 0:
        label_risk = min(
            100,
            label_anomalies * 20
        )

    # --------------------------------------------------------
    # Model behavior / integrity
    # --------------------------------------------------------

    if detector_results.get("model_integrity_status") == "TAMPERED":
        model_risk = 100

    behavior_anomalies = detector_results.get(
        "behavior_anomalies", []
    )

    if behavior_anomalies:
        model_risk = max(
            model_risk,
            min(100, len(behavior_anomalies) * 30)
        )

    # --------------------------------------------------------
    # Inference
    # --------------------------------------------------------

    if detector_results.get("inference_status") == "TAMPERED":
        inference_risk = 100

    if detector_results.get("replay_detected") is True:
        inference_risk = max(
            inference_risk,
            70
        )

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

    risks = calculate_component_risk(
        detector_results
    )

    risk_score = calculate_risk_score(
        integrity_risk=risks["integrity_risk"],
        duplicate_risk=risks["duplicate_risk"],
        label_risk=risks["label_risk"],
        model_risk=risks["model_risk"],
        inference_risk=risks["inference_risk"]
    )

    overall_status = get_risk_status(
        risk_score
    )

    return {
        "risk_score": risk_score,
        "overall_status": overall_status,
        "recommendation": overall_status,
        "component_risks": risks,
        "findings": findings,
        "finding_count": len(findings)
    }