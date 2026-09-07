from app.services.risk_engine import (
    calculate_risk_score,
    get_risk_status
)


def test_low_risk():

    score = calculate_risk_score(
        integrity_risk=0,
        duplicate_risk=10,
        label_risk=10,
        model_risk=0,
        inference_risk=0
    )

    assert score < 40
    assert get_risk_status(score) == "ACCEPT"


def test_medium_risk():

    score = calculate_risk_score(
        integrity_risk=40,
        duplicate_risk=60,
        label_risk=50,
        model_risk=40,
        inference_risk=50
    )

    assert 40 <= score < 70
    assert get_risk_status(score) == "REVIEW"


def test_high_risk():

    score = calculate_risk_score(
        integrity_risk=90,
        duplicate_risk=90,
        label_risk=80,
        model_risk=90,
        inference_risk=90
    )

    assert score >= 70
    assert get_risk_status(score) == "QUARANTINE"