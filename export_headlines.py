import pandas as pd

from infrastructure.postgresql_database import close_database_pool
from repositories.article_repository import article_repository


try:
    articles = article_repository.get_all()
finally:
    close_database_pool()

df = pd.DataFrame(
    (article[:4] for article in articles),
    columns=["title", "source", "category", "published_date"],
)

print(df.head())
print()
print("Total articles:", len(df))

df.to_csv(
    "ml/datasets/news_headlines.csv",
    index=False
)

print("Exported to ml/datasets/news_headlines.csv")
