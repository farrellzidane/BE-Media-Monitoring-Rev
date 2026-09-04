from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FILE = PROJECT_ROOT / "ml/datasets/cybersecurity/labeled.csv"
OUTPUT_DIR = PROJECT_ROOT / "ml/datasets/cybersecurity"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Cybersecurity labeled dataset not found: {INPUT_FILE}. "
        "Run auto_labeler.py first."
    )

# ==========================
# Load Dataset
# ==========================

df = pd.read_csv(INPUT_FILE)

required_columns = {"title", "content", "category", "label"}
missing_columns = required_columns - set(df.columns)
if missing_columns:
    raise ValueError(
        f"Missing required columns: {sorted(missing_columns)}"
    )

cybersecurity_terms = (
    "cyber", "siber", "ransomware", "malware", "phishing", "hacker",
    "hacking", "data breach", "data leak", "kebocoran data", "peretasan",
    "kerentanan", "exploit", "ddos", "keamanan jaringan",
)
cybersecurity_categories = {
    "cybersecurity", "cyber security", "cybersec",
    "malware & ransomware", "phishing & social engineering",
    "data breach & leak", "hacking & cyber crime",
    "vulnerability & exploit", "ddos & network attack",
    "cyber espionage & warfare", "security technology & defense",
    "policy & regulation", "general cybersecurity",
}
article_text = (
    df["title"].fillna("").astype(str) + " " +
    df["content"].fillna("").astype(str)
).str.lower()
is_cybersecurity = article_text.apply(
    lambda text: any(term in text for term in cybersecurity_terms)
)
is_cybersecurity |= df["category"].fillna("").astype(str).str.strip().str.lower().isin(
    cybersecurity_categories
)
df = df[is_cybersecurity].copy()
if df.empty:
    raise ValueError("No cybersecurity articles found in the labeled dataset")

df["label"] = df["label"].astype(str).str.strip().str.title()
df = df[df["label"].isin({"Negative", "Neutral", "Positive"})].copy()
df["dedupe_key"] = (
    df["title"].fillna("").astype(str).str.strip().str.lower()
    + "|"
    + df["content"].fillna("").astype(str).str.strip().str.lower()
)
df = df.drop_duplicates(subset=["dedupe_key"]).drop(columns=["dedupe_key"])

# ==========================
# Combine title + content
# ==========================

df["text"] = (
    df["title"].fillna("") +
    ". " +
    df["content"].fillna("")
)

# ==========================
# Label Encoding
# ==========================

label_map = {
    "Negative": 0,
    "Neutral": 1,
    "Positive": 2
}

df["label_id"] = df["label"].map(label_map)

# Keep only required columns
df = df[["text", "label", "label_id"]]

# ==========================
# Train / Validation Split
# ==========================

train_df, remainder_df = train_test_split(
    df,
    test_size=0.3,
    random_state=42,
    shuffle=True,
    stratify=df["label"]
)
valid_df, test_df = train_test_split(
    remainder_df,
    test_size=0.5,
    random_state=42,
    shuffle=True,
    stratify=remainder_df["label"],
)

# ==========================
# Save
# ==========================

train_df.to_csv(
    OUTPUT_DIR / "train.csv",
    index=False,
    encoding="utf-8-sig"
)

valid_df.to_csv(
    OUTPUT_DIR / "valid.csv",
    index=False,
    encoding="utf-8-sig"
)

test_df.to_csv(
    OUTPUT_DIR / "test.csv",
    index=False,
    encoding="utf-8-sig"
)

print("=" * 60)
print("Dataset Preparation Finished")
print("=" * 60)

print(f"Total Data      : {len(df)}")
print(f"Training Data   : {len(train_df)}")
print(f"Validation Data : {len(valid_df)}")
print(f"Test Data       : {len(test_df)}")

print("\nTraining Label Distribution")
print(train_df["label"].value_counts())

print("\nValidation Label Distribution")
print(valid_df["label"].value_counts())

print("\nTest Label Distribution")
print(test_df["label"].value_counts())

print("\nSaved:")
print(OUTPUT_DIR / "train.csv")
print(OUTPUT_DIR / "valid.csv")
print(OUTPUT_DIR / "test.csv")