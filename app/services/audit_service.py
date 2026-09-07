import hashlib
import json

from sqlalchemy.orm import Session

from app.database.models import AuditEvent
from app.database.crud import create_audit_event


def calculate_event_hash(
    event_type: str,
    asset_type: str | None,
    asset_id: str | None,
    previous_hash: str | None
) -> str:

    event_data = {
        "event_type": event_type,
        "asset_type": asset_type,
        "asset_id": asset_id,
        "previous_hash": previous_hash
    }

    canonical_data = json.dumps(
        event_data,
        sort_keys=True,
        separators=(",", ":")
    )

    return hashlib.sha256(
        canonical_data.encode("utf-8")
    ).hexdigest()


def record_audit_event(
    db: Session,
    event_type: str,
    asset_type: str | None = None,
    asset_id: str | None = None
):

    last_event = (
        db.query(AuditEvent)
        .order_by(AuditEvent.id.desc())
        .first()
    )

    previous_hash = (
        last_event.event_hash
        if last_event
        else None
    )

    event_hash = calculate_event_hash(
        event_type=event_type,
        asset_type=asset_type,
        asset_id=asset_id,
        previous_hash=previous_hash
    )

    return create_audit_event(
        db=db,
        event_type=event_type,
        event_hash=event_hash,
        asset_type=asset_type,
        asset_id=asset_id,
        previous_hash=previous_hash
    )


def verify_audit_chain(db: Session) -> dict:

    events = (
        db.query(AuditEvent)
        .order_by(AuditEvent.id.asc())
        .all()
    )

    previous_hash = None
    invalid_events = []

    for event in events:

        expected_hash = calculate_event_hash(
            event_type=event.event_type,
            asset_type=event.asset_type,
            asset_id=event.asset_id,
            previous_hash=previous_hash
        )

        if event.previous_hash != previous_hash:
            invalid_events.append({
                "event_id": event.id,
                "reason": "Previous hash does not match audit chain"
            })

        if event.event_hash != expected_hash:
            invalid_events.append({
                "event_id": event.id,
                "reason": "Event hash does not match event contents"
            })

        previous_hash = event.event_hash

    return {
        "total_events": len(events),
        "chain_valid": len(invalid_events) == 0,
        "invalid_event_count": len(invalid_events),
        "invalid_events": invalid_events
    }