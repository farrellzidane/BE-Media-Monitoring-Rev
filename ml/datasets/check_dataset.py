from pathlib import Path

import pandas as pd

FILE = Path(__file__).resolve().parent / "cybersecurity/labeled.csv"

df = pd.read_csv(FILE)

if "title" in df.columns and "content" in df.columns:
	cybersecurity_terms = (
		"cyber", "siber", "ransomware", "malware", "phishing", "hacker",
		"hacking", "data breach", "data leak", "kebocoran data", "peretasan",
		"kerentanan", "exploit", "ddos", "keamanan jaringan",
	)
	article_text = (
		df["title"].fillna("").astype(str) + " " +
		df["content"].fillna("").astype(str)
	).str.lower()
	non_cybersecurity = ~article_text.apply(
		lambda text: any(term in text for term in cybersecurity_terms)
	)
	print(f"Non-cybersecurity rows: {non_cybersecurity.sum()}")

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