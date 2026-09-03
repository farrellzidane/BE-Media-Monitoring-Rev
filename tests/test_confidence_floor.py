import unittest

from services.analytics_service import get_articles_with_sentiment
from services.sentiment_service import analyze_sentiment


class FakeRepository:
    def __init__(self, articles):
        self._articles = articles

    def get_all(self):
        return self._articles


class RealConfidenceTests(unittest.TestCase):
    def test_analyze_sentiment_returns_model_confidence_in_valid_range(self):
        response = analyze_sentiment("Cybersecurity breach triggered major incident response.")
        self.assertIn(response["label"], {"Positive", "Neutral", "Negative"})
        self.assertGreaterEqual(response["confidence"], 0.0)
        self.assertLessEqual(response["confidence"], 1.0)

    def test_analytics_keeps_original_confidence_values_when_present(self):
        repository = FakeRepository([
            (
                "Security incident",
                "Kompas",
                "General Cybersecurity",
                "2026-08-31",
                "2026-08-31 10:00:00",
                "https://example.com/incident",
                "A ransomware attack disrupted systems.",
                "Negative",
                0.87,
                "Observed confidence",
            )
        ])

        enriched = get_articles_with_sentiment(repository)
        self.assertEqual(len(enriched), 1)
        self.assertAlmostEqual(enriched[0]["confidence"], 0.87)



if __name__ == "__main__":
    unittest.main()
