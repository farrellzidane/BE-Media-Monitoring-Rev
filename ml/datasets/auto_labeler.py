import os
import json
import time
import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)


MODEL = "qwen/qwen3-30b-a3b"

INPUT_FILE = "ml/datasets/raw/financial_news.csv"
OUTPUT_FILE = "ml/datasets/labeled/financial_news_labeled.csv"

PROMPT = """
You are a professional financial sentiment analyst.

Analyze BOTH the title and the content.

Choose EXACTLY ONE label:

Positive
Neutral
Negative

Definitions:

Positive:
- Revenue growth
- Profit increase
- Business expansion
- Investment
- Partnership
- Stock price increase
- Credit rating upgrade
- Economic growth
- Strong financial outlook

Negative:
- Revenue decline
- Loss
- Layoffs
- Bankruptcy
- Corruption
- Lawsuit
- Inflation
- Rising prices
- Oil price spikes
- Geopolitical conflict affecting markets
- Weak earnings
- Debt risk
- Stock decline
- Economic slowdown
- Financial uncertainty

Neutral:
Use Neutral ONLY if the article is purely informational and contains no clear positive or negative financial implication.

Return ONLY valid JSON.

Example:

{
    "label":"Positive",
    "reason":"Company reported record earnings."
}

Title:
{title}

Content:
{content}
"""


import re

def clean_json(text: str):

    text = text.strip()

    match = re.search(r"\{[\s\S]*\}", text)

    if match:
        return match.group(0)

    return text


def predict(title, content):

    prompt = PROMPT.format(
        title=str(title),
        content=str(content)[:4000]
    )

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    text = response.choices[0].message.content

    print("\n========== MODEL RESPONSE ==========")
    print(text)
    print("====================================\n")

    text = clean_json(text)

    try:
        result = json.loads(text)

        if not isinstance(result, dict):
            raise ValueError("Model did not return JSON object.")
        
        label = str(result.get("label", "Neutral")).strip().title()

        if label not in ["Positive", "Neutral", "Negative"]:
            label = "Neutral"
        
        reason = str(result.get("reason", "")).strip()

        return label, reason

    except Exception as e:
      print("\n===== JSON ERROR =====")
      print(text)
      print("======================")
      raise


def main():

    os.makedirs("ml/datasets/labeled", exist_ok=True)

    df = pd.read_csv(INPUT_FILE)

    labels = []
    reasons = []

    total = len(df)

    for i, row in df.iterrows():

        print(f"\n[{i+1}/{total}] {row['title']}")

        while True:

            try:

                label, reason = predict(
                    row["title"],
                    row["content"]
                )

                print(f"Label : {label}")

                labels.append(label)
                reasons.append(reason)

                break

            except Exception as e:

              print(e)

              retryable_errors = (
                "429",
                "500",
                "502",
                "503",
                "504",
                "Rate limit",
                "timeout",
            )

            if any(err.lower() in str(e).lower() for err in retryable_errors):
                print("Retrying in 5 seconds...")
                time.sleep(5)
                continue

            raise

        temp = df.iloc[:len(labels)].copy()
        temp["label"] = labels
        temp["reason"] = reasons

        temp.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        time.sleep(1)

    print("\nFinished!")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()