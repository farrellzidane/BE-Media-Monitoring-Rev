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


def load_data():
    cols = ["text", "label"]

    train = pd.read_csv(
        "ml/datasets/smsa/train_preprocess.tsv",
        sep="\t",
        header=None,
        names=cols
    )

    valid = pd.read_csv(
        "ml/datasets/smsa/valid_preprocess.tsv",
        sep="\t",
        header=None,
        
        names=cols
    )

    label_map = {
        "negative": 0,
        "neutral": 1,
        "positive": 2
    }

    train["label"] = train["label"].map(label_map)
    valid["label"] = valid["label"].map(label_map)

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


training_args = TrainingArguments(
    output_dir="./ml/models/sentiment_model",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_steps=100
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=valid_dataset,
    compute_metrics=compute_metrics
)

trainer.train()

trainer.save_model("./ml/models/sentiment_model")
tokenizer.save_pretrained("./ml/models/sentiment_model")