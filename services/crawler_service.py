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
        f"{len(articles)} articles"
    )

    print()

    return articles