import json

from datetime import datetime, timedelta
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from models.article import Article

from config.settings import (
    TRIBUN_URLS,
    MAX_ARTICLES,
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT
)


def get_latest_article_urls(limit=MAX_ARTICLES):

    today = datetime.today().date()
    min_date = today - timedelta(days=30)

    allowed_hosts = {
        urlparse(url).netloc.lower()
        for url in TRIBUN_URLS
    }

    urls = []
    processed_urls = set()

    for tribun_url in TRIBUN_URLS:

        try:

            response = requests.get(
                tribun_url,
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

                if not href.startswith("https://"):
                    continue

                href = href.split("?")[0]

                host = (
                    urlparse(href)
                    .netloc
                    .lower()
                )

                if host not in allowed_hosts:
                    continue

                if "/topic/" in href:
                    continue

                if "/tag/" in href:
                    continue

                if "/images/" in href:
                    continue

                if "/video/" in href:
                    continue

                if href in processed_urls:
                    continue

                try:

                    article = get_article(href)

                except Exception:
                    continue

                if not article:
                    continue

                if not article.published_date:
                    continue

                try:

                    article_date = datetime.strptime(
                        article.published_date,
                        "%Y-%m-%d"
                    ).date()

                except:
                    continue

                if article_date < min_date:
                    continue

                processed_urls.add(href)
                urls.append(href)

                if len(urls) >= limit:
                    return urls

        except Exception as e:

            print(
                f"TRIBUN ERROR ({tribun_url}): {e}"
            )

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

    if not h1:
        return None

    title = h1.get_text(
        " ",
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

        if text.startswith("Baca juga:"):
            continue

        if text.startswith("Lihat Foto"):
            continue

        if text.startswith("TRIBUNNEWS.COM"):
            continue

        content_list.append(text)

    content = "\n".join(
        content_list
    )

    published_date = ""

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):

        try:

            raw_json = script.get_text(
                strip=True
            )

            if not raw_json:
                continue

            data = json.loads(
                raw_json
            )

            if (
                isinstance(data, dict)
                and "datePublished" in data
            ):

                published_date = (
                    data["datePublished"][:10]
                )

                break

            if (
                isinstance(data, dict)
                and "@graph" in data
            ):

                for item in data["@graph"]:

                    if (
                        isinstance(item, dict)
                        and "datePublished" in item
                    ):

                        published_date = (
                            item["datePublished"][:10]
                        )

                        break

                if published_date:
                    break

            if isinstance(data, list):

                for item in data:

                    if (
                        isinstance(item, dict)
                        and "datePublished" in item
                    ):

                        published_date = (
                            item["datePublished"][:10]
                        )

                        break

                if published_date:
                    break

        except:
            continue

    parts = url.split("/")

    if len(parts) > 3:

        category = (
            parts[3]
            .lower()
            .strip()
        )

    else:

        category = "unknown"

    return Article(
        title=title,
        url=url,
        source="Tribun",
        category=category,
        published_date=published_date,
        content=content
    )