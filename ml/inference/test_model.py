from transformers import pipeline

model_path = "./ml/models/saved_model_cybersecurity"

classifier = pipeline(
    "text-classification",
    model=model_path,
    tokenizer=model_path
)

samples = [
    "Apple merilis pembaruan keamanan untuk memperbaiki kerentanan kritis.",
    "Data pelanggan bocor setelah sistem perusahaan diretas hacker.",
    "Artikel menjelaskan pengertian phishing tanpa melaporkan insiden baru."
]

for text in samples:
    result = classifier(text)[0]

    print("=" * 60)
    print("Headline:", text)
    print("Prediction:", result)