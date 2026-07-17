"""Compatibility facade for existing backend scripts.

New code should use the repository and infrastructure layers directly.
"""

from infrastructure.sqlite_database import (
    DATABASE_FILE,
    initialize_database,
)
from repositories.article_repository import article_repository
from services.article_service import normalize_category


def create_database():
    initialize_database()


def clear_articles():
    before, after = article_repository.clear()
    print(f"Before delete: {before}")
    print(f"After delete: {after}")


def save_articles_to_database(articles):
    records = [
        (
            article.title,
            article.url,
            article.source,
            normalize_category(article.category),
            article.published_date,
            article.crawl_date,
            article.content,
        )
        for article in articles
    ]

    article_repository.save(records)
    print()
    print(f"Saved to {DATABASE_FILE}")


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
