from ml.models.predict import predict


def analyze_sentiment(text):
    """
    Analyze sentiment using the cybersecurity-focused model without forcing a
    synthetic score. The confidence returned here should reflect the model's
    actual prediction strength.
    """

    if not text:
        return {
            "label": "Neutral",
            "confidence": 0.0,
            "scores": {
                "Negative": 0.0,
                "Neutral": 1.0,
                "Positive": 0.0
            }
        }

    return predict(text)