import unittest

from models.article import Article
from services.crawler_service import is_topic_related
from services.topic_verification_service import verify_article_topic


def article(title, content):
    return Article(
        title=title,
        url="https://example.com/article",
        source="Example",
        category="Technology",
        published_date="2026-08-21",
        content=content,
    )


class TopicVerificationServiceTests(unittest.TestCase):
    def test_explicit_cybersecurity_title_is_verified(self):
        result = verify_article_topic(article(
            "Serangan Siber Membobol Sistem Perusahaan",
            "Perusahaan sedang memulihkan layanan.",
        ))

        self.assertTrue(result.is_related)
        self.assertIn("serangan siber", result.matched_keywords)
        self.assertIn("title", result.reason)

    def test_short_acronyms_do_not_match_inside_ordinary_words(self):
        result = verify_article_topic(article(
            "Model open source baru diluncurkan",
            "Perusahaan mengumumkannya secara diam-diam kepada publik.",
        ))

        self.assertFalse(result.is_related)
        self.assertNotIn("rce", result.matched_keywords)
        self.assertNotIn("iam", result.matched_keywords)

    def test_ambiguous_soc_does_not_verify_a_chip_article(self):
        result = verify_article_topic(article(
            "Ponsel baru menggunakan SoC tercepat",
            "System-on-chip tersebut meningkatkan performa perangkat.",
        ))

        self.assertFalse(result.is_related)
        self.assertIn("soc", result.matched_keywords)
        self.assertIn("ambiguous", result.reason)

    def test_generic_digital_infrastructure_is_supporting_only(self):
        result = verify_article_topic(article(
            "Ekspansi pusat data baru",
            "Infrastruktur digital diperluas untuk memenuhi kebutuhan bisnis. " * 5,
        ))

        self.assertFalse(result.is_related)
        self.assertIn("infrastruktur digital", result.matched_keywords)

    def test_single_general_vulnerability_reference_is_rejected(self):
        result = verify_article_topic(article(
            "Program bantuan pangan diperbaiki",
            "Sistem distribusi memiliki satu kerentanan operasional.",
        ))

        self.assertFalse(result.is_related)
        self.assertIn("kerentanan", result.matched_keywords)

    def test_repeated_software_vulnerability_evidence_is_verified(self):
        result = verify_article_topic(article(
            "Apple merilis pembaruan iOS",
            (
                "Pembaruan perangkat lunak menutup kerentanan pada iPhone. "
                "Kerentanan tersebut dapat memengaruhi sistem operasi perangkat."
            ),
        ))

        self.assertTrue(result.is_related)
        self.assertIn("kerentanan", result.matched_keywords)
        self.assertIn("contextual", result.reason)

    def test_cybersecurity_term_outside_article_lead_is_ignored(self):
        result = verify_article_topic(article(
            "Harga energi diperbarui",
            ("Berita ekonomi dan energi. " * 150) + " ransomware",
        ))

        self.assertFalse(result.is_related)

    def test_crawler_boolean_wrapper_uses_verifier(self):
        self.assertTrue(is_topic_related(article(
            "Data pelanggan bocor akibat serangan phishing",
            "Pelaku mencuri kredensial pengguna.",
        )))


if __name__ == "__main__":
    unittest.main()
