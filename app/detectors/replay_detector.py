def detect_replay(
    inference_records: list[dict]
) -> dict:
    """
    Detect repeated inference records.

    Each record should contain:
    {
        "input_hash": "...",
        "model_hash": "...",
        "output_hash": "..."
    }
    """

    seen = set()
    replayed_records = []

    for record in inference_records:

        input_hash = record.get("input_hash")
        model_hash = record.get("model_hash")
        output_hash = record.get("output_hash")

        fingerprint = (
            input_hash,
            model_hash,
            output_hash
        )

        if fingerprint in seen:
            replayed_records.append({
                "input_hash": input_hash,
                "model_hash": model_hash,
                "output_hash": output_hash,
                "reason": "Identical inference evidence was observed more than once"
            })
        else:
            seen.add(fingerprint)

    return {
        "total_records": len(inference_records),
        "replay_count": len(replayed_records),
        "replay_detected": len(replayed_records) > 0,
        "replayed_records": replayed_records
    }