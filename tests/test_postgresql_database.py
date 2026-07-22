import os
import unittest

from unittest.mock import MagicMock, patch

import infrastructure.postgresql_database as database


class PostgreSQLDatabaseTests(unittest.TestCase):
    def setUp(self):
        database._database_pool = None

    def tearDown(self):
        database.close_database_pool()

    def test_database_url_is_required(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL is required"):
                database.open_database_pool()

    def test_pool_is_opened_once_and_closed(self):
        pool = MagicMock()
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://user:password@localhost/database",
                "DATABASE_POOL_MIN_SIZE": "2",
                "DATABASE_POOL_MAX_SIZE": "5",
            },
            clear=True,
        ), patch.object(database, "ConnectionPool", return_value=pool) as pool_class:
            first = database.open_database_pool()
            second = database.open_database_pool()

        self.assertIs(first, pool)
        self.assertIs(second, pool)
        pool_class.assert_called_once_with(
            conninfo="postgresql://user:password@localhost/database",
            min_size=2,
            max_size=5,
            open=False,
        )
        pool.open.assert_called_once_with(wait=True)

        database.close_database_pool()
        pool.close.assert_called_once_with()
        self.assertIsNone(database._database_pool)

    def test_failed_pool_open_is_cleaned_up(self):
        pool = MagicMock()
        pool.open.side_effect = RuntimeError("connection failed")
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "postgresql://user:password@localhost/database"},
            clear=True,
        ), patch.object(database, "ConnectionPool", return_value=pool):
            with self.assertRaisesRegex(RuntimeError, "connection failed"):
                database.open_database_pool()

        pool.close.assert_called_once_with()
        self.assertIsNone(database._database_pool)

    def test_invalid_pool_size_is_rejected(self):
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": "postgresql://user:password@localhost/database",
                "DATABASE_POOL_MIN_SIZE": "5",
                "DATABASE_POOL_MAX_SIZE": "2",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "Invalid database pool size"):
                database.open_database_pool()


if __name__ == "__main__":
    unittest.main()
