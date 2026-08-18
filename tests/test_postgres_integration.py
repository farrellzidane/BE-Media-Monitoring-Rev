import os
import unittest

from datetime import date, datetime
from pathlib import Path

from infrastructure.postgresql_database import (
    close_database_pool,
    database_connection,
    initialize_database,
)
from migrate_sqlite_to_postgres import (
    DEFAULT_SQLITE_PATH,
    migrate,
    read_sqlite_articles,
)
from repositories.article_repository import article_repository


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "Set TEST_DATABASE_URL to a disposable PostgreSQL database.",
)
class PostgreSQLIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = TEST_DATABASE_URL
        close_database_pool()
        initialize_database()

    @classmethod
    def tearDownClass(cls):
        close_database_pool()
        if cls.original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = cls.original_database_url

    def setUp(self):
        article_repository.clear()

    @staticmethod
    def record(title="Rupiah Menguat", url="https://example.com/rupiah"):
        return (
            title,
            url,
            "Media Satu",
            "Business",
            "2026-07-20",
            "2026-07-20 12:30:45",
            "Isi berita ekonomi yang lengkap.",
            "Neutral",
            1.0,
        )

    def test_schema_save_upsert_filters_and_date_contract(self):
        article_repository.save([self.record()])

        with database_connection() as connection:
            published_date, crawl_date = connection.execute(
                "SELECT published_date, crawl_date FROM articles"
            ).fetchone()
        self.assertIsInstance(published_date, date)
        self.assertNotIsInstance(published_date, datetime)
        self.assertIsInstance(crawl_date, datetime)

        article = article_repository.get_all()[0]
        self.assertEqual(article[3], "2026-07-20")
        self.assertEqual(article[4], "2026-07-20 12:30:45")
        self.assertEqual(len(article_repository.search("rupiah")), 1)
        self.assertEqual(len(article_repository.get_by_source("media satu")), 1)
        self.assertEqual(len(article_repository.get_by_category("business")), 1)
        self.assertEqual(len(article_repository.get_by_date("2026-07-20")), 1)

        article_repository.save([
            self.record(title="Rupiah Kembali Menguat")
        ])
        articles = article_repository.get_all()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0][0], "Rupiah Kembali Menguat")

    def test_connection_context_rolls_back_on_error(self):
        with self.assertRaisesRegex(RuntimeError, "force rollback"):
            with database_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO articles (title, url)
                    VALUES (%s, %s)
                    """,
                    ("Temporary", "https://example.com/temporary"),
                )
                raise RuntimeError("force rollback")

        self.assertEqual(article_repository.get_all(), [])

    def test_current_sqlite_database_migrates_all_78_articles(self):
        if not Path(DEFAULT_SQLITE_PATH).is_file():
            self.skipTest("The ignored local SQLite database is unavailable.")

        result = migrate(DEFAULT_SQLITE_PATH)

        self.assertEqual(result, {"rows": 78, "unique_urls": 78})
        self.assertEqual(len(article_repository.get_all()), 78)

        source_rows, _ = read_sqlite_articles(DEFAULT_SQLITE_PATH)
        source_ids = [row[0] for row in source_rows]
        with database_connection() as connection:
            target_ids = [
                row[0]
                for row in connection.execute(
                    "SELECT id FROM articles ORDER BY id"
                ).fetchall()
            ]
        self.assertEqual(target_ids, source_ids)

        article_repository.save([
            self.record(
                title="Artikel setelah migrasi",
                url="https://example.com/after-migration",
            )
        ])
        with database_connection() as connection:
            next_id = connection.execute(
                "SELECT id FROM articles WHERE url = %s",
                ("https://example.com/after-migration",),
            ).fetchone()[0]
        self.assertEqual(next_id, max(source_ids) + 1)


if __name__ == "__main__":
    unittest.main()
