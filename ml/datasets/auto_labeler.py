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

INPUT_FILE = "ml/datasets/raw/cybersecurity_news.csv"

OUTPUT_FILE = (
    "ml/datasets/labeled/cybersecurity_news_labeled.csv"
)


# ======================================
# PROMPT
# ======================================

PROMPT = """
You are a professional cybersecurity sentiment analyst covering Indonesian media.

Your task is to classify the CYBERSECURITY SENTIMENT of the article.

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

Classify the article based on its OVERALL IMPACT ON CYBERSECURITY / DIGITAL SAFETY
for the affected organization, users, government, or the public.

Do NOT classify an article as Neutral merely because it is reporting facts.

If the article contains a clear development that is beneficial or harmful to
digital security, data protection, or the affected organization/public, classify
it as Positive or Negative.


========================
POSITIVE
========================

Choose Positive when the overall security implication is beneficial.

Examples include:

- A vulnerability is discovered and successfully patched/fixed
- An attack, breach, or intrusion attempt is successfully blocked or prevented
- Law enforcement arrests hackers, or takes down a ransomware/malware group
- A company/agency strengthens its security systems or passes a security audit
- New security regulation, standard, or policy that improves data protection
- Successful recovery from an incident with no lasting harm
- Security researchers responsibly disclose a flaw before it is exploited
- Increased cybersecurity awareness, training, or investment that reduces risk
- A platform improves user privacy or data protection features
- Stolen data or systems are successfully recovered


========================
NEGATIVE
========================

Choose Negative when the overall security implication is harmful, risky, or damaging.

Examples include:

- Data breach or leak (kebocoran data)
- Hacking, defacement, or unauthorized access (peretasan)
- Ransomware, malware, or phishing attack (serangan siber)
- DDoS attack causing service disruption
- Vulnerability discovered but left unpatched / actively exploited
- Personal, financial, or government data exposed or sold
- Identity theft or fraud enabled by a security failure
- Critical infrastructure, government, or financial systems compromised
- Security negligence, misconfiguration, or cover-up by an organization
- Financial or reputational loss caused by a cyber incident
- New/emerging cyber threat, exploit, or attack technique with no mitigation yet


========================
MIXED ARTICLES
========================

Some articles contain BOTH positive and negative information.

Do NOT automatically choose Neutral.

Instead, determine the DOMINANT security impact.

Examples:

1. A company is breached but responds quickly, patches the flaw, and no data
   is confirmed stolen. Choose Negative if the breach itself is the dominant
   event, or Positive if the response fully neutralized the harm before any
   real damage occurred.

2. A vulnerability is disclosed together with a patch already available.
   Choose Positive if the patch is what makes the article newsworthy, Negative
   if active exploitation in the wild is still emphasized.

3. Hackers are arrested after a long-running attack campaign.
   Choose Positive, since the dominant news is the successful law-enforcement
   outcome, even though the underlying attack was harmful.

4. An article discusses a new regulation and explains both its protections
   and its compliance burden. Choose the label representing the dominant
   expected impact on digital security/data protection.


========================
NEUTRAL
========================

Choose Neutral ONLY when there is genuinely NO clear dominant positive or
negative security impact.

Examples:

- Purely informational explanations of cybersecurity concepts or terms
- General educational articles or how-to/tips content
- Schedules, conference announcements, or product launches with no clear
  security consequence
- Profiles or interviews that contain no meaningful security development
- Statistics or reports that simply describe a trend without a clear
  beneficial or harmful outcome
- Opinion pieces that merely discuss the topic without reporting an event


========================
IMPORTANT DECISION RULES
========================

1. NEVER choose Neutral simply because the article is factual.

2. ALWAYS consider the consequences for digital security, data protection,
   or the affected organization/public.

3. If the article reports a clear improvement, fix, prevention, or successful
   defense/law-enforcement action:
   Positive.

4. If the article reports a clear attack, breach, leak, exploit, or
   deterioration in security:
   Negative.

5. If both Positive and Negative signals exist:
   Choose the DOMINANT overall security impact.

6. If the article discusses a vulnerability:

   - Disclosed with a fix/patch already applied, and that is the focus -> Positive
   - Actively exploited or left unpatched -> Negative
   - Merely described with no clear consequence yet -> Neutral

7. If the article discusses an attacker/threat actor:

   - Caught, blocked, or dismantled -> Positive
   - Successful or ongoing attack, still at large -> Negative

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
    "reason": "The vulnerability was disclosed and patched before it could be exploited, indicating an improvement in security."
}

Another example:

{
    "label": "Negative",
    "reason": "The company suffered a data breach exposing customer information, indicating a serious security failure."
}

Another example:

{
    "label": "Neutral",
    "reason": "The article provides general educational information about cybersecurity without a clear dominant positive or negative security impact."
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