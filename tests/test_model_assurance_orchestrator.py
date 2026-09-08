from app.services.assurance_orchestrator import (
    calculate_component_risk,
    generate_assurance_decision
)


def test_invalid_model_format_creates_critical_model_risk():

    detector_results = {
        "format": "ONNX",
        "format_valid": False
    }

    risks = calculate_component_risk(
        detector_results
    )

    assert risks["model_risk"] == 100


def test_valid_model_format_has_no_format_risk():

    detector_results = {
        "format": "ONNX",
        "format_valid": True
    }

    risks = calculate_component_risk(
        detector_results
    )

    assert risks["model_risk"] == 0


def test_invalid_model_format_quarantines():

    detector_results = {
        "format": "ONNX",
        "format_valid": False
    }

    decision = generate_assurance_decision(
        detector_results
    )

    assert decision["component_risks"]["model_risk"] == 100
    assert decision["overall_status"] == "QUARANTINE"