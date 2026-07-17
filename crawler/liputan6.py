import requests

from bs4 import BeautifulSoup

from models.article import Article

from config.settings import (
    LIPUTAN6_URL,
    MAX_ARTICLES,
    DEFAULT_HEADERS,
    REQUEST_TIMEOUT
)


def get_latest_article_urls(
    limit=MAX_ARTICLES
):
    response = requests.get(
        LIPUTAN6_URL,
        headers=DEFAULT_HEADERS,
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    links = soup.find_all("a")

    urls = []
    processed_urls = set()

    for link in links:
        href = link.get("href")

        if not href:
            continue

        if "enamplus.liputan6.com" in href:
            continue

        if "/read/" not in href:
            continue

        if href in processed_urls:
            continue

        processed_urls.add(href)

        urls.append(
            href.split("?")[0]
        )

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

    h1 = soup.find("h1")

    if h1:
        title = h1.get_text(
            " ",
            strip=True
        )
    else:
        title = soup.title.text

    paragraphs = soup.find_all("p")

    content_list = []

    for p in paragraphs:
        text = p.get_text(
            " ",
            strip=True
        )

        if not text:
            continue

        if text == title:
            continue

        content_list.append(
            text
        )

    content = "\n".join(
        content_list
    )

    published_date = ""

    time_tag = soup.find(
        "time"
    )

    if time_tag:
        datetime_value = time_tag.get(
            "datetime"
        )

        if datetime_value:
            published_date = (
                datetime_value[:10]
            )

    category = "unknown"

    try:
        after_domain = url.split(
            "liputan6.com/"
        )[1]

        category = after_domain.split(
            "/"
        )[0]

    except:
        pass

    return Article(
        title=title,
        url=url,
        source="Liputan6",
        category=category,
        published_date=published_date,
        content=content
    )