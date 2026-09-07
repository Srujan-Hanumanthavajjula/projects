from app.services.risk_engine import (
    calculate_risk_score,
    get_risk_status
)


def generate_assurance_report(
    integrity_risk: float = 0,
    duplicate_risk: float = 0,
    label_risk: float = 0,
    model_risk: float = 0,
    inference_risk: float = 0,
    findings: list | None = None
) -> dict:

    if findings is None:
        findings = []

    risk_score = calculate_risk_score(
        integrity_risk=integrity_risk,
        duplicate_risk=duplicate_risk,
        label_risk=label_risk,
        model_risk=model_risk,
        inference_risk=inference_risk
    )

    overall_status = get_risk_status(risk_score)

    return {
        "risk_score": risk_score,
        "overall_status": overall_status,
        "recommendation": overall_status,
        "findings": findings,
        "summary": {
            "total_findings": len(findings),
            "high_severity_findings": sum(
                1 for finding in findings
                if finding.get("severity") == "HIGH"
            ),
            "medium_severity_findings": sum(
                1 for finding in findings
                if finding.get("severity") == "MEDIUM"
            ),
            "low_severity_findings": sum(
                1 for finding in findings
                if finding.get("severity") == "LOW"
            )
        }
    }