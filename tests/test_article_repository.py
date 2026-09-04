import unittest

from contextlib import contextmanager
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import repositories.article_repository as repository_module
from repositories.article_repository import ArticleRepository


@contextmanager
def connection_context(connection):
    yield connection


class ArticleRepositoryTests(unittest.TestCase):
    def test_save_uses_postgresql_upsert_and_placeholders(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        records = [
            (
                "Title",
                "https://example.com/article",
                "Source",
                "General Cybersecurity",
                "2026-07-20",
                "2026-07-20 12:00:00",
                "Content",
                "Neutral",
                1.0,
                "Reason",
                "Confidence reason",
                0.1,
                0.2,
                0.7,
            )
        ]

        with patch.object(
            repository_module,
            "database_connection",
            return_value=connection_context(connection),
        ):
            ArticleRepository().save(records)

        query, parameters = cursor.executemany.call_args.args
        self.assertIn("ON CONFLICT (url) DO UPDATE", query)
        self.assertIn(
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            query,
        )
        self.assertNotIn("?", query)
        self.assertEqual(parameters, records)

    def test_fetch_normalizes_native_postgresql_dates(self):
        connection = MagicMock()
        connection.execute.return_value.fetchall.return_value = [
            (
                "Title",
                "Source",
                "General Cybersecurity",
                date(2026, 7, 20),
                datetime(2026, 7, 20, 12, 30, 45, 123456),
                "https://example.com/article",
                "Content",
                "Neutral",
                1.0,
                "Reason",
            )
        ]

        with patch.object(
            repository_module,
            "database_connection",
            return_value=connection_context(connection),
        ):
            articles = ArticleRepository().get_all()

        self.assertEqual(articles[0][3], "2026-07-20")
        self.assertEqual(articles[0][4], "2026-07-20 12:30:45")

    def test_search_uses_case_insensitive_postgresql_matching(self):
        connection = MagicMock()
        connection.execute.return_value.fetchall.return_value = []

        with patch.object(
            repository_module,
            "database_connection",
            return_value=connection_context(connection),
        ):
            ArticleRepository().search("Rupiah")

        query, parameters = connection.execute.call_args.args
        self.assertIn("title ILIKE %s", query)
        self.assertIn("content ILIKE %s", query)
        self.assertEqual(parameters, ("%Rupiah%", "%Rupiah%"))


if __name__ == "__main__":
    unittest.main()
