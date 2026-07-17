from transformers import pipeline

classifier = None


def initialize_model():
    global classifier

    if classifier is None:
        classifier = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-xlm-roberta-base-sentiment",
            tokenizer="cardiffnlp/twitter-xlm-roberta-base-sentiment"
        )


def analyze_sentiment(text):

    if not text:
        return {
            "label": "Neutral",
            "confidence": 0.0
        }

    initialize_model()

    result = classifier(
        text[:512]
    )[0]

    label_map = {
        "label_0": "Negative",
        "label_1": "Neutral",
        "label_2": "Positive",
        "negative": "Negative",
        "neutral": "Neutral",
        "positive": "Positive",
    }

    raw_label = str(result["label"]).strip().lower()

    return {
        "label": label_map.get(raw_label, "Neutral"),
        "confidence": round(
            result["score"],
            4
        )
    }