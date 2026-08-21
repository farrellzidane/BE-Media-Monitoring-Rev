from config.sources import SOURCES

from config.settings import (
    DATA_DIR,
    OUTPUT_FILE,
    NEWS_TOPIC
)

from services.crawler_service import (
    crawl_articles
)

from services.article_service import (
    save_articles,
    save_articles_csv,
    print_statistics,
    remove_duplicates
)

from database.database import (
    close_database,
    create_database,
    save_articles_to_database,
)

from datetime import datetime, timedelta


def main():

    create_database()

    articles = []

    print()
    print("=" * 40)
    print(f"CRAWLING TOPIC: {NEWS_TOPIC}")
    print("=" * 40)

    for source_name, get_urls, get_article in SOURCES:

        source_articles = crawl_articles(
            get_urls,
            get_article,
            source_name
        )

        articles.extend(
            source_articles
        )

    print()
    print(
        f"Total verified {NEWS_TOPIC} articles: "
        f"{len(articles)}"
    )

    articles = remove_duplicates(
        articles
    )

    # ========================================
    # KEEP RECENT NEWS
    # ========================================

    today = datetime.today().date()
    max_age = timedelta(days=30)

    filtered_articles = []

    for article in articles:

        if not article.published_date:
            continue

        try:

            published = datetime.strptime(
                article.published_date,
                "%Y-%m-%d"
            ).date()

            if today - published <= max_age:
                filtered_articles.append(
                    article
                )

        except Exception:
            continue

    articles = filtered_articles

    articles.sort(
        key=lambda article: article.published_date,
        reverse=True
    )

    # ========================================
    # FINAL RESULT
    # ========================================

    print()
    print("=" * 40)
    print("FINAL TOPIC RESULT")
    print("=" * 40)

    print(
        f"Topic      : {NEWS_TOPIC}"
    )

    print(
        f"Articles   : {len(articles)}"
    )

    print("=" * 40)

    print_statistics(
        articles
    )

    # ========================================
    # SAVE
    # ========================================

    save_articles_to_database(
        articles
    )

    save_articles(
        articles,
        OUTPUT_FILE
    )

    save_articles_csv(
        articles,
        str(DATA_DIR / "articles.csv")
    )

    print()
    print(
        f"Saved {len(articles)} "
        f"{NEWS_TOPIC} articles."
    )


if __name__ == "__main__":

    try:
        main()

    finally:
        close_database()
