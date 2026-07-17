import json
import requests

from bs4 import BeautifulSoup

from models.article import Article

from config.settings import (
    CNBC_URLS,
    MAX_ARTICLES,
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT
)


def get_latest_article_urls(limit=MAX_ARTICLES):
    urls = []
    processed_urls = set()

    for cnbc_url in CNBC_URLS:
        try:
            response = requests.get(
                cnbc_url,
                headers=DEFAULT_HEADERS,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            links = soup.find_all("a")

            for link in links:
                href = link.get("href")

                if not href:
                    continue

                if not href.startswith(
                    "https://www.cnbcindonesia.com/"
                ):
                    continue

                href = href.split("?")[0]

                parts = href.split("/")

                if len(parts) < 6:
                    continue

                category = parts[3]

                if category in [
                    "video",
                    "foto",
                    "opini",
                    "tv",
                    "topik",
                    "indeks",
                    "market-data"
                ]:
                    continue

                article_part = parts[4]

                if "-" not in article_part:
                    continue

                if href in processed_urls:
                    continue

                processed_urls.add(href)
                urls.append(href)

                if len(urls) >= limit:
                    return urls

        except Exception as e:
            print(f"CNBC ERROR ({cnbc_url}): {e}")

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

    title = ""

    h1 = soup.find("h1")

    if h1:
        title = h1.get_text(" ", strip=True)

    if not title:
        meta_title = soup.find(
            "meta",
            property="og:title"
        )

        if meta_title:
            title = meta_title.get(
                "content",
                ""
            ).strip()

    content_list = []

    for p in soup.find_all("p"):
        text = p.get_text(" ", strip=True)

        if not text:
            continue

        if text == title:
            continue

        content_list.append(text)

    content = "\n".join(content_list)

    category = "economy"

    published_date = ""

    for script in soup.find_all(
        "script",
        type="application/ld+json"
    ):
        try:
            data = json.loads(script.get_text())

            if (
                isinstance(data, dict)
                and "datePublished" in data
            ):
                published_date = (
                    data["datePublished"][:10]
                )
                break

        except:
            continue

    if not published_date:
        meta_date = soup.find(
            "meta",
            property="article:published_time"
        )

        if meta_date:
            published_date = (
                meta_date.get(
                    "content",
                    ""
                )[:10]
            )

    if not title:
        return None

    return Article(
        title=title,
        url=url,
        source="CNBC Indonesia",
        category=category,
        published_date=published_date,
        content=content
    )