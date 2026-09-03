from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_CANDIDATES = [
    Path(__file__).resolve().parent / "saved_model_cybersecurity",
    Path(__file__).resolve().parent / "saved_model",
    Path(__file__).resolve().parent / "saved_model_backup2",
]

MODEL_PATH = None
for candidate in MODEL_CANDIDATES:
    if candidate.exists() and (
        (candidate / "config.json").exists() and
        (
            (candidate / "model.safetensors").exists()
            or (candidate / "pytorch_model.bin").exists()
        )
    ):
        MODEL_PATH = candidate
        break

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

tokenizer = None
model = None

if MODEL_PATH is not None:
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
        model.to(device)
        model.eval()
    except Exception:
        tokenizer = None
        model = None

LABELS = {
    0: "Negative",
    1: "Neutral",
    2: "Positive",
}


def predict(text: str):
    if model is None or tokenizer is None:
        return {
            "label": "Neutral",
            "confidence": 0.0,
            "scores": {
                "Negative": 0.0,
                "Neutral": 1.0,
                "Positive": 0.0,
            },
        }

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256,
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
        },
    }


if __name__ == "__main__":

    text = text = """
        Perusahaan mengalami kerugian besar setelah pendapatan turun drastis.
        Manajemen mengumumkan PHK terhadap ribuan karyawan akibat kondisi keuangan yang memburuk.
        Harga saham perusahaan juga anjlok tajam setelah laporan keuangan dirilis.
"""

    result = predict(text)

    print(result)
