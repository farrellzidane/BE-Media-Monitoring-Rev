import pandas as pd

df = pd.read_csv("ml/datasets/labeled/financial_news_labeled.csv")

print(df["label"].value_counts())