import sqlite3
import pandas as pd

import os
print("DB PATH:", os.path.abspath("data/articles.db"))

conn = sqlite3.connect("data/articles.db")

query = """
SELECT
    title,
    source,
    category,
    published_date
FROM articles
ORDER BY published_date DESC
"""

df = pd.read_sql_query(query, conn)

conn.close()

print(df.head())
print()
print("Total articles:", len(df))

df.to_csv(
    "ml/datasets/news_headlines.csv",
    index=False
)

print("Exported to ml/datasets/news_headlines.csv")