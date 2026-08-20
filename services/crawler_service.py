from config.settings import (
    NEWS_TOPIC,
    TOPIC_KEYWORDS
)


def is_topic_related(article):
    """
    Check whether an article is related to the configured news topic.
    Topic and keywords are controlled through config/settings.py.
    """

    keywords = TOPIC_KEYWORDS.get(
        NEWS_TOPIC,
        []
    )

    if not keywords:
        return True

    text = (
        f"{article.title} "
        f"{article.content}"
    ).lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


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

            if not is_topic_related(article):

                print(
                    f"[{source_name}] "
                    f"SKIPPED (not {NEWS_TOPIC}): "
                    f"{article.title}"
                )

                continue

            articles.append(
                article
            )

            print(
                f"[{source_name}] "
                f"{article.title}"
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