import unittest

from datetime import datetime

from config.settings import DATA_QUALITY_DIMENSIONS, DATA_QUALITY_RULES
from services.data_quality_service import (
    get_data_quality_report,
    get_data_quality_rule_evidence,
)


class FakeArticleRepository:
    def __init__(self, articles):
        self.articles = articles

    def get_all(self):
        return self.articles


def article(
    title="Judul unik",
    source="Media Satu",
    category="General Cybersecurity",
    published_date="2026-07-20",
    crawl_date="2026-07-20 11:00:00",
    url="https://example.com/article",
    content=None,
):
    return (
        title,
        source,
        category,
        published_date,
        crawl_date,
        url,
        content or (f"{title} " + "isi artikel yang lengkap dan relevan " * 8),
    )


class DataQualityServiceTests(unittest.TestCase):
    now = datetime(2026, 7, 20, 12, 0, 0)

    def report(self, articles):
        return get_data_quality_report(
            repository=FakeArticleRepository(articles),
            now=self.now,
        )

    def evidence(self, articles, rule_key, result_filter="all", limit=25, offset=0):
        return get_data_quality_rule_evidence(
            repository=FakeArticleRepository(articles),
            rule_key=rule_key,
            result_filter=result_filter,
            limit=limit,
            offset=offset,
            now=self.now,
        )

    @staticmethod
    def rules_by_key(report):
        return {rule["key"]: rule for rule in report["rules"]}

    def test_configured_weights_total_one_hundred(self):
        self.assertEqual(sum(rule["weight"] for rule in DATA_QUALITY_RULES.values()), 100)
        self.assertEqual(sum(dimension["weight"] for dimension in DATA_QUALITY_DIMENSIONS.values()), 100)
        for dimension_key, dimension in DATA_QUALITY_DIMENSIONS.items():
            self.assertEqual(
                sum(
                    rule["weight"]
                    for rule in DATA_QUALITY_RULES.values()
                    if rule["dimension"] == dimension_key
                ),
                dimension["weight"],
            )

    def test_clean_articles_receive_a_perfect_explainable_score(self):
        report = self.report([
            article(),
            article(
                title="Judul kedua",
                url="https://example.com/article-2",
                content="konten kedua yang berbeda dan lengkap " * 8,
            ),
        ])

        self.assertEqual(report["quality_score"], 100.0)
        self.assertEqual(report["status"], "excellent")
        self.assertTrue(all(rule["failed"] == 0 for rule in report["rules"]))
        self.assertEqual(len(report["dimensions"]), 5)

    def test_score_is_normalized_by_record_count(self):
        articles = [
            article(
                title=f"Judul {index}",
                url=f"https://example.com/{index}",
                content=f"konten unik nomor {index} " + "isi lengkap " * 20,
            )
            for index in range(10)
        ]
        first = list(articles[0])
        first[0] = None
        articles[0] = tuple(first)

        report = self.report(articles)
        title_rule = self.rules_by_key(report)["title_present"]

        self.assertEqual(title_rule["score"], 90.0)
        self.assertEqual(title_rule["failed"], 1)
        self.assertEqual(report["quality_score"], 99.0)

    def test_normalized_duplicate_headlines_are_detected(self):
        report = self.report([
            article(title="IHSG Naik Hari Ini!", url="https://example.com/1"),
            article(
                title="ihsg naik hari ini",
                url="https://example.com/2",
                content="konten artikel kedua yang berbeda " * 10,
            ),
        ])
        rule = self.rules_by_key(report)["headline_unique"]

        self.assertEqual(rule["applicable"], 2)
        self.assertEqual(rule["failed"], 1)
        self.assertEqual(rule["score"], 50.0)
        self.assertEqual(report["duplicate_titles"], 1)

    def test_tracking_parameters_do_not_hide_duplicate_urls(self):
        report = self.report([
            article(url="https://www.example.com/news/?utm_source=social"),
            article(
                title="Judul kedua",
                url="https://example.com/news#section",
                content="konten artikel kedua yang berbeda " * 10,
            ),
        ])
        rule = self.rules_by_key(report)["url_unique"]

        self.assertEqual(rule["failed"], 1)
        self.assertEqual(rule["score"], 50.0)

    def test_missing_invalid_and_nonstandard_values_are_reported_separately(self):
        report = self.report([
            article(
                title=None,
                category="kategori-bebas",
                published_date="not-a-date",
                url="not-a-url",
            ),
            article(
                title="Tanggal hilang",
                published_date=None,
                url="https://example.com/valid",
                content="konten valid yang cukup panjang " * 10,
            ),
        ])
        rules = self.rules_by_key(report)

        self.assertEqual(rules["title_present"]["failed"], 1)
        self.assertEqual(rules["publication_date_present"]["failed"], 1)
        self.assertEqual(rules["publication_date_valid"]["failed"], 1)
        self.assertEqual(rules["url_valid"]["failed"], 1)
        self.assertEqual(rules["category_standardized"]["failed"], 1)

    def test_source_freshness_uses_current_time_and_has_independent_status(self):
        report = self.report([
            article(
                published_date="2026-07-19",
                crawl_date="2026-07-20 05:00:00",
            ),
        ])
        source = report["sources"][0]
        freshness_rule = self.rules_by_key(report)["source_crawl_fresh"]

        self.assertEqual(source["status"], "critical")
        self.assertEqual(source["crawl_age_minutes"], 420.0)
        self.assertEqual(freshness_rule["failed"], 1)

    def test_empty_dataset_is_not_reported_as_perfect(self):
        report = self.report([])

        self.assertEqual(report["quality_score"], 0.0)
        self.assertEqual(report["status"], "critical")
        self.assertEqual(report["rules"], [])

    def test_evidence_counts_match_every_report_rule(self):
        articles = [
            article(),
            article(
                title="JUDUL UNIK!",
                category="kategori-bebas",
                published_date="2026-07-18",
                crawl_date="2026-07-20 11:00:00",
                url="https://www.example.com/article/?utm_source=test",
            ),
            article(
                title="Artikel ketiga",
                source="Media Lambat",
                published_date=None,
                crawl_date="2026-07-20 05:00:00",
                url="invalid-url",
                content="pendek",
            ),
        ]
        report = self.report(articles)

        for rule in report["rules"]:
            with self.subTest(rule=rule["key"]):
                evidence = self.evidence(articles, rule["key"])
                self.assertEqual(evidence["total"], rule["applicable"])
                self.assertEqual(evidence["rule"]["passed"], rule["passed"])
                self.assertEqual(evidence["rule"]["failed"], rule["failed"])
                self.assertEqual(evidence["rule"]["score"], rule["score"])

    def test_evidence_supports_result_filter_and_pagination(self):
        articles = [
            article(title=f"Judul {index}", url=f"https://example.com/{index}")
            for index in range(5)
        ]
        broken = list(articles[3])
        broken[0] = None
        articles[3] = tuple(broken)

        failed = self.evidence(articles, "title_present", result_filter="failed")
        page = self.evidence(articles, "title_present", limit=2, offset=2)

        self.assertEqual(failed["filtered_total"], 1)
        self.assertEqual(failed["evidence"][0]["result"], "failed")
        self.assertEqual(page["filtered_total"], 5)
        self.assertEqual(len(page["evidence"]), 2)
        self.assertEqual(page["offset"], 2)

    def test_source_freshness_evidence_is_source_level(self):
        evidence = self.evidence([
            article(crawl_date="2026-07-20 05:00:00"),
        ], "source_crawl_fresh")

        self.assertEqual(evidence["total"], 1)
        self.assertEqual(evidence["evidence"][0]["entity_type"], "source")
        self.assertEqual(evidence["evidence"][0]["result"], "failed")

    def test_unknown_evidence_rule_is_rejected(self):
        with self.assertRaises(ValueError):
            self.evidence([article()], "unknown_rule")


if __name__ == "__main__":
    unittest.main()
