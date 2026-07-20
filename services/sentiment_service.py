from ml.models.predict import predict


def analyze_sentiment(text):
    """
    Analyze sentiment using the locally fine-tuned IndoBERT model.

    Returns:
    {
        "label": "Positive",
        "confidence": 0.91,
        "scores": {
            "Negative": 0.03,
            "Neutral": 0.06,
            "Positive": 0.91
        }
    }
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