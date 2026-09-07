from sqlalchemy.orm import Session

from app.database.models import (
    Dataset,
    Model,
    Inference,
    Finding,
    AssuranceAssessment,
    AuditEvent
)


def create_dataset(
    db: Session,
    dataset_id: str,
    filename: str,
    sha256: str,
    integrity_status: str
):
    dataset = Dataset(
        dataset_id=dataset_id,
        filename=filename,
        sha256=sha256,
        integrity_status=integrity_status
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    return dataset


def create_model(
    db: Session,
    model_id: str,
    filename: str,
    sha256: str,
    integrity_status: str
):
    model = Model(
        model_id=model_id,
        filename=filename,
        sha256=sha256,
        integrity_status=integrity_status
    )

    db.add(model)
    db.commit()
    db.refresh(model)

    return model


def create_inference(
    db: Session,
    inference_id: str,
    input_hash: str,
    model_hash: str,
    output_hash: str,
    integrity_status: str,
    replay_detected: bool = False
):
    inference = Inference(
        inference_id=inference_id,
        input_hash=input_hash,
        model_hash=model_hash,
        output_hash=output_hash,
        integrity_status=integrity_status,
        replay_detected=replay_detected
    )

    db.add(inference)
    db.commit()
    db.refresh(inference)

    return inference


def create_finding(
    db: Session,
    asset_type: str,
    asset_id: str,
    severity: str,
    reason: str,
    evidence: str = None,
    confidence: float = None,
    recommendation: str = None
):
    finding = Finding(
        asset_type=asset_type,
        asset_id=asset_id,
        severity=severity,
        reason=reason,
        evidence=evidence,
        confidence=confidence,
        recommendation=recommendation
    )

    db.add(finding)
    db.commit()
    db.refresh(finding)

    return finding


def create_assurance_assessment(
    db: Session,
    assurance_id: str,
    overall_status: str,
    risk_score: float
):
    assessment = AssuranceAssessment(
        assurance_id=assurance_id,
        overall_status=overall_status,
        risk_score=risk_score
    )

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return assessment


def create_audit_event(
    db: Session,
    event_type: str,
    event_hash: str,
    asset_type: str = None,
    asset_id: str = None,
    previous_hash: str = None
):
    event = AuditEvent(
        event_type=event_type,
        asset_type=asset_type,
        asset_id=asset_id,
        event_hash=event_hash,
        previous_hash=previous_hash
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event