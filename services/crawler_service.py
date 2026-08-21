from config.settings import (
    NEWS_TOPIC
)

from services.topic_verification_service import (
    verify_article_topic
)


def is_topic_related(article):
    """
    Backwards-compatible boolean wrapper around the topic verifier.
    """

    return verify_article_topic(
        article,
        NEWS_TOPIC
    ).is_related


def crawl_articles(
    get_urls_function,
    get_article_function,
    source_name
):
    articles = []

    print(
        f"Crawling {source_name}..."
    )

    print()

    try:

        urls = (
            get_urls_function()
        )

        print(
            f"Found {len(urls)} URLs"
        )

    except Exception as e:

        print(
            f"FAILED TO LOAD URLS "
            f"FROM {source_name}"
        )

        print(e)

        print()

        return []

    for url in urls:

        try:

            article = (
                get_article_function(
                    url
                )
            )

            if not article:

                print(
                    f"EMPTY ARTICLE: {url}"
                )

                continue

            if not article.title:

                print()
                print(
                    f"EMPTY TITLE: {url}"
                )
                print()

                continue

            verification = verify_article_topic(
                article,
                NEWS_TOPIC
            )

            if not verification.is_related:

                print(
                    f"[{source_name}] "
                    f"SKIPPED (not {NEWS_TOPIC}): "
                    f"{article.title}"
                )

                print(
                    f"[{source_name}] "
                    f"Verification: {verification.reason}"
                )

                continue

            articles.append(
                article
            )

            print(
                f"[{source_name}] "
                f"VERIFIED: {article.title}"
            )

            print(
                f"[{source_name}] "
                f"Verification: {verification.reason}"
            )

        except Exception as e:

            print()
            print(
                f"ERROR {source_name}:"
            )

            print(url)

            print(e)

            print()

    print(
        f"SUCCESS {source_name}: "
        f"{len(articles)} {NEWS_TOPIC} articles"
    )

    print()

    return articles
