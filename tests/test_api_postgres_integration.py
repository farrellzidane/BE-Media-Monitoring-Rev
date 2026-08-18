import os
import sys
import types
import unittest


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

if TEST_DATABASE_URL:
    fake_sentiment = types.ModuleType("services.sentiment_service")
    fake_sentiment.analyze_sentiment = lambda _text: {
        "label": "Neutral",
        "confidence": 1.0,
        "scores": {
            "Negative": 0.0,
            "Neutral": 1.0,
            "Positive": 0.0,
        },
    }
    original_sentiment = sys.modules.get("services.sentiment_service")
    sys.modules["services.sentiment_service"] = fake_sentiment
    try:
        from fastapi.testclient import TestClient

        from api import app
        from infrastructure.postgresql_database import close_database_pool
        from repositories.article_repository import article_repository
    finally:
        if original_sentiment is None:
            sys.modules.pop("services.sentiment_service", None)
        else:
            sys.modules["services.sentiment_service"] = original_sentiment


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "Set TEST_DATABASE_URL to a disposable PostgreSQL database.",
)
class PostgreSQLAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_database_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = TEST_DATABASE_URL
        close_database_pool()

    @classmethod
    def tearDownClass(cls):
        close_database_pool()
        if cls.original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = cls.original_database_url

    def test_read_endpoints_keep_the_existing_json_contract(self):
        with TestClient(app) as client:
            article_repository.clear()
            article_repository.save([
                (
                    "Rupiah Menguat",
                    "https://example.com/rupiah",
                    "Media Satu",
                    "Business",
                    "2026-07-22",
                    "2026-07-22 10:01:53",
                    "Isi artikel ekonomi yang cukup panjang. " * 10,
                    "Neutral",
                    1.0,
                )
            ])

            health = client.get("/health")
            articles = client.get("/articles")
            analytics = client.get("/analytics")
            evidence = client.get(
                "/data-quality/rules/title_present/evidence"
            )

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {"status": "ok"})

        self.assertEqual(articles.status_code, 200)
        self.assertEqual(articles.json()[0]["published_date"], "2026-07-22")
        self.assertEqual(articles.json()[0]["crawl_date"], "2026-07-22 10:01:53")

        self.assertEqual(analytics.status_code, 200)
        self.assertIn("quality", analytics.json())
        self.assertIn("articles", analytics.json())

        self.assertEqual(evidence.status_code, 200)
        self.assertEqual(evidence.json()["rule"]["key"], "title_present")


if __name__ == "__main__":
    unittest.main()
