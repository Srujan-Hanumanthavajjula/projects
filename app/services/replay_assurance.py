from sqlalchemy.orm import Session

from app.database.models import Inference
from app.detectors.replay_detector import detect_replay
from app.database.crud import create_finding
from app.services.audit_service import record_audit_event


def run_replay_assurance(
    db: Session
) -> dict:
    """
    Run replay detection against inference records
    stored in PostgreSQL.
    """

    # --------------------------------------------------------
    # Load inference records from database
    # --------------------------------------------------------

    inference_records = (
        db.query(Inference)
        .order_by(Inference.id.asc())
        .all()
    )

    # --------------------------------------------------------
    # Convert database records into detector input
    # --------------------------------------------------------

    detector_records = []

    for inference in inference_records:

        detector_records.append({
            "inference_id": inference.inference_id,
            "input_hash": inference.input_hash,
            "model_hash": inference.model_hash,
            "output_hash": inference.output_hash
        })

    # --------------------------------------------------------
    # Run replay detector
    # --------------------------------------------------------

    replay_result = detect_replay(
        detector_records
    )

    findings = []

    # --------------------------------------------------------
    # Create findings for replayed records
    # --------------------------------------------------------

    if replay_result["replay_detected"]:

        for item in replay_result["replayed_records"]:

            matching_inference = None

            for inference in inference_records:

                if (
                    inference.input_hash
                    == item["input_hash"]
                    and
                    inference.model_hash
                    == item["model_hash"]
                    and
                    inference.output_hash
                    == item["output_hash"]
                ):
                    matching_inference = inference
                    break

            asset_id = (
                matching_inference.inference_id
                if matching_inference
                else "UNKNOWN"
            )

            finding = {
                "asset_type": "inference",
                "asset_id": asset_id,
                "severity": "MEDIUM",
                "reason": item.get(
                    "reason",
                    "Repeated inference evidence detected"
                ),
                "evidence": str(item),
                "confidence": 1.0,
                "recommendation": "REVIEW"
            }

            findings.append(finding)

            # ------------------------------------------------
            # Save finding to PostgreSQL
            # ------------------------------------------------

            create_finding(
                db=db,
                asset_type=finding["asset_type"],
                asset_id=finding["asset_id"],
                severity=finding["severity"],
                reason=finding["reason"],
                evidence=finding["evidence"],
                confidence=finding["confidence"],
                recommendation=finding["recommendation"]
            )

            # ------------------------------------------------
            # Record audit event
            # ------------------------------------------------

            record_audit_event(
                db=db,
                event_type="INFERENCE_REPLAY_DETECTED",
                asset_type="inference",
                asset_id=asset_id
            )

    # --------------------------------------------------------
    # Return assurance result
    # --------------------------------------------------------

    return {
        "total_inference_records": len(inference_records),
        "replay_count": replay_result["replay_count"],
        "replay_detected": replay_result["replay_detected"],
        "replayed_records": replay_result["replayed_records"],
        "findings": findings,
        "finding_count": len(findings),
        "status": (
            "REVIEW"
            if replay_result["replay_detected"]
            else "VERIFIED"
        )
    }