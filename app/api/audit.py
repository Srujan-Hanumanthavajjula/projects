from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.services.audit_service import (
    record_audit_event,
    verify_audit_chain
)


router = APIRouter(
    prefix="/audit",
    tags=["Audit Trail"]
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class AuditEventRequest(BaseModel):
    event_type: str
    asset_type: str | None = None
    asset_id: str | None = None


# ============================================================
# RECORD AUDIT EVENT
# ============================================================

@router.post("/record")
def create_audit_event(
    request: AuditEventRequest,
    db: Session = Depends(get_db)
):

    event = record_audit_event(
        db=db,
        event_type=request.event_type,
        asset_type=request.asset_type,
        asset_id=request.asset_id
    )

    return {
        "status": "audit_event_recorded",
        "event_id": event.id,
        "event_type": event.event_type,
        "asset_type": event.asset_type,
        "asset_id": event.asset_id,
        "event_hash": event.event_hash,
        "previous_hash": event.previous_hash
    }


# ============================================================
# VERIFY AUDIT CHAIN
# ============================================================

@router.get("/verify")
def verify_chain(
    db: Session = Depends(get_db)
):

    result = verify_audit_chain(db)

    return {
        "status": "verification_completed",
        "results": result
    }