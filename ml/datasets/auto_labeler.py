import os
import json
import time
import re

import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI


# ======================================
# ENVIRONMENT
# ======================================

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "OPENROUTER_API_KEY is not set in .env"
    )


# ======================================
# OPENROUTER CLIENT
# ======================================

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)


# ======================================
# CONFIGURATION
# ======================================

MODEL = "qwen/qwen3.5-35b-a3b"

INPUT_FILE = "ml/datasets/raw/financial_news.csv"

OUTPUT_FILE = (
    "ml/datasets/labeled/financial_news_labeled.csv"
)


# ======================================
# PROMPT
# ======================================

PROMPT = """
You are a professional financial sentiment analyst.

Your task is to classify the FINANCIAL SENTIMENT of the article.

Analyze BOTH:

1. The title
2. The full content

Choose EXACTLY ONE label:

Positive
Neutral
Negative


========================
IMPORTANT CLASSIFICATION RULE
========================

Classify the article based on its OVERALL FINANCIAL IMPACT.

Do NOT classify an article as Neutral merely because it is reporting facts.

If the article contains a clear financial development that is beneficial or harmful to a company, investor, market, consumer, or the economy, classify it as Positive or Negative.


========================
POSITIVE
========================

Choose Positive when the overall financial implication is beneficial.

Examples include:

- Revenue increases
- Profit increases
- Earnings beat expectations
- Business growth
- Business expansion
- Successful investment
- Successful fundraising
- New partnership that benefits the business
- Stock price increases
- IHSG increases
- Currency strengthens
- Credit rating upgrade
- Increased exports
- Increased investment
- Economic growth
- Strong financial outlook
- Improved liquidity
- Higher production
- Successful IPO
- Successful debt issuance
- Government policy that clearly supports business or economic growth


========================
NEGATIVE
========================

Choose Negative when the overall financial implication is harmful, risky, or deteriorating.

Examples include:

- Revenue decreases
- Profit decreases
- Losses
- Earnings miss expectations
- Layoffs caused by financial problems
- Bankruptcy
- Default
- Debt problems
- Credit rating downgrade
- Lawsuit with financial consequences
- Corruption with financial consequences
- Stock price decreases
- IHSG decreases
- Currency weakens significantly
- Inflation that negatively affects purchasing power or businesses
- Rising prices that negatively affect consumers or businesses
- Oil price spikes that create economic or business pressure
- Geopolitical conflict that negatively affects markets
- Economic slowdown
- Weak financial outlook
- Liquidity problems
- Declining production
- Failed IPO
- Failed investment
- Financial uncertainty
- Supply disruption that creates financial damage


========================
MIXED ARTICLES
========================

Some articles contain BOTH positive and negative information.

Do NOT automatically choose Neutral.

Instead, determine the DOMINANT financial impact.

Examples:

1. A company reports higher profit but also higher debt.
   Choose Positive if the overall financial result is clearly strong.

2. A company reports higher revenue but suffers major losses.
   Choose Negative if the overall financial result is harmful.

3. Stock price rises despite some negative background information.
   Choose Positive if the market impact is clearly positive.

4. An article discusses a policy and explains both benefits and risks.
   Choose the label representing the dominant expected financial impact.


========================
NEUTRAL
========================

Choose Neutral ONLY when there is genuinely NO clear dominant positive or negative financial impact.

Examples:

- Purely informational explanations
- Definitions of financial terms
- General educational articles
- Schedules or announcements with no clear financial impact
- Profiles that contain no meaningful financial development
- Price information that does not indicate a meaningful positive or negative trend
- Reports that simply describe an event without financial consequences


========================
IMPORTANT DECISION RULES
========================

1. NEVER choose Neutral simply because the article is factual.

2. ALWAYS consider financial consequences.

3. If the article reports a clear increase or improvement in financial performance:
   Positive.

4. If the article reports a clear decrease, loss, risk, or deterioration:
   Negative.

5. If both Positive and Negative signals exist:
   Choose the DOMINANT overall financial impact.

6. If the article discusses market movement:

   - Market rises / strengthens -> Positive
   - Market falls / weakens -> Negative

7. If the article discusses a price increase:

   - Determine WHO is financially affected.
   - Higher selling prices benefiting producers -> potentially Positive.
   - Higher prices harming consumers/businesses -> potentially Negative.
   - If there is no clear financial implication -> Neutral.

8. Do NOT use Neutral as a safe fallback.

9. Every article MUST receive exactly one of:

   Positive
   Neutral
   Negative.


========================
OUTPUT FORMAT
========================

Return ONLY valid JSON.

The JSON must contain exactly these fields:

label
reason

Example:

{
    "label": "Positive",
    "reason": "The company reported higher revenue and stronger profit, indicating improved financial performance."
}

Another example:

{
    "label": "Negative",
    "reason": "The company reported declining revenue and significant losses, indicating deteriorating financial performance."
}

Another example:

{
    "label": "Neutral",
    "reason": "The article provides general financial information without a clear dominant positive or negative financial impact."
}


========================
ARTICLE
========================

Title:
{title}

Content:
{content}
"""


# ======================================
# CLEAN JSON
# ======================================

def clean_json(text: str):

    text = text.strip()

    match = re.search(
        r"\{[\s\S]*\}",
        text
    )

    if match:
        return match.group(0)

    return text


# ======================================
# PREDICT
# ======================================

def predict(title, content):

    prompt = PROMPT.replace(
    "{title}",
    str(title)
).replace(
    "{content}",
    str(content)[:4000]
)

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={
            "type": "json_object"
        },
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
            raise ValueError(
                "Model did not return JSON object."
            )

        label = str(
            result.get(
                "label",
                "Neutral"
            )
        ).strip().title()

        if label not in [
            "Positive",
            "Neutral",
            "Negative"
        ]:
            label = "Neutral"

        reason = str(
            result.get(
                "reason",
                ""
            )
        ).strip()

        return label, reason

    except Exception:

        print("\n===== JSON ERROR =====")
        print(text)
        print("======================")

        raise


# ======================================
# MAIN
# ======================================

def main():

    os.makedirs(
        "ml/datasets/labeled",
        exist_ok=True
    )

    df = pd.read_csv(
        INPUT_FILE
    )

    labels = []
    reasons = []

    total = len(df)

    for i, row in df.iterrows():

        print(
            f"\n[{i + 1}/{total}] {row['title']}"
        )

        while True:

            try:

                label, reason = predict(
                    row["title"],
                    row["content"]
                )

                print(
                    f"Label : {label}"
                )

                labels.append(label)
                reasons.append(reason)

                break

            except Exception as e:

                error_text = str(e)

                print(
                    f"Error: {error_text}"
                )

                retryable_errors = (
                    "429",
                    "500",
                    "502",
                    "503",
                    "504",
                    "Rate limit",
                    "timeout",
                )

                if any(
                    err.lower() in error_text.lower()
                    for err in retryable_errors
                ):

                    print(
                        "Retrying in 5 seconds..."
                    )

                    time.sleep(5)

                    continue

                raise

        temp = df.iloc[
            :len(labels)
        ].copy()

        temp["label"] = labels
        temp["reason"] = reasons

        temp.to_csv(
            OUTPUT_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        time.sleep(1)

    print("\nFinished!")

    print(
        f"Saved to {OUTPUT_FILE}"
    )


# ======================================
# ENTRY POINT
# ======================================

if __name__ == "__main__":
    main()