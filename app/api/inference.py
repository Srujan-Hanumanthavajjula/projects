# ============================================================
# CREATE INFERENCE RECORD
# ============================================================

@router.post("/create")
def create_inference_record(
    request: InferenceRequest,
    db: Session = Depends(get_db)
):

    inference_id = f"INF-{uuid.uuid4().hex[:8].upper()}"

    inference_record = {
        "image": request.image,
        "prediction": request.prediction,
        "confidence": request.confidence
    }

    # --------------------------------------------------------
    # Calculate input hash
    # --------------------------------------------------------

    input_hash = calculate_inference_hash({
        "image": request.image
    })

    # --------------------------------------------------------
    # Calculate output hash
    # --------------------------------------------------------

    output_hash = calculate_inference_hash(
        inference_record
    )

    # --------------------------------------------------------
    # Bind input + model + output together
    # --------------------------------------------------------

    binding_hash = calculate_inference_binding_hash(
        input_hash=input_hash,
        model_hash=request.model_hash,
        output_hash=output_hash
    )

    # --------------------------------------------------------
    # Save inference evidence to PostgreSQL
    # --------------------------------------------------------

    create_inference(
        db=db,
        inference_id=inference_id,
        input_hash=input_hash,
        model_hash=request.model_hash,
        output_hash=output_hash,
        integrity_status="VERIFIED",
        replay_detected=False
    )

    # --------------------------------------------------------
    # Record audit event
    # --------------------------------------------------------

    record_audit_event(
        db=db,
        event_type="INFERENCE_CREATED",
        asset_type="inference",
        asset_id=inference_id
    )

    return {
        "inference_id": inference_id,
        "image": request.image,
        "prediction": request.prediction,
        "confidence": request.confidence,
        "model_hash": request.model_hash,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "binding_hash": binding_hash,
        "integrity_status": "VERIFIED",
        "database_saved": True,
        "audit_event_recorded": True
    }