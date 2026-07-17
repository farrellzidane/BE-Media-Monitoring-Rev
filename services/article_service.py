import csv
import json

from dataclasses import asdict

from repositories.article_repository import get_all_articles


def normalize_category(category):

    if not category:
        return "Unknown"

    category = category.lower().strip()

    mapping = {
        
        "news": "General",
        "berita": "General",
        "nasional": "General",
        "peristiwa": "General",
        "metropolitan": "General",
        "megapolitan": "General",
        "politik": "General",
        "arsip": "General",
        "adv": "General",
        "advertorial": "General",
        "epaper": "General",
        "photo": "General",
        "foto-news": "General",
        "foto-bisnis": "General",
        "video": "General",
        "kolom": "General",
        "tokoh": "General",
        "wawancara": "General",
        "prelude": "General",
        "adikarya-parlemen": "General",

        "economy": "Business",
        "market": "Business",
        "ekonomi": "Business",
        "ekbis": "Business",
        "money": "Business",
        "bisnis": "Business",
        "business": "Business",
        "consumer": "Business",
        "crypto": "Business",
        "saham": "Business",
        "energi": "Business",
        "moneter": "Business",
        "industri": "Business",
        "properti": "Business",
        "berita-ekonomi-bisnis": "Business",
        "ekonomi-hijau": "Business",
        "bursa-dan-valas": "Business",
        "finance": "Business",
        "fintech": "Business",
        "entrepreneur": "Business",
        "infrastruktur": "Business",

        "sport": "Sports",
        "sports": "Sports",
        "sportstars": "Sports",
        "olahraga": "Sports",
        "bola": "Sports",
        "sepakbola": "Sports",
        "superskor": "Sports",
        "superball": "Sports",
        "sport-lain": "Sports",
        "sportstyle": "Sports",
        "raket": "Sports",
        "moto-gp": "Sports",
        "olympic": "Sports",
        "piala-dunia": "Sports",
        "basket": "Sports",
        "bola-jatim": "Sports",

        "international": "International",
        "internasional": "International",
        "global": "International",

        "celebrity": "Entertainment",
        "showbiz": "Entertainment",
        "entertainment": "Entertainment",
        "hiburan": "Entertainment",
        "lifestyle": "Entertainment",
        "gaya-hidup": "Entertainment",
        "travel": "Entertainment",
        "food-travel": "Entertainment",
        "food": "Entertainment",
        "woman": "Entertainment",
        "mom": "Entertainment",
        "musik": "Entertainment",
        "seleb": "Entertainment",
        "persona": "Entertainment",
        "hype": "Entertainment",
        "ibu-dan-anak": "Entertainment",
        "tvscope": "Entertainment",
        "tren": "Entertainment",
        "teroka": "Entertainment",

        "tech": "Science",
        "tekno": "Science",
        "teknologi": "Science",
        "science": "Science",
        "tekno-sains": "Science",
        "cyberlife": "Science",
        "digital": "Science",
        "security": "Science",
        "review-produk": "Science",
        "fotoinet": "Science",
        "techno": "Science",
        "ototekno": "Science",
        "telco": "Science",
        "tips-dan-trik": "Science",
        "laptop-dan-pc": "Science",
        "info-sehat": "Science",
        "lingkungan": "Science",
        "sains": "Science",
        "research": "Science",

        "crime": "Law",
        "hukum": "Law",
        "kemenkumham": "Law",

        "regional": "Regional",
        "daerah": "Regional",

        "bandung": "Regional",
        "metro-bandung": "Regional",
        "kabupaten-bandung": "Regional",
        "jabar-region": "Regional",
        "jabar-istimewa": "Regional",
        "ciamis": "Regional",
        "garut": "Regional",
        "cirebon": "Regional",
        "sumedang": "Regional",
        "tasik": "Regional",
        "banyuwangi": "Regional",

        "jatim": "Regional",
        "bojonegoro": "Regional",
        "blitar": "Regional",
        "kediri": "Regional",
        "jombang": "Regional",
        "madura": "Regional",
        "malang": "Regional",
        "mojokerto": "Regional",
        "probolinggo": "Regional",
        "surabaya": "Regional",
        "pasuruan": "Regional",
        "nganjuk": "Regional",
        "trenggalek": "Regional",

        "medan": "Regional",
        "medan-terkini": "Regional",
        "sumut-terkini": "Regional",
        "deliserdang": "Regional",
        "langkat": "Regional",
        "binjai": "Regional",
        "siantar": "Regional",
        "tribun-medan-wiki": "Regional",

        "makassar": "Regional",

        "yogyakarta": "Regional",
        "denpasar": "Regional",
        "tapsel": "Regional",
        "tapteng": "Regional",

        "cek-fakta": "Fact Check",
        "cekfakta": "Fact Check"
    }

    return mapping.get(category, category.title())


def remove_duplicates(articles):
    unique_articles = []
    seen_urls = set()

    for article in articles:

        if article.url in seen_urls:
            continue

        seen_urls.add(article.url)

        article.category = normalize_category(
            article.category
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

        category = normalize_category(
            article.category
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
            normalize_category(
                article.category
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
                normalize_category(
                    article.category
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

        title = article[0]
        source = article[1]

        sentiment = analyze_sentiment(
            title
        )

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
