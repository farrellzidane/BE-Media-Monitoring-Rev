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
# LABEL MAPPING
# ======================================

LABEL_MAP = {
    "Negative": 0,
    "Neutral": 1,
    "Positive": 2
}

ID2LABEL = {
    0: "Negative",
    1: "Neutral",
    2: "Positive"
}


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

print("\nTraining Label Distribution:")
print(train_df["label"].value_counts())

print("\nValidation Label Distribution:")
print(valid_df["label"].value_counts())


# ======================================
# CALCULATE CLASS WEIGHTS
# ======================================

class_counts = (
    train_df["label_id"]
    .value_counts()
    .reindex(range(NUM_LABELS), fill_value=0)
)

print("\n" + "=" * 60)
print("CLASS WEIGHTS")
print("=" * 60)

print("Class counts:")
print(class_counts)

# Inverse-frequency weighting.
# Negative has very few examples, so it receives a larger weight.
total_samples = len(train_df)

class_weights = []

for class_id in range(NUM_LABELS):

    count = class_counts[class_id]

    if count == 0:
        weight = 1.0
    else:
        weight = total_samples / (NUM_LABELS * count)

    class_weights.append(weight)

class_weights = torch.tensor(
    class_weights,
    dtype=torch.float
)

print("\nRaw class weights:")
for i, weight in enumerate(class_weights):
    print(
        f"{ID2LABEL[i]:<10}: {weight.item():.4f}"
    )

# Prevent the extremely small Negative class
# from receiving an excessively large weight.
class_weights = torch.clamp(
    class_weights,
    max=5.0
)

print("\nFinal class weights:")
for i, weight in enumerate(class_weights):
    print(
        f"{ID2LABEL[i]:<10}: {weight.item():.4f}"
    )


# ======================================
# CONVERT TO HF DATASET
# ======================================

train_dataset = Dataset.from_pandas(train_df)
valid_dataset = Dataset.from_pandas(valid_df)


# ======================================
# TOKENIZER
# ======================================

print("\nLoading Tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME
)

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
    num_labels=NUM_LABELS,
    id2label=ID2LABEL,
    label2id=LABEL_MAP
)

print("Model Loaded!")


# ======================================
# METRICS
# ======================================

def compute_metrics(eval_pred):

    logits, labels = eval_pred

    predictions = np.argmax(
        logits,
        axis=-1
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="macro",
            zero_division=0
        )
    )

    weighted_precision, weighted_recall, weighted_f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="weighted",
            zero_division=0
        )
    )

    accuracy = accuracy_score(
        labels,
        predictions
    )

    return {
        "accuracy": accuracy,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": f1,
        "weighted_precision": weighted_precision,
        "weighted_recall": weighted_recall,
        "weighted_f1": weighted_f1
    }


# ======================================
# WEIGHTED TRAINER
# ======================================

class WeightedTrainer(Trainer):

    def compute_loss(
        self,
        model,
        inputs,
        return_outputs=False,
        num_items_in_batch=None
    ):

        labels = inputs.pop("labels")

        outputs = model(**inputs)

        logits = outputs.logits

        weights = class_weights.to(
            logits.device
        )

        loss_function = torch.nn.CrossEntropyLoss(
            weight=weights
        )

        loss = loss_function(
            logits,
            labels
        )

        if return_outputs:
            return loss, outputs

        return loss


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

    metric_for_best_model="macro_f1",
    greater_is_better=True,

    report_to="none",

    seed=SEED
)


# ======================================
# TRAINER
# ======================================

trainer = WeightedTrainer(

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
# FINAL EVALUATION
# ======================================

print("\n" + "=" * 60)
print("FINAL EVALUATION")
print("=" * 60)

metrics = trainer.evaluate()

print("\nFinal Metrics:")

for key, value in metrics.items():

    if isinstance(value, float):

        print(
            f"{key:<25}: {value:.4f}"
        )

    else:

        print(
            f"{key:<25}: {value}"
        )


# ======================================
# SAVE MODEL
# ======================================

trainer.save_model(
    OUTPUT_DIR
)

tokenizer.save_pretrained(
    OUTPUT_DIR
)


# ======================================
# FINISHED
# ======================================

print("\n" + "=" * 60)
print("TRAINING FINISHED")
print("=" * 60)

print(
    f"Model saved to : {OUTPUT_DIR}"
)
