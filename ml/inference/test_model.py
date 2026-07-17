from transformers import pipeline

model_path = "./ml/models/sentiment_model/checkpoint-1375"

classifier = pipeline(
    "text-classification",
    model=model_path,
    tokenizer=model_path
)

samples = [
    "IHSG anjlok akibat konflik perang global",
    "Timnas Indonesia menang telak 3-0",
    "Pemerintah bahas kebijakan ekonomi baru",
    "Harga saham teknologi melemah hari ini",
    "Jokowi bertemu investor asing di Jakarta"
]

for text in samples:
    result = classifier(text)[0]

    print("=" * 60)
    print("Headline:", text)
    print("Prediction:", result)