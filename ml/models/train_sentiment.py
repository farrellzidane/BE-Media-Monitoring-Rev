# ======================================
# IMPORT
# ======================================

import os
import numpy as np
import pandas as pd

from datasets import Dataset

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support
)

# ======================================
# CONFIGURATION
# ======================================

MODEL_NAME = "indobenchmark/indobert-base-p2"

TRAIN_FILE = "ml/datasets/processed/train.csv"
VALID_FILE = "ml/datasets/processed/valid.csv"

OUTPUT_DIR = "ml/models/saved_model"

NUM_LABELS = 3
MAX_LENGTH = 256
BATCH_SIZE = 8
LEARNING_RATE = 2e-5
NUM_EPOCHS = 5

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================================
# LOAD DATASET
# ======================================

train_df = pd.read_csv(TRAIN_FILE)
valid_df = pd.read_csv(VALID_FILE)

print("=" * 60)
print("DATASET INFORMATION")
print("=" * 60)
print(f"Training Data   : {len(train_df)}")
print(f"Validation Data : {len(valid_df)}")

# ======================================
# CONVERT TO HF DATASET
# ======================================

train_dataset = Dataset.from_pandas(train_df)
valid_dataset = Dataset.from_pandas(valid_df)

# ======================================
# TOKENIZER
# ======================================

print("\nLoading Tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

print("Tokenizer Loaded!")

# ======================================
# TOKENIZATION
# ======================================

def tokenize_function(examples):
    return tokenizer(
        examples["text"],
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH
    )

train_dataset = train_dataset.map(
    tokenize_function,
    batched=True
)

valid_dataset = valid_dataset.map(
    tokenize_function,
    batched=True
)

# ======================================
# PREPARE DATASET
# ======================================

train_dataset = train_dataset.rename_column("label_id", "labels")
valid_dataset = valid_dataset.rename_column("label_id", "labels")

train_dataset.set_format(
    type="torch",
    columns=[
        "input_ids",
        "attention_mask",
        "labels"
    ]
)

valid_dataset.set_format(
    type="torch",
    columns=[
        "input_ids",
        "attention_mask",
        "labels"
    ]
)

# ======================================
# LOAD MODEL
# ======================================

print("\nLoading Model...")

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=NUM_LABELS
)

print("Model Loaded!")

# ======================================
# METRICS
# ======================================

def compute_metrics(eval_pred):

    logits, labels = eval_pred

    predictions = np.argmax(logits, axis=-1)

    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="weighted",
        zero_division=0
    )

    accuracy = accuracy_score(labels, predictions)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

# ======================================
# TRAINING ARGUMENTS
# ======================================

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,

    eval_strategy="epoch",
    save_strategy="epoch",

    learning_rate=LEARNING_RATE,

    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,

    num_train_epochs=NUM_EPOCHS,

    weight_decay=0.01,

    logging_steps=5,

    load_best_model_at_end=True,

    metric_for_best_model="f1",

    greater_is_better=True,

    report_to="none"
)

# ======================================
# TRAINER
# ======================================
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=valid_dataset,
    compute_metrics=compute_metrics
)

# ======================================
# TRAIN
# ======================================

print("\nStarting Training...\n")

trainer.train()

# ======================================
# EVALUATE
# ======================================

print("\nEvaluating...\n")

metrics = trainer.evaluate()

print(metrics)

# ======================================
# SAVE MODEL
# ======================================

trainer.save_model(OUTPUT_DIR)

tokenizer.save_pretrained(OUTPUT_DIR)

print("\n===================================")
print("Training Finished!")
print("Model saved to:")
print(OUTPUT_DIR)
print("===================================")