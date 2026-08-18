from datetime import date, datetime

from infrastructure.postgresql_database import database_connection


ARTICLE_SELECT = """
    SELECT
        title,
        source,
        category,
        published_date,
        crawl_date,
        url,
        content,
        sentiment,
        sentiment_confidence
    FROM articles
"""


class ArticleRepository:
    def save(self, records):
        """Persists articles. Each record must include a precomputed
        (sentiment, sentiment_confidence) pair so the API never has to run
        the sentiment model on the request path."""
        with database_connection() as connection:
            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO articles (
                        title,
                        url,
                        source,
                        category,
                        published_date,
                        crawl_date,
                        content,
                        sentiment,
                        sentiment_confidence
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE SET
                        title = EXCLUDED.title,
                        source = EXCLUDED.source,
                        category = EXCLUDED.category,
                        published_date = EXCLUDED.published_date,
                        crawl_date = EXCLUDED.crawl_date,
                        content = EXCLUDED.content,
                        sentiment = EXCLUDED.sentiment,
                        sentiment_confidence = EXCLUDED.sentiment_confidence
                    """,
                    records,
                )

    def clear(self):
        with database_connection() as connection:
            before = connection.execute(
                "SELECT COUNT(*) FROM articles"
            ).fetchone()[0]

            connection.execute("DELETE FROM articles")

            after = connection.execute(
                "SELECT COUNT(*) FROM articles"
            ).fetchone()[0]

        return before, after

    def get_all(self):
        return self._fetch_all(
            f"{ARTICLE_SELECT} ORDER BY published_date DESC"
        )

    def search(self, keyword):
        pattern = f"%{keyword}%"
        return self._fetch_all(
            f"""
            {ARTICLE_SELECT}
            WHERE
                title ILIKE %s
                OR content ILIKE %s
            ORDER BY published_date DESC
            """,
            (pattern, pattern),
        )

    def get_by_source(self, source):
        return self._fetch_all(
            f"""
            {ARTICLE_SELECT}
            WHERE LOWER(source) = LOWER(%s)
            ORDER BY published_date DESC
            """,
            (source,),
        )

    def get_by_category(self, category):
        return self._fetch_all(
            f"""
            {ARTICLE_SELECT}
            WHERE LOWER(category) = LOWER(%s)
            ORDER BY published_date DESC
            """,
            (category,),
        )

    def get_by_date(self, date):
        return self._fetch_all(
            f"""
            {ARTICLE_SELECT}
            WHERE published_date = %s
            ORDER BY published_date DESC
            """,
            (date,),
        )

    @staticmethod
    def _fetch_all(query, parameters=()):
        with database_connection() as connection:
            rows = connection.execute(
                query,
                parameters,
            ).fetchall()
        return [_serialize_article(row) for row in rows]


def _serialize_article(row):
    article = list(row)
    article[3] = _serialize_date(article[3])
    article[4] = _serialize_datetime(article[4])
    return tuple(article)


def _serialize_date(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def _serialize_datetime(value):
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="seconds")
    return value


article_repository = ArticleRepository()


def get_all_articles():
    """Convenience function used by existing analytics services."""
    return article_repository.get_all()
