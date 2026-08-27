import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.models.predict import predict

from infrastructure.postgresql_database import database_connection


def rescore_articles():
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, content FROM articles"
        ).fetchall()

        for article_id, title, content in rows:
            result = predict(
                f"{title}\n\n{content or ''}"
            )
            connection.execute(
                """
                UPDATE articles
                SET sentiment = %s,
                    sentiment_confidence = %s
                WHERE id = %s
                """,
                (result["label"], result["confidence"], article_id),
            )

    print(f"Rescored {len(rows)} articles")


if __name__ == "__main__":
    rescore_articles()