from services.sentiment_service import analyze_sentiment

TEST_CASES = [
    ("IHSG menguat setelah Bank Indonesia menurunkan suku bunga", "Positive"),
    ("Harga saham BBCA melonjak 8 persen", "Positive"),
    ("Laba bersih BBRI naik signifikan", "Positive"),
    ("Rupiah melemah ke Rp18.100 per dolar AS", "Negative"),
    ("IHSG anjlok 4 persen akibat tekanan global", "Negative"),
    ("Harga minyak dunia melonjak karena konflik Timur Tengah", "Negative"),
    ("Bank Indonesia mempertahankan suku bunga acuan", "Neutral"),
    ("BEI mengumumkan jadwal perdagangan pekan depan", "Neutral"),
    ("OJK menggelar konferensi pers hari ini", "Neutral"),
]

correct = 0

print("=" * 80)
print("SENTIMENT MODEL BENCHMARK")
print("=" * 80)

for text, expected in TEST_CASES:

    result = analyze_sentiment(text)

    predicted = result["label"].capitalize()

    expected = expected.capitalize()

    confidence = result["confidence"]

    status = "OK" if predicted == expected else "WRONG"

    if predicted == expected:
        correct += 1

    print()
    print(text)
    print(f"Expected  : {expected}")
    print(f"Predicted : {predicted}")
    print(f"Confidence: {confidence}")
    print(f"Result    : {status}")

print()
print("=" * 80)
print(f"Accuracy : {correct}/{len(TEST_CASES)} ({correct/len(TEST_CASES)*100:.1f}%)")
print("=" * 80)