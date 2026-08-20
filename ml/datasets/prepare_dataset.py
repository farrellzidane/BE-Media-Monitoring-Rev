import os
import pandas as pd
from sklearn.model_selection import train_test_split

INPUT_FILE = "ml/datasets/labeled/cybersecurity_news_labeled.csv"
OUTPUT_DIR = "ml/datasets/processed"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==========================
# Load Dataset
# ==========================

df = pd.read_csv(INPUT_FILE)

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

train_df, valid_df = train_test_split(
    df,
    test_size=0.2,
    random_state=42,
    shuffle=True,
    stratify=df["label"]
)

# ==========================
# Save
# ==========================

train_df.to_csv(
    f"{OUTPUT_DIR}/train.csv",
    index=False,
    encoding="utf-8-sig"
)

valid_df.to_csv(
    f"{OUTPUT_DIR}/valid.csv",
    index=False,
    encoding="utf-8-sig"
)

print("=" * 60)
print("Dataset Preparation Finished")
print("=" * 60)

print(f"Total Data      : {len(df)}")
print(f"Training Data   : {len(train_df)}")
print(f"Validation Data : {len(valid_df)}")

print("\nTraining Label Distribution")
print(train_df["label"].value_counts())

print("\nValidation Label Distribution")
print(valid_df["label"].value_counts())

print("\nSaved:")
print(f"{OUTPUT_DIR}/train.csv")
print(f"{OUTPUT_DIR}/valid.csv")