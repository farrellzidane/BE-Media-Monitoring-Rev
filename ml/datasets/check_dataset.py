import pandas as pd

FILE = "ml/datasets/labeled/cybersecurity_news_labeled.csv"

df = pd.read_csv(FILE)

print("=" * 60)
print("DATASET INFORMATION")
print("=" * 60)

print(f"Rows    : {len(df)}")
print(f"Columns : {len(df.columns)}")

print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values")
print(df.isnull().sum())

print("\nDuplicate rows")
print(df.duplicated().sum())

print("\nLabel distribution")
print(df["label"].value_counts())

print("\nFirst 5 rows")
print(df.head())