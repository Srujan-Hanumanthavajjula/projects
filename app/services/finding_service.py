from sqlalchemy.orm import Session

from app.database.crud import create_finding


def save_finding(
    db: Session,
    asset_type: str,
    asset_id: str,
    severity: str,
    reason: str,
    evidence: str | None = None,
    confidence: float | None = None,
    recommendation: str | None = None
):
    return create_finding(
        db=db,
        asset_type=asset_type,
        asset_id=asset_id,
        severity=severity,
        reason=reason,
        evidence=evidence,
        confidence=confidence,
        recommendation=recommendation
    )


def save_findings(
    db: Session,
    findings: list[dict]
) -> list:

    saved_findings = []

    for finding in findings:

        saved = save_finding(
            db=db,
            asset_type=finding["asset_type"],
            asset_id=finding["asset_id"],
            severity=finding["severity"],
            reason=finding["reason"],
            evidence=finding.get("evidence"),
            confidence=finding.get("confidence"),
            recommendation=finding.get("recommendation")
        )

        saved_findings.append(saved)

    return saved_findings
def findings_from_detector_results(
    asset_type: str,
    asset_id: str,
    detector_results: dict
) -> list[dict]:
    """
    Convert detector output into standardized findings.
    """

    findings = []

    # OOD findings
    for item in detector_results.get("ood_images", []):
        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "MEDIUM",
            "reason": item.get(
                "reason",
                "Out-of-distribution image detected"
            ),
            "evidence": str(item),
            "confidence": 0.80,
            "recommendation": "REVIEW"
        })

    # Trigger / backdoor indicator findings
    for item in detector_results.get("suspicious_images", []):
        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "HIGH",
            "reason": item.get(
                "reason",
                "Suspicious trigger indicator detected"
            ),
            "evidence": str(item),
            "confidence": 0.85,
            "recommendation": "QUARANTINE"
        })

    # Duplicate findings
    for item in detector_results.get("exact_duplicates", []):
        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "MEDIUM",
            "reason": "Exact duplicate image detected",
            "evidence": str(item),
            "confidence": 1.0,
            "recommendation": "REVIEW"
        })

    for item in detector_results.get("near_duplicates", []):
        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "LOW",
            "reason": "Near duplicate image detected",
            "evidence": str(item),
            "confidence": 0.90,
            "recommendation": "REVIEW"
        })

    # Label anomaly findings
    for item in detector_results.get("suspicious_labels", []):
        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "MEDIUM",
            "reason": item.get(
                "reason",
                "Suspicious label detected"
            ),
            "evidence": str(item),
            "confidence": 0.80,
            "recommendation": "REVIEW"
        })

    return findings