"""Compatibility facade for existing backend scripts.

New code should use the repository and infrastructure layers directly.
"""

from infrastructure.postgresql_database import (
    close_database_pool,
    initialize_database,
)
from repositories.article_repository import article_repository
from services.article_service import normalize_category
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
                normalize_category(article.category),
                article.published_date,
                article.crawl_date,
                article.content,
                sentiment["label"],
                sentiment["confidence"],
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
