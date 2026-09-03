from pathlib import Path

import numpy as np
import pandas as pd
from datasets import Dataset
from sklearn.model_selection import train_test_split
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

import evaluate

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "ml/datasets/cybersecurity/labeled.csv"
OUTPUT_DIR = PROJECT_ROOT / "ml/models/saved_model_cybersecurity"
MODEL_NAME = "indobenchmark/indobert-base-p1"


def load_dataset():
    df = pd.read_csv(DATA_PATH)
    df = df.dropna(subset=["label"]).copy()
    df["text"] = (
        df["title"].fillna("").astype(str).str.strip()
        + " "
        + df["content"].fillna("").astype(str).str.strip()
    ).str.strip()

    label_map = {"Negative": 0, "Neutral": 1, "Positive": 2}
    df["label_id"] = df["label"].map(label_map)
    df = df[df["label_id"].notna()].copy()

    if df.empty:
        raise ValueError(f"No valid labeled rows found in {DATA_PATH}")

    train_df, valid_df = train_test_split(
        df[["text", "label_id"]],
        test_size=0.25,
        random_state=42,
        stratify=df["label_id"],
    )

    return train_df.reset_index(drop=True), valid_df.reset_index(drop=True)


def tokenize_function(tokenizer):
    def _tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding="max_length",
            max_length=256,
        )

    return _tokenize


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    accuracy = evaluate.load("accuracy")
    f1 = evaluate.load("f1")
    return {
        **accuracy.compute(predictions=predictions, references=labels),
        **f1.compute(predictions=predictions, references=labels, average="macro"),
    }


def main():
    train_df, valid_df = load_dataset()

    train_dataset = Dataset.from_pandas(train_df.rename(columns={"label_id": "labels"}))
    valid_dataset = Dataset.from_pandas(valid_df.rename(columns={"label_id": "labels"}))

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_dataset = train_dataset.map(tokenize_function(tokenizer), batched=True)
    valid_dataset = valid_dataset.map(tokenize_function(tokenizer), batched=True)

    train_dataset = train_dataset.remove_columns(["text"])
    valid_dataset = valid_dataset.remove_columns(["text"])

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=3,
        id2label={0: "Negative", 1: "Neutral", 2: "Positive"},
        label2id={"Negative": 0, "Neutral": 1, "Positive": 2},
    )

    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=8,
        weight_decay=0.01,
        logging_steps=5,
        save_total_limit=2,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        compute_metrics=compute_metrics,
    )

    trainer.train()
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))

    metrics = trainer.evaluate()
    print("EVAL_METRICS:")
    print(metrics)


if __name__ == "__main__":
    main()
