from pathlib import Path

import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
import numpy as np
import evaluate


MODEL_NAME = "indobenchmark/indobert-base-p1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "ml/models/saved_model"


def load_data():
    train = pd.read_csv(PROJECT_ROOT / "ml/datasets/processed/train.csv")
    valid = pd.read_csv(PROJECT_ROOT / "ml/datasets/processed/valid.csv")

    required_columns = {"text", "label"}
    for split_name, split in (("train", train), ("valid", valid)):
        missing_columns = required_columns - set(split.columns)
        if missing_columns:
            raise ValueError(
                f"{split_name} dataset is missing columns: {sorted(missing_columns)}"
            )

    label_map = {
        "negative": 0,
        "neutral": 1,
        "positive": 2
    }

    train["label"] = train["label"].astype(str).str.strip().str.lower().map(label_map)
    valid["label"] = valid["label"].astype(str).str.strip().str.lower().map(label_map)

    train = train.dropna(subset=["text", "label"])[["text", "label"]]
    valid = valid.dropna(subset=["text", "label"])[["text", "label"]]

    return train, valid


train_df, valid_df = load_data()

train_dataset = Dataset.from_pandas(train_df)
valid_dataset = Dataset.from_pandas(valid_df)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=128
    )


train_dataset = train_dataset.map(tokenize, batched=True)
valid_dataset = valid_dataset.map(tokenize, batched=True)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=3
)

accuracy_metric = evaluate.load("accuracy")


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return accuracy_metric.compute(
        predictions=predictions,
        references=labels
    )


def main():
    training_args = TrainingArguments(
        output_dir=str(OUTPUT_DIR),
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="accuracy",
        greater_is_better=True,
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        logging_steps=100,
        report_to=[]
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=valid_dataset,
        compute_metrics=compute_metrics
    )

    trainer.train()
    trainer.save_model(str(OUTPUT_DIR))
    tokenizer.save_pretrained(str(OUTPUT_DIR))


if __name__ == "__main__":
    main()