"""Compatibility facade for existing backend scripts.

New code should use the repository and infrastructure layers directly.
"""

from infrastructure.postgresql_database import (
    close_database_pool,
    initialize_database,
)
from repositories.article_repository import article_repository
from services.article_service import categorize_cybersecurity_topic
from services.sentiment_reason_service import (
    generate_confidence_reason,
    generate_sentiment_reason,
)
from services.sentiment_service import analyze_sentiment


def create_database():
    initialize_database()


def close_database():
    close_database_pool()


def clear_articles():
    before, after = article_repository.clear()
    print(f"Before delete: {before}")
    print(f"After delete: {after}")


def save_articles_to_database(articles):
    records = []

    for article in articles:
        sentiment = analyze_sentiment(
            f"{article.title}\n\n{article.content or ''}"
        )

        records.append(
            (
                article.title,
                article.url,
                article.source,
                categorize_cybersecurity_topic(article.title, article.content),
                article.published_date,
                article.crawl_date,
                article.content,
                sentiment["label"],
                sentiment["confidence"],
                generate_sentiment_reason(
                    article.title, article.content, sentiment["label"]
                ),
                generate_confidence_reason(
                    sentiment["label"],
                    sentiment["confidence"],
                    sentiment.get("scores"),
                ),
                (sentiment.get("scores") or {}).get("Negative"),
                (sentiment.get("scores") or {}).get("Neutral"),
                (sentiment.get("scores") or {}).get("Positive"),
            )
        )

    article_repository.save(records)
    print()
    print("Saved to PostgreSQL database")


def search_articles(keyword):
    return article_repository.search(keyword)


def get_all_articles():
    return article_repository.get_all()


def get_articles_by_source(source):
    return article_repository.get_by_source(source)


def get_articles_by_category(category):
    return article_repository.get_by_category(category)


def get_articles_by_date(date):
    return article_repository.get_by_date(date)
