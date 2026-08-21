import csv
import json
import re

from dataclasses import asdict
from functools import lru_cache

from repositories.article_repository import get_all_articles
from services.sentiment_service import analyze_sentiment


# Cybersecurity subtopics, keyed by the keywords whose presence in an
# article's title/lead identifies that subtopic. Only used for articles that
# have already passed topic_verification_service's cybersecurity check, so
# every article gets a subtopic and "General Cybersecurity" is the catch-all
# for ones that don't match a more specific bucket.
CYBERSECURITY_TAXONOMY = {
    "Malware & Ransomware": (
        "malware", "ransomware", "spyware", "trojan", "worm", "keylogger",
        "rootkit", "cryptojacking", "virus komputer",
    ),
    "Phishing & Social Engineering": (
        "phishing", "spear phishing", "smishing", "vishing",
        "social engineering", "penipuan digital", "penipuan online",
        "online scam", "scam", "credential theft", "credential stealing",
        "password attack", "brute force", "brute-force",
        "account takeover", "identity theft", "pencurian identitas",
    ),
    "Data Breach & Leak": (
        "data breach", "data breaches", "data leak", "data leakage",
        "kebocoran data", "bocor data", "pencurian data", "database breach",
        "stolen data", "exposed data", "data exposure", "data theft",
    ),
    "Hacking & Cyber Crime": (
        "hacker", "hackers", "hacking", "hacked", "diretas", "meretas",
        "peretasan", "peretas", "dibobol", "membobol", "cybercriminal",
        "cybercriminals", "cyber criminal", "cyber criminals",
        "kejahatan siber", "cybercrime", "pelaku peretasan",
        "kelompok hacker",
    ),
    "Vulnerability & Exploit": (
        "vulnerability", "vulnerabilities", "kerentanan", "security flaw",
        "security flaws", "zero day", "zero-day", "exploit", "exploitation",
        "remote code execution", "rce", "privilege escalation",
        "command injection", "sql injection", "cross site scripting", "xss",
        "buffer overflow", "security patch", "patch keamanan",
        "celah keamanan",
    ),
    "DDoS & Network Attack": (
        "ddos", "denial of service", "distributed denial of service",
        "network security", "serangan jaringan", "keamanan jaringan",
    ),
    "Cyber Espionage & Warfare": (
        "cyber espionage", "spionase siber", "cyberwar", "cyber warfare",
        "advanced persistent threat", "apt group", "nation-state",
    ),
    "Security Technology & Defense": (
        "firewall", "endpoint security", "endpoint protection", "antivirus",
        "anti-virus", "security operation center",
        "security operations center", "soc", "siem", "zero trust",
        "multi factor authentication", "multifactor authentication",
        "multi-factor authentication", "mfa", "two factor authentication",
        "two-factor authentication", "2fa", "encryption", "enkripsi",
        "decryption", "identity access management", "iam",
        "access control", "threat detection", "intrusion detection",
        "intrusion prevention",
    ),
    "Policy & Regulation": (
        "badan siber dan sandi negara", "bssn", "cybersecurity agency",
        "regulasi keamanan", "undang-undang perlindungan data",
        "perlindungan data pribadi", "uu pdp", "kominfo", "compliance",
        "kebijakan keamanan", "security advisory",
    ),
}

CYBERSECURITY_CATEGORIES = tuple(CYBERSECURITY_TAXONOMY) + ("General Cybersecurity",)

ARTICLE_LEAD_LENGTH = 3000


@lru_cache(maxsize=None)
def _keyword_pattern(term):
    phrase = r"\s+".join(re.escape(part) for part in term.split())
    return re.compile(rf"(?<!\w){phrase}(?!\w)", re.IGNORECASE)


def categorize_cybersecurity_topic(title, content):
    """Classify a (pre-verified) cybersecurity article into a subtopic,
    based on keyword evidence in the title and lead content. Title matches
    are weighted higher than lead matches. Falls back to the catch-all
    bucket when no subtopic keyword is present."""

    title = title or ""
    lead = (content or "")[:ARTICLE_LEAD_LENGTH]

    best_category = None
    best_score = 0

    for category, keywords in CYBERSECURITY_TAXONOMY.items():
        score = 0

        for keyword in keywords:
            pattern = _keyword_pattern(keyword)

            if pattern.search(title):
                score += 3

            if pattern.search(lead):
                score += 1

        if score > best_score:
            best_score = score
            best_category = category

    return best_category or "General Cybersecurity"


def remove_duplicates(articles):
    unique_articles = []
    seen_urls = set()

    for article in articles:

        if article.url in seen_urls:
            continue

        seen_urls.add(article.url)

        article.category = categorize_cybersecurity_topic(
            article.title, article.content
        )

        unique_articles.append(article)

    return unique_articles


def print_statistics(articles):
    source_counts = {}
    category_counts = {}

    for article in articles:

        source_counts[article.source] = (
            source_counts.get(
                article.source,
                0
            ) + 1
        )

        category = categorize_cybersecurity_topic(
            article.title, article.content
        )

        category_counts[category] = (
            category_counts.get(
                category,
                0
            ) + 1
        )

    print()
    print("=" * 40)
    print("SOURCE STATISTICS")
    print("=" * 40)

    for source, count in sorted(
        source_counts.items()
    ):
        print(
            f"{source:<15} : {count}"
        )

    print(
        f"Total Articles  : {len(articles)}"
    )

    print("=" * 40)

    print()
    print("=" * 40)
    print("CATEGORY STATISTICS")
    print("=" * 40)

    for category, count in sorted(
        category_counts.items()
    ):
        print(
            f"{category:<15} : {count}"
        )

    print("=" * 40)


def save_articles(
    articles,
    file_path
):
    article_data = []

    for article in articles:

        data = asdict(article)

        data["category"] = (
            categorize_cybersecurity_topic(
                article.title, article.content
            )
        )

        article_data.append(data)

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            article_data,
            file,
            ensure_ascii=False,
            indent=4
        )

    print()
    print(
        f"Saved to {file_path}"
    )


def save_articles_csv(
    articles,
    file_path
):
    with open(
        file_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "title",
            "url",
            "source",
            "category",
            "published_date",
            "content"
        ])

        for article in articles:

            writer.writerow([
                article.title,
                article.url,
                article.source,
                categorize_cybersecurity_topic(
                    article.title, article.content
                ),
                article.published_date,
                article.content
            ])

    print()
    print(
        f"Saved to {file_path}"
    )


from services.sentiment_service import (
    analyze_sentiment
)

def get_sentiment_by_source():

    articles = get_all_articles()

    source_stats = {}

    for article in articles:

        # article tuple:
        # 0 = title
        # 1 = source
        # 2 = category
        # 3 = published_date
        # 4 = crawl_date
        # 5 = url
        # 6 = content

        title = article[0]
        source = article[1]
        content = article[6] or ""

        # Gunakan format yang sama seperti saat training:
        # title + content
        text = f"{title}. {content}"

        result = analyze_sentiment(text)

        sentiment = result["label"]

        if source not in source_stats:
            source_stats[source] = {
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }

        if sentiment == "Positive":
            source_stats[source]["positive"] += 1

        elif sentiment == "Negative":
            source_stats[source]["negative"] += 1

        else:
            source_stats[source]["neutral"] += 1

    return source_stats