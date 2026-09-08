from statistics import mean


def calculate_contributor_risk(
    contributor_id: str,
    findings: list[dict]
) -> dict:
    """
    Calculate contributor-level risk from assurance findings.

    Each finding should contain:
    {
        "asset_type": "dataset" | "model" | "inference",
        "asset_id": "...",
        "severity": "LOW" | "MEDIUM" | "HIGH",
        "confidence": 0.0 - 1.0
    }
    """

    if not findings:
        return {
            "contributor_id": contributor_id,
            "risk_score": 0.0,
            "overall_status": "ACCEPT",
            "recommendation": "ACCEPT",
            "total_findings": 0,
            "high_findings": 0,
            "medium_findings": 0,
            "low_findings": 0,
            "asset_summary": {
                "dataset": 0,
                "model": 0,
                "inference": 0
            }
        }

    severity_weights = {
        "LOW": 10,
        "MEDIUM": 40,
        "HIGH": 80
    }

    weighted_scores = []

    high_findings = 0
    medium_findings = 0
    low_findings = 0

    asset_summary = {
        "dataset": 0,
        "model": 0,
        "inference": 0
    }

    for finding in findings:

        severity = finding.get(
            "severity",
            "LOW"
        ).upper()

        confidence = finding.get(
            "confidence",
            1.0
        )

        confidence = max(
            0.0,
            min(float(confidence), 1.0)
        )

        base_score = severity_weights.get(
            severity,
            10
        )

        finding_score = base_score * confidence

        weighted_scores.append(
            finding_score
        )

        # ----------------------------------------------------
        # Severity counts
        # ----------------------------------------------------

        if severity == "HIGH":
            high_findings += 1

        elif severity == "MEDIUM":
            medium_findings += 1

        else:
            low_findings += 1

        # ----------------------------------------------------
        # Asset counts
        # ----------------------------------------------------

        asset_type = finding.get(
            "asset_type",
            "unknown"
        ).lower()

        if asset_type in asset_summary:
            asset_summary[asset_type] += 1

    # --------------------------------------------------------
    # Calculate average finding risk
    # --------------------------------------------------------

    risk_score = mean(
        weighted_scores
    )

    risk_score = round(
        min(max(risk_score, 0), 100),
        2
    )

    # --------------------------------------------------------
    # Critical finding override
    # --------------------------------------------------------

    if high_findings > 0:
        overall_status = "QUARANTINE"

    elif medium_findings > 0:
        overall_status = "REVIEW"

    else:
        overall_status = "ACCEPT"

    return {
        "contributor_id": contributor_id,
        "risk_score": risk_score,
        "overall_status": overall_status,
        "recommendation": overall_status,
        "total_findings": len(findings),
        "high_findings": high_findings,
        "medium_findings": medium_findings,
        "low_findings": low_findings,
        "asset_summary": asset_summary
    }