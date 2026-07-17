from infrastructure.sqlite_database import database_connection


ARTICLE_SELECT = """
    SELECT
        title,
        source,
        category,
        published_date,
        crawl_date,
        url,
        content
    FROM articles
"""


class ArticleRepository:
    def save(self, records):
        with database_connection() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO articles (
                    title,
                    url,
                    source,
                    category,
                    published_date,
                    crawl_date,
                    content
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            connection.commit()

    def clear(self):
        with database_connection() as connection:
            before = connection.execute(
                "SELECT COUNT(*) FROM articles"
            ).fetchone()[0]

            connection.execute("DELETE FROM articles")
            connection.commit()

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
                LOWER(title) LIKE LOWER(?)
                OR LOWER(content) LIKE LOWER(?)
            ORDER BY published_date DESC
            """,
            (pattern, pattern),
        )

    def get_by_source(self, source):
        return self._fetch_all(
            f"""
            {ARTICLE_SELECT}
            WHERE LOWER(source) = LOWER(?)
            ORDER BY published_date DESC
            """,
            (source,),
        )

    def get_by_category(self, category):
        return self._fetch_all(
            f"""
            {ARTICLE_SELECT}
            WHERE LOWER(category) = LOWER(?)
            ORDER BY published_date DESC
            """,
            (category,),
        )

    def get_by_date(self, date):
        return self._fetch_all(
            f"""
            {ARTICLE_SELECT}
            WHERE published_date = ?
            ORDER BY published_date DESC
            """,
            (date,),
        )

    @staticmethod
    def _fetch_all(query, parameters=()):
        with database_connection() as connection:
            return connection.execute(
                query,
                parameters,
            ).fetchall()


article_repository = ArticleRepository()


def get_all_articles():
    """Convenience function used by existing analytics services."""
    return article_repository.get_all()
