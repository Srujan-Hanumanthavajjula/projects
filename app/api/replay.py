from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.detectors.replay_detector import detect_replay
from app.database.connection import get_db
from app.services.replay_assurance import run_replay_assurance


router = APIRouter(
    prefix="/replay",
    tags=["Replay Assurance"]
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class InferenceRecord(BaseModel):
    input_hash: str
    model_hash: str
    output_hash: str


class ReplayRequest(BaseModel):
    inference_records: list[InferenceRecord]


# ============================================================
# MANUAL REPLAY ANALYSIS
# ============================================================

@router.post("/analyze")
def analyze_replay(
    request: ReplayRequest
):

    records = [
        {
            "input_hash": record.input_hash,
            "model_hash": record.model_hash,
            "output_hash": record.output_hash
        }
        for record in request.inference_records
    ]

    result = detect_replay(records)

    return {
        "status": "analysis_completed",
        "results": result
    }


# ============================================================
# DATABASE-BACKED REPLAY ASSURANCE
# ============================================================

@router.get("/assurance")
def replay_assurance(
    db: Session = Depends(get_db)
):

    result = run_replay_assurance(
        db=db
    )

    return {
        "status": "replay_assurance_completed",

        "total_inference_records": result[
            "total_inference_records"
        ],

        "replay_count": result[
            "replay_count"
        ],

        "replay_detected": result[
            "replay_detected"
        ],

        "status_decision": result[
            "status"
        ],

        "finding_count": result[
            "finding_count"
        ],

        "findings": result[
            "findings"
        ],

        "replayed_records": result[
            "replayed_records"
        ]
    }