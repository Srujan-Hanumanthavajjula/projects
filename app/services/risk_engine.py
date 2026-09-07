def calculate_risk_score(
    integrity_risk: float = 0,
    duplicate_risk: float = 0,
    label_risk: float = 0,
    model_risk: float = 0,
    inference_risk: float = 0
) -> float:
    """
    Calculate an overall CV integrity risk score.

    Each risk value should be between 0 and 100.
    """

    weights = {
        "integrity": 0.25,
        "duplicate": 0.15,
        "label": 0.15,
        "model": 0.25,
        "inference": 0.20
    }

    score = (
        integrity_risk * weights["integrity"]
        + duplicate_risk * weights["duplicate"]
        + label_risk * weights["label"]
        + model_risk * weights["model"]
        + inference_risk * weights["inference"]
    )

    return round(min(max(score, 0), 100), 2)


def get_risk_status(risk_score: float) -> str:
    """
    Convert risk score into an assurance decision.
    """

    if risk_score < 40:
        return "ACCEPT"

    if risk_score < 70:
        return "REVIEW"

    return "QUARANTINE"