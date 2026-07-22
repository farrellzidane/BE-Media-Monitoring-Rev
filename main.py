from config.sources import SOURCES

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
    clear_articles
)

from config.settings import (
    DATA_DIR,
    OUTPUT_FILE
)

from datetime import datetime, timedelta


def main():

    create_database()

    clear_articles()

    sources = SOURCES

    articles = []

    for source_name, get_urls, get_article in sources:

        source_articles = crawl_articles(
            get_urls,
            get_article,
            source_name
        )

        articles.extend(
            source_articles
        )

    articles = remove_duplicates(
        articles
    )
    # =====================================================
    # Keep only recent news
    # =====================================================

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
                filtered_articles.append(article)

        except:
            continue

    articles = filtered_articles

    articles.sort(
        key=lambda article: article.published_date,
        reverse=True
    )

    print()
    print(
        f"Successfully crawled "
        f"{len(articles)} articles."
    )

    print_statistics(
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

    save_articles_to_database(
        articles
    )


if __name__ == "__main__":
    try:
        main()
    finally:
        close_database()
