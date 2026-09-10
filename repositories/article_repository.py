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
        sentiment_confidence,
        sentiment_reason,
        confidence_reason,
        sentiment_score_negative,
        sentiment_score_neutral,
        sentiment_score_positive,
        sentiment_override
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
                        sentiment_confidence,
                        sentiment_reason,
                        confidence_reason,
                        sentiment_score_negative,
                        sentiment_score_neutral,
                        sentiment_score_positive
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE SET
                        title = EXCLUDED.title,
                        source = EXCLUDED.source,
                        category = EXCLUDED.category,
                        published_date = EXCLUDED.published_date,
                        crawl_date = EXCLUDED.crawl_date,
                        content = EXCLUDED.content,
                        sentiment = CASE WHEN articles.sentiment_override THEN articles.sentiment ELSE EXCLUDED.sentiment END,
                        sentiment_confidence = CASE WHEN articles.sentiment_override THEN articles.sentiment_confidence ELSE EXCLUDED.sentiment_confidence END,
                        sentiment_reason = CASE WHEN articles.sentiment_override THEN articles.sentiment_reason ELSE EXCLUDED.sentiment_reason END,
                        confidence_reason = CASE WHEN articles.sentiment_override THEN articles.confidence_reason ELSE EXCLUDED.confidence_reason END,
                        sentiment_score_negative = EXCLUDED.sentiment_score_negative,
                        sentiment_score_neutral = EXCLUDED.sentiment_score_neutral,
                        sentiment_score_positive = EXCLUDED.sentiment_score_positive,
                        sentiment_override = articles.sentiment_override
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

    def update_sentiment(self, url, sentiment):
        with database_connection() as connection:
            row = connection.execute(
                """
                UPDATE articles
                SET sentiment = %s,
                    sentiment_confidence = 1.0,
                    sentiment_reason = 'Label diubah manual oleh pengguna.',
                    confidence_reason = 'Label manual pengguna.',
                    sentiment_score_negative = CASE WHEN %s = 'Negative' THEN 1.0 ELSE 0.0 END,
                    sentiment_score_neutral = CASE WHEN %s = 'Neutral' THEN 1.0 ELSE 0.0 END,
                    sentiment_score_positive = CASE WHEN %s = 'Positive' THEN 1.0 ELSE 0.0 END,
                    sentiment_override = TRUE
                WHERE url = %s
                RETURNING url
                """,
                (sentiment, sentiment, sentiment, sentiment, url),
            ).fetchone()
        return row is not None

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
