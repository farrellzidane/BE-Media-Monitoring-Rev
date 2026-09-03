import unittest

from services.analytics_service import (
    get_articles_with_sentiment,
    get_daily_volume,
    get_sentiment_by_category,
    get_sentiment_by_source,
    get_sentiment_trend,
    get_top_keywords,
)


class FakeRepository:
    def __init__(self, articles):
        self._articles = articles

    def get_all(self):
        return self._articles


class AnalyticsServiceTests(unittest.TestCase):
    def test_analytics_helpers_build_expected_summary_payloads(self):
        articles = [
            (
                "Phishing campaign hits bank",
                "Kompas",
                "General Cybersecurity",
                "2026-07-20",
                "2026-07-20 08:00:00",
                "https://example.com/a",
                "Phishing campaign targeted customer accounts in a major attack.",
                "Positive",
                0.9,
                "Strong detection",
            ),
            (
                "Data leak exposes customer records",
                "Detik",
                "General Cybersecurity",
                "2026-07-20",
                "2026-07-20 09:00:00",
                "https://example.com/b",
                "Sensitive customer records were leaked after an exposed database.",
                "Negative",
                0.8,
                "Security breach",
            ),
            (
                "Patch released for critical vulnerability",
                "Kompas",
                "General Cybersecurity",
                "2026-07-19",
                "2026-07-19 10:00:00",
                "https://example.com/c",
                "A patch was released after a critical zero-day vulnerability report.",
                "Positive",
                0.75,
                "Patch available",
            ),
        ]

        repository = FakeRepository(articles)

        enriched = get_articles_with_sentiment(repository)
        self.assertEqual(len(enriched), 3)
        self.assertEqual(enriched[0]["sentiment"], "Positive")

        self.assertEqual(get_daily_volume(repository)["2026-07-20"], 2)
        self.assertEqual(get_sentiment_by_category(repository, enriched)["General Cybersecurity"]["positive"], 2)
        self.assertEqual(get_sentiment_by_source(repository, enriched)["Kompas"]["positive"], 2)
        self.assertEqual(get_sentiment_trend(repository, enriched)["2026-07-20"]["positive"], 1)
        self.assertTrue(get_top_keywords(5, repository))


if __name__ == "__main__":
    unittest.main()
