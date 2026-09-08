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

    findings = []

    # --------------------------------------------------
    # OOD findings
    # --------------------------------------------------

    for item in detector_results.get(
        "ood_images",
        []
    ):

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

    # --------------------------------------------------
    # Trigger indicator findings
    # --------------------------------------------------

    for item in detector_results.get(
        "suspicious_images",
        []
    ):

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

    # --------------------------------------------------
    # Exact duplicate findings
    # --------------------------------------------------

    for item in detector_results.get(
        "exact_duplicates",
        []
    ):

        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "MEDIUM",
            "reason": "Exact duplicate image detected",
            "evidence": str(item),
            "confidence": 1.0,
            "recommendation": "REVIEW"
        })

    # --------------------------------------------------
    # Near duplicate findings
    # --------------------------------------------------

    for item in detector_results.get(
        "near_duplicates",
        []
    ):

        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "LOW",
            "reason": "Near duplicate image detected",
            "evidence": str(item),
            "confidence": 0.90,
            "recommendation": "REVIEW"
        })

    # --------------------------------------------------
    # Missing image findings
    # --------------------------------------------------

    for item in detector_results.get(
        "missing_images",
        []
    ):

        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "HIGH",
            "reason": "Label references an image that does not exist",
            "evidence": str(item),
            "confidence": 1.0,
            "recommendation": "REVIEW"
        })

    # --------------------------------------------------
    # Duplicate label findings
    # --------------------------------------------------

    for filename in detector_results.get(
        "duplicate_label_entries",
        []
    ):

        findings.append({
            "asset_type": asset_type,
            "asset_id": asset_id,
            "severity": "MEDIUM",
            "reason": "Duplicate label entry detected",
            "evidence": str({
                "filename": filename
            }),
            "confidence": 1.0,
            "recommendation": "REVIEW"
        })

    # --------------------------------------------------
    # Suspicious label findings
    # --------------------------------------------------

    for item in detector_results.get(
        "suspicious_labels",
        []
    ):

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

    # --------------------------------------------------
    # YOLO annotation findings
    # --------------------------------------------------

    yolo_validation = detector_results.get(
        "yolo_annotation_validation"
    )

    if yolo_validation:

        for item in yolo_validation.get(
            "invalid_annotations",
            []
        ):

            findings.append({
                "asset_type": asset_type,
                "asset_id": asset_id,
                "severity": "HIGH",
                "reason": item.get(
                    "reason",
                    "Invalid YOLO annotation detected"
                ),
                "evidence": str(item),
                "confidence": 1.0,
                "recommendation": "REVIEW"
            })

    return findings