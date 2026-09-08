def calculate_risk_score(
    integrity_risk=0,
    duplicate_risk=0,
    label_risk=0,
    model_risk=0,
    inference_risk=0
) -> float:

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

    return round(
        min(max(score, 0), 100),
        2
    )


def get_risk_status(
    risk_score: float,
    integrity_risk: float = 0,
    model_risk: float = 0,
    inference_risk: float = 0
) -> str:

    # Critical integrity/model/inference compromise
    # must never be averaged down to ACCEPT.
    if (
        integrity_risk >= 100
        or model_risk >= 100
        or inference_risk >= 100
    ):
        return "QUARANTINE"

    if risk_score < 40:
        return "ACCEPT"

    if risk_score < 70:
        return "REVIEW"

    return "QUARANTINE"