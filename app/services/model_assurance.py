from pathlib import Path

from app.detectors.model_format_detector import detect_model_format


def run_model_assurance(model_path: Path) -> dict:
    """
    Run model-format detection and validation.

    Returns a normalized result that can be consumed
    by the assurance/risk pipeline.
    """

    format_result = detect_model_format(model_path)

    model_format = format_result.get("format", "UNKNOWN")
    valid = format_result.get("valid", False)

    model_risk = 0

    findings = []

    # --------------------------------------------------
    # Unknown model format
    # --------------------------------------------------

    if model_format == "UNKNOWN":

        model_risk = 70

        findings.append(
            {
                "severity": "MEDIUM",
                "reason": "Unsupported or unknown model format",
                "evidence": str(format_result),
                "confidence": format_result.get("confidence", 0.0),
                "recommendation": "REVIEW"
            }
        )

    # --------------------------------------------------
    # Known format but validation failed
    # --------------------------------------------------

    elif valid is False:

        model_risk = 100

        findings.append(
            {
                "severity": "HIGH",
                "reason": "Model format detected but structural validation failed",
                "evidence": str(format_result),
                "confidence": format_result.get("confidence", 0.0),
                "recommendation": "QUARANTINE"
            }
        )

    # --------------------------------------------------
    # Valid model
    # --------------------------------------------------

    elif valid is True:

        model_risk = 0

    # --------------------------------------------------
    # Validation unavailable
    # --------------------------------------------------

    else:

        model_risk = 30

        findings.append(
            {
                "severity": "LOW",
                "reason": "Model format detected but validation could not be completed",
                "evidence": str(format_result),
                "confidence": format_result.get("confidence", 0.0),
                "recommendation": "REVIEW"
            }
        )

    return {
        "model_filename": model_path.name,
        "model_format": model_format,
        "format_confidence": format_result.get("confidence", 0.0),
        "format_valid": valid,
        "format_reason": format_result.get("reason"),
        "model_risk": model_risk,
        "findings": findings
    }