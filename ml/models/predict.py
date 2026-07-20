from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

MODEL_PATH = "ml/models/saved_model"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
model.to(device)
model.eval()

LABELS = {
    0: "Negative",
    1: "Neutral",
    2: "Positive"
}


def predict(text: str):

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():

        outputs = model(**inputs)

        probabilities = torch.softmax(outputs.logits, dim=-1)

        confidence, prediction = torch.max(probabilities, dim=1)

    return {
        "label": LABELS[prediction.item()],
        "confidence": float(confidence.item()),
        "scores": {
            LABELS[i]: float(probabilities[0][i])
            for i in range(len(LABELS))
        }
    }


if __name__ == "__main__":

    text = """
    IHSG ditutup menguat hampir 2 persen setelah investor asing kembali melakukan pembelian besar.
    """

    result = predict(text)

    print(result)