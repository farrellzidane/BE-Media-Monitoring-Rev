import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.sentiment_service import analyze_sentiment
from services.sentiment_reason_service import generate_confidence_reason, generate_sentiment_reason

from infrastructure.postgresql_database import database_connection


def rescore_articles():
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT id, title, content FROM articles WHERE sentiment_override IS NOT TRUE"
        ).fetchall()

        for article_id, title, content in rows:
            result = analyze_sentiment(
                f"{title}\n\n{content or ''}"
            )
            connection.execute(
                """
                UPDATE articles
                SET sentiment = %s,
                    sentiment_confidence = %s,
                    sentiment_reason = %s,
                    confidence_reason = %s,
                    sentiment_score_negative = %s,
                    sentiment_score_neutral = %s,
                    sentiment_score_positive = %s
                WHERE id = %s
                """,
                (
                    result["label"],
                    result["confidence"],
                    generate_sentiment_reason(title, content, result["label"]),
                    generate_confidence_reason(result["label"], result["confidence"], result.get("scores")),
                    (result.get("scores") or {}).get("Negative"),
                    (result.get("scores") or {}).get("Neutral"),
                    (result.get("scores") or {}).get("Positive"),
                    article_id,
                ),
            )

    print(f"Rescored {len(rows)} articles")


if __name__ == "__main__":
    rescore_articles()