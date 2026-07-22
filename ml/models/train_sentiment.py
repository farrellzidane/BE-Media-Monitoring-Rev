# ======================================
# IMPORT
# ======================================

import os
import random
import numpy as np
import pandas as pd
import torch

from datasets import Dataset

from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding
)

from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support
)

# ======================================
# CONFIGURATION
# ======================================

MODEL_NAME = "indobenchmark/indobert-base-p1"

TRAIN_FILE = "ml/datasets/processed/train.csv"
VALID_FILE = "ml/datasets/processed/valid.csv"

OUTPUT_DIR = "ml/models/saved_model"

NUM_LABELS = 3
MAX_LENGTH = 256
BATCH_SIZE = 4
LEARNING_RATE = 2e-5
NUM_EPOCHS = 3
SEED = 42

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ======================================
# RANDOM SEED
# ======================================

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

# ======================================
# DEVICE
# ======================================

device = "cuda" if torch.cuda.is_available() else "cpu"

print("=" * 60)
print("DEVICE")
print("=" * 60)
print(device)

if device == "cuda":
    print(torch.cuda.get_device_name(0))

# ======================================
# LOAD DATASET
# ======================================

train_df = pd.read_csv(TRAIN_FILE)
valid_df = pd.read_csv(VALID_FILE)

print("\n" + "=" * 60)
print("DATASET")
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

data_collator = DataCollatorWithPadding(
    tokenizer=tokenizer
)

print("Tokenizer Loaded!")

# ======================================
# TOKENIZATION
# ======================================

def tokenize_function(examples):

    return tokenizer(
        examples["text"],
        truncation=True,
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

train_dataset = train_dataset.rename_column(
    "label_id",
    "labels"
)

valid_dataset = valid_dataset.rename_column(
    "label_id",
    "labels"
)

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

    accuracy = accuracy_score(
        labels,
        predictions
    )

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

    save_total_limit=1,

    learning_rate=LEARNING_RATE,

    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,

    num_train_epochs=NUM_EPOCHS,

    weight_decay=0.01,

    logging_steps=5,

    load_best_model_at_end=True,

    metric_for_best_model="f1",
    greater_is_better=True,

    report_to="none",

    seed=SEED
)

# ======================================
# TRAINER
# ======================================

trainer = Trainer(

    model=model,

    args=training_args,

    train_dataset=train_dataset,
    eval_dataset=valid_dataset,

    data_collator=data_collator,

    compute_metrics=compute_metrics
)

# ======================================
# TRAIN
# ======================================

print("\n" + "=" * 60)
print("START TRAINING")
print("=" * 60)

trainer.train()

# ======================================
# EVALUATE
# ======================================

print("\n" + "=" * 60)
print("FINAL EVALUATION")
print("=" * 60)

metrics = trainer.evaluate()

print(metrics)

# ======================================
# SAVE MODEL
# ======================================

trainer.save_model(OUTPUT_DIR)

tokenizer.save_pretrained(OUTPUT_DIR)

print("\n" + "=" * 60)
print("TRAINING FINISHED")
print("=" * 60)
print(f"Model saved to : {OUTPUT_DIR}")