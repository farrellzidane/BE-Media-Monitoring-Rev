from transformers import pipeline

MODEL_NAME = "ihsan31415/indo-roBERTa-financial-sentiment"

classifier = None

LABEL_MAP = {
    "LABEL_0": "Positive",
    "LABEL_1": "Neutral",
    "LABEL_2": "Negative"
}


def initialize():

    global classifier

    if classifier is None:

        classifier = pipeline(
            "text-classification",
            model=MODEL_NAME,
            tokenizer=MODEL_NAME
        )


def predict(text):

    if not text:

        return {
            "label": "Neutral",
            "confidence": 0.0
        }

    initialize()

    result = classifier(
        text[:512]
    )[0]

    return {
        "label": LABEL_MAP.get(
            result["label"],
            result["label"]
        ),
        "confidence": round(
            result["score"],
            4
        )
    }