import requests
from bs4 import BeautifulSoup
import json

from models.article import Article

from config.settings import (
    CNN_URLS,
    MAX_ARTICLES,
    USER_AGENT,
    REQUEST_TIMEOUT
)


def get_latest_article_urls(limit=MAX_ARTICLES):
    urls = []
    processed_urls = set()

    for cnn_url in CNN_URLS:
        try:
            response = requests.get(
                cnn_url,
                headers={"User-Agent": USER_AGENT},
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

                if not href.startswith("https://www.cnnindonesia.com"):
                    continue

                if "/ekonomi/" not in href:
                    continue

                if "/202" not in href:
                    continue

                href = href.split("?")[0]

                if href in processed_urls:
                    continue

                processed_urls.add(href)
                urls.append(href)

                if len(urls) >= limit:
                    return urls

        except Exception as e:
            print(f"CNN ERROR ({cnn_url}): {e}")

    return urls


def get_article(url):
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
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

        if text in [
            "ADVERTISEMENT",
            "SCROLL TO CONTINUE WITH CONTENT"
        ]:
            continue

        if text.startswith("[Gambas:"):
            continue

        content_list.append(text)

    content = "\n".join(content_list)

    published_date = ""

    meta_time = soup.find(
        "meta",
        attrs={
            "property": "article:published_time"
        }
    )

    if meta_time:
        raw_date = meta_time.get("content", "")

        if raw_date:
            published_date = raw_date[:10]

    if not published_date:
        for script in soup.find_all(
            "script",
            type="application/ld+json"
        ):
            try:
                data = json.loads(script.string)

                if isinstance(data, dict):
                    if "datePublished" in data:
                        published_date = data["datePublished"][:10]
                        break
            except:
                pass

    if not published_date:
        parts = url.split("/")

        if len(parts) >= 5:
            article_id = parts[4]

            if len(article_id) >= 8:
                published_date = (
                    f"{article_id[0:4]}-"
                    f"{article_id[4:6]}-"
                    f"{article_id[6:8]}"
                )

    category = "economy"

    return Article(
        title=title,
        url=url,
        source="CNN Indonesia",
        category=category,
        published_date=published_date,
        content=content
    )