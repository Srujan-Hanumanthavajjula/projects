from statistics import mean


def analyze_model_behavior(
    predictions: list[dict],
    confidence_threshold: float = 0.5
) -> dict:
    """
    Analyze model predictions for basic behavioral anomalies.

    Each prediction should contain:
    {
        "image": "image.jpg",
        "prediction": "cat",
        "confidence": 0.95
    }
    """

    if not predictions:
        return {
            "total_predictions": 0,
            "low_confidence_count": 0,
            "prediction_distribution": {},
            "behavior_anomalies": [],
            "average_confidence": 0
        }

    low_confidence = []
    prediction_distribution = {}

    for item in predictions:

        prediction = item.get("prediction")
        confidence = item.get("confidence", 0)

        prediction_distribution[prediction] = (
            prediction_distribution.get(prediction, 0) + 1
        )

        if confidence < confidence_threshold:
            low_confidence.append({
                "image": item.get("image"),
                "prediction": prediction,
                "confidence": confidence,
                "reason": "Model confidence is below the expected threshold"
            })

    confidence_values = [
        item.get("confidence", 0)
        for item in predictions
    ]

    average_confidence = mean(confidence_values)

    behavior_anomalies = []

    # Detect extreme prediction concentration.
    total_predictions = len(predictions)

    for label, count in prediction_distribution.items():

        ratio = count / total_predictions

        if ratio >= 0.9 and total_predictions >= 5:

            behavior_anomalies.append({
                "type": "prediction_concentration",
                "prediction": label,
                "ratio": round(ratio, 2),
                "reason": "Model predicts the same class for an unusually large proportion of inputs"
            })

    return {
        "total_predictions": total_predictions,
        "low_confidence_count": len(low_confidence),
        "prediction_distribution": prediction_distribution,
        "average_confidence": round(average_confidence, 4),
        "low_confidence_predictions": low_confidence,
        "behavior_anomalies": behavior_anomalies
    }