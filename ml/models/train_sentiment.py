from pathlib import Path

import numpy as np
import pandas as pd
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "ml/models/saved_model_cybersecurity_retrained"
MODEL_NAME = "indobenchmark/indobert-base-p1"


def load_dataset():
    label_map = {"Negative": 0, "Neutral": 1, "Positive": 2}

    def read_split(name):
        split = pd.read_csv(PROJECT_ROOT / f"ml/datasets/cybersecurity/{name}.csv")
        split["label_id"] = split["label"].map(label_map)
        split = split.dropna(subset=["text", "label_id"])[["text", "label_id"]]
        if split.empty:
            raise ValueError(f"No valid rows found in cybersecurity/{name}.csv")
        return split.reset_index(drop=True)

    return read_split("train"), read_split("valid")


def load_test_dataset():
    test_df = pd.read_csv(PROJECT_ROOT / "ml/datasets/cybersecurity/test.csv")
    test_df["label_id"] = test_df["label"].map({"Negative": 0, "Neutral": 1, "Positive": 2})
    test_df = test_df.dropna(subset=["text", "label_id"])[["text", "label_id"]]
    return test_df.reset_index(drop=True)


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
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, labels=[0, 1, 2], zero_division=0,
    )
    return {
        "accuracy": accuracy_score(labels, predictions),
        "macro_f1": f1_score(labels, predictions, average="macro", zero_division=0),
        "negative_f1": f1[0],
        "neutral_f1": f1[1],
        "positive_f1": f1[2],
        "macro_precision": float(precision.mean()),
        "macro_recall": float(recall.mean()),
    }


def main():
    train_df, valid_df = load_dataset()
    test_df = load_test_dataset()

    train_dataset = Dataset.from_pandas(train_df.rename(columns={"label_id": "labels"}))
    valid_dataset = Dataset.from_pandas(valid_df.rename(columns={"label_id": "labels"}))

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    train_dataset = train_dataset.map(tokenize_function(tokenizer), batched=True)
    valid_dataset = valid_dataset.map(tokenize_function(tokenizer), batched=True)
    test_dataset = Dataset.from_pandas(test_df.rename(columns={"label_id": "labels"}))
    test_dataset = test_dataset.map(tokenize_function(tokenizer), batched=True)

    train_dataset = train_dataset.remove_columns(["text"])
    valid_dataset = valid_dataset.remove_columns(["text"])
    test_dataset = test_dataset.remove_columns(["text"])

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
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=5,
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

    print("VALIDATION_METRICS:")
    print(trainer.evaluate())
    print("TEST_METRICS:")
    print(trainer.evaluate(eval_dataset=test_dataset, metric_key_prefix="test"))


if __name__ == "__main__":
    main()
