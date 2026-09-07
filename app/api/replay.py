from fastapi import APIRouter
from pydantic import BaseModel

from app.detectors.replay_detector import detect_replay


router = APIRouter(
    prefix="/replay",
    tags=["Replay Detection"]
)


class InferenceRecord(BaseModel):
    input_hash: str
    model_hash: str
    output_hash: str


class ReplayRequest(BaseModel):
    inference_records: list[InferenceRecord]


@router.post("/analyze")
def analyze_replay(request: ReplayRequest):

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