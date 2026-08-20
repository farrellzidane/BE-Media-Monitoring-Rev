from datetime import datetime, timedelta
import json
import requests
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from models.article import Article

from config.settings import (
    TEMPO_URL,
    MAX_ARTICLES,
    REQUEST_TIMEOUT,
    DEFAULT_HEADERS
)


def get_latest_article_urls(limit=MAX_ARTICLES):

    today = datetime.today().date()
    min_date = today - timedelta(days=30)

    response = requests.get(
        TEMPO_URL,
        headers=DEFAULT_HEADERS,
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    urls = []
    processed_urls = set()

    for link in soup.find_all("a"):

        href = link.get("href")

        if not href:
            continue

        if not href.startswith("/"):
            continue

        if href.count("/") < 2:
            continue

        if "-" not in href:
            continue

        if "/foto/" in href:
            continue

        if "/tag/" in href:
            continue

        if "/newsletter" in href:
            continue

        if not href.startswith("/ekonomi/"):
            continue

        if "/info-tempo" in href:
            continue

        if "/plus" in href:
            continue

        # `href` begins with `/ekonomi/...`; concatenating it with the
        # section URL (`https://www.tempo.co/ekonomi`) produced an invalid
        # `/ekonomi/ekonomi/...` URL.  urljoin resolves it from the domain.
        full_url = urljoin(
            TEMPO_URL,
            href.split("?")[0]
        )

        if full_url in processed_urls:
            continue

        article = get_article(full_url)

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

        processed_urls.add(full_url)
        urls.append(full_url)

        if len(urls) >= limit:
            break

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

    script = soup.find(
        "script",
        attrs={
            "type": "application/ld+json"
        }
    )

    if not script:
        return None

    try:

        data = json.loads(
            script.string
        )

    except:
        return None

    title = data.get(
        "headline",
        ""
    )

    content = data.get(
        "articleBody",
        ""
    )

    published_date = data.get(
        "datePublished",
        ""
    )

    if published_date:

        published_date = (
            published_date
            .split("T")[0]
        )

    category = "financial"

    return Article(
        title=title,
        url=url,
        source="Tempo Ekonomi",
        category=category,
        published_date=published_date,
        content=content
    )
