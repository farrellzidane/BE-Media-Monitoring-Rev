from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from models.article import Article

from config.settings import (
    DETIK_URLS,
    MAX_ARTICLES,
    USER_AGENT,
    REQUEST_TIMEOUT
)


def get_latest_article_urls(limit=MAX_ARTICLES):

    today = datetime.today().date()
    min_date = today - timedelta(days=30)

    urls = []
    processed_urls = set()

    for detik_url in DETIK_URLS:

        try:

            response = requests.get(
                detik_url,
                headers={
                    "User-Agent": USER_AGENT
                },
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            for link in soup.find_all("a"):

                href = link.get("href")

                if not href:
                    continue

                if "/finance/" not in href:
                    continue

                if "/d-" not in href:
                    continue

                href = href.split("?")[0]

                if href in processed_urls:
                    continue

                article = get_article(href)

                if not article:
                    continue

                if article.published_date:

                    try:

                        article_date = datetime.strptime(
                            article.published_date,
                            "%Y-%m-%d"
                        ).date()

                        if article_date < min_date:
                            continue

                    except:
                        continue

                processed_urls.add(href)
                urls.append(href)

                if len(urls) >= limit:
                    return urls

        except Exception as e:

            print(
                f"DETIK ERROR ({detik_url}): {e}"
            )

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

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    h1 = soup.find("h1")

    if h1:

        title = h1.get_text(
            " ",
            strip=True
        )

    else:

        title = soup.title.get_text(
            strip=True
        )

    content_list = []

    for p in soup.find_all("p"):

        text = p.get_text(
            " ",
            strip=True
        )

        if not text:
            continue

        if text == title:
            continue

        if text.startswith("Lihat juga"):
            continue

        if text.startswith("[Gambas:"):
            continue

        if text.startswith("Simak Video"):
            continue

        content_list.append(text)

    content = "\n".join(content_list)

    published_date = ""

    publish_meta = soup.find(
        "meta",
        attrs={
            "name": "publishdate"
        }
    )

    if publish_meta:

        raw_date = publish_meta.get(
            "content",
            ""
        )

        if raw_date:

            published_date = (
                raw_date
                .split(" ")[0]
                .replace("/", "-")
            )

    if not published_date:

        og_time = soup.find(
            "meta",
            attrs={
                "property": "article:published_time"
            }
        )

        if og_time:

            raw_date = og_time.get(
                "content",
                ""
            )

            if raw_date:
                published_date = raw_date[:10]

    category = "economy"

    return Article(
        title=title,
        url=url,
        source="Detik Finance",
        category=category,
        published_date=published_date,
        content=content
    )