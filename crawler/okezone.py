from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from models.article import Article

from config.settings import (
    OKEZONE_URLS,
    MAX_ARTICLES,
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT
)


def get_latest_article_urls(limit=MAX_ARTICLES):

    today = datetime.today().date()
    min_date = today - timedelta(days=30)

    urls = []
    processed_urls = set()

    for base_url in OKEZONE_URLS:

        try:

            response = requests.get(
                base_url,
                headers=DEFAULT_HEADERS,
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

                if ".okezone.com/read/" not in href:
                    continue

                href = href.split("?")[0]

                parts = href.split("/")

                if "read" not in parts:
                    continue

                idx = parts.index("read")

                if len(parts) <= idx + 3:
                    continue

                try:

                    article_date = datetime(
                        int(parts[idx + 1]),
                        int(parts[idx + 2]),
                        int(parts[idx + 3])
                    ).date()

                except:
                    continue

                if article_date < min_date:
                    continue

                if href in processed_urls:
                    continue

                processed_urls.add(href)
                urls.append(href)

                if len(urls) >= limit:
                    return urls

        except Exception as e:

            print(f"Okezone crawl error: {e}")

    return urls


def get_article(url):

    response = requests.get(
        url,
        headers=DEFAULT_HEADERS,
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
        title = soup.title.get_text(strip=True)

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

        content_list.append(text)

    content = "\n".join(content_list)

    published_date = ""

    parts = url.split("/")

    if "read" in parts:

        idx = parts.index("read")

        if len(parts) > idx + 3:

            published_date = (
                f"{parts[idx + 1]}-"
                f"{parts[idx + 2]}-"
                f"{parts[idx + 3]}"
            )

    try:

        category = (
            url.split("//")[1]
            .split(".")[0]
            .lower()
        )

    except:

        category = "unknown"

    return Article(
        title=title,
        url=url,
        source="Okezone",
        category=category,
        published_date=published_date,
        content=content
    )