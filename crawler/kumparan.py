import json
import requests

from models.article import Article

from config.settings import (
    REQUEST_TIMEOUT,
    USER_AGENT
)


from config.settings import MAX_ARTICLES

import json
import requests

from models.article import Article
from config.settings import (
    REQUEST_TIMEOUT,
   USER_AGENT,
    MAX_ARTICLES
)


def get_latest_article_urls(limit=MAX_ARTICLES):

    urls = []
    seen = set()

    for cursor in range(1, 10):

        url = (
            "https://cdn-graphql-v4.kumparan.com/query"
            "?operationName=FindAllActiveHeadlines"
            f"&variables=%7B%22size%22%3A50%2C%22placement%22%3A%22HOMEPAGE%22%2C%22cursor%22%3A%22{cursor}%22%7D"
            "&extensions=%7B%22persistedQuery%22%3A%7B"
            "%22version%22%3A1%2C"
            "%22sha256Hash%22%3A%22eb503c3f2ef2f7f7ffb36ce34b1c928bdefdc87e6f178527f388ce4b5e3ceb16%22"
            "%7D%7D"
        )

        try:
            response = requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            data = response.json()

            edges = (
                data["data"]
                ["FindAllActiveHeadlines"]
                ["edges"]
            )

            if not edges:
                break

            for edge in edges:

                story = edge["story"]
                slug = story["slug"]

                graphql_url = (
                    "https://cdn-graphql-v4.kumparan.com/query"
                    "?operationName=FindStoryBySlug"
                    f"&variables=%7B%22slug%22%3A%22{slug}%22%7D"
                    "&extensions=%7B%22persistedQuery%22%3A%7B"
                    "%22version%22%3A1%2C"
                    "%22sha256Hash%22%3A%22ddc650b3799caa2c56a7abb5103bae13c3875955741b4ac257513c1fb4232a0e%22"
                    "%7D%7D"
                )

                if graphql_url in seen:
                    continue

                seen.add(graphql_url)
                urls.append(graphql_url)

                if len(urls) >= limit:
                    return urls

        except Exception as e:
            print(f"Kumparan cursor {cursor} error: {e}")

    return urls

def get_article(url):

    response = requests.get(
        url,
        headers={
            "User-Agent": USER_AGENT
        },
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    data = response.json()

    story = data["data"]["FindStoryBySlug"]

    document = json.loads(
        story["contentPublish"]["document"]
    )

    content_parts = []

    for node in document["document"]["nodes"]:

        if node.get("type") != "paragraph":
            continue

        text_parts = []

        for child in node.get(
            "nodes",
            []
        ):

            for leaf in child.get(
                "leaves",
                []
            ):

                text_parts.append(
                    leaf.get(
                        "text",
                        ""
                    )
                )

        paragraph = "".join(
            text_parts
        ).strip()

        if paragraph:

            content_parts.append(
                paragraph
            )

    content = "\n".join(
        content_parts
    )

    published_date = (
        story["publishedAt"][:10]
    )

    category = (
        story["channel"]["slug"]
    )

    if category == "bola-sports":
        category = "olahraga"

    return Article(
        title=story["title"],
        url=(
            "https://kumparan.com/"
            + story["slug"]
        ),
        source="Kumparan",
        category=category,
        published_date=published_date,
        content=content
    )


if __name__ == "__main__":

    urls = get_latest_article_urls()

    print()

    for url in urls:
        print(url)