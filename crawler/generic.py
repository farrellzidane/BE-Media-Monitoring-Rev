from datetime import date
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from models.article import Article
from config.settings import MAX_ARTICLES, REQUEST_TIMEOUT, USER_AGENT


REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/rss+xml,application/atom+xml;q=0.8,*/*;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
}

PLACEHOLDER_TITLES = {
    "don't miss tomorrow's cybersecurity industry news",
    "dont miss tomorrow's cybersecurity industry news",
}


def _is_placeholder_title(title):
    normalized = " ".join((title or "").casefold().split())
    return normalized in PLACEHOLDER_TITLES


def _feed_urls_from_page(soup, source_url):
    return [
        urljoin(source_url, link["href"])
        for link in soup.find_all("link", href=True)
        if "alternate" in link.get("rel", [])
        and link.get("type", "").lower() in {"application/rss+xml", "application/atom+xml", "text/xml", "application/xml"}
    ]


def _extract_feed_urls(feed_text, source_url, limit, seen):
    urls = []
    entries = re.findall(r"<(?:item|entry)\b[^>]*>(.*?)</(?:item|entry)>", feed_text, re.IGNORECASE | re.DOTALL)
    for entry in entries:
        match = re.search(r"<link\b[^>]*href=[\"']([^\"']+)[\"']", entry, re.IGNORECASE)
        if not match:
            match = re.search(r"<(?:link|guid)\b[^>]*>\s*(https?://[^<\s]+)\s*</(?:link|guid)>", entry, re.IGNORECASE)
        if not match:
            continue
        url = urljoin(source_url, match.group(1)).split("#")[0]
        if url not in seen and urlparse(url).scheme in {"http", "https"}:
            seen.add(url)
            urls.append(url)
            if len(urls) >= limit:
                return urls
    return urls


def build_source(source_name, source_url, feed_urls=()):
    def get_latest_article_urls(limit=MAX_ARTICLES):
        base_host = urlparse(source_url).netloc
        urls = []
        seen = set()
        feed_links = list(feed_urls)
        homepage = None
        try:
            homepage = requests.get(source_url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
            if homepage.ok:
                soup = BeautifulSoup(homepage.text, "html.parser")
                feed_links.extend(_feed_urls_from_page(soup, source_url))
        except requests.RequestException:
            pass

        for feed_link in dict.fromkeys(feed_links):
            try:
                feed = requests.get(urljoin(source_url, feed_link), headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
                feed.raise_for_status()
                urls.extend(_extract_feed_urls(feed.text, source_url, limit - len(urls), seen))
                if len(urls) >= limit:
                    return urls[:limit]
            except requests.RequestException:
                continue

        if homepage is None or not homepage.ok:
            if homepage is not None:
                homepage.raise_for_status()
            return urls[:limit]

        soup = BeautifulSoup(homepage.text, "html.parser")
        for link in soup.find_all("a", href=True):
            url = urljoin(source_url, link["href"]).split("#")[0]
            parsed = urlparse(url)
            if parsed.scheme not in {"http", "https"} or parsed.netloc != base_host:
                continue
            path = parsed.path.lower()
            if url == source_url or url in seen or len(path.strip("/").split("/")) < 1:
                continue
            if re.search(r"/(category|categories|tag|tags|author|authors|page|search|about|contact|privacy|terms|subscribe|newsletter)(/|$)", path):
                continue
            if not re.search(r"/20\d{2}/|/(article|articles|news|post|posts)(/|$)|/[a-z0-9-]{24,}", path):
                continue
            seen.add(url)
            urls.append(url)
            if len(urls) >= limit:
                break
        return urls

    def get_article(url):
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        metadata_title = (
            soup.find("meta", attrs={"property": "og:title"})
            or soup.find("meta", attrs={"name": "twitter:title"})
        )
        title = metadata_title.get("content", "").strip() if metadata_title else ""
        if not title:
            title_node = soup.find("h1") or soup.find("title")
            title = title_node.get_text(" ", strip=True) if title_node else ""
        if _is_placeholder_title(title):
            page_title = soup.find("title")
            title = page_title.get_text(" ", strip=True).split(" | ")[0] if page_title else ""
        paragraphs = [
            node.get_text(" ", strip=True)
            for node in soup.find_all("p")
            if node.get_text(" ", strip=True) and node.get_text(" ", strip=True) != title
        ]
        published = ""
        published_node = soup.find("meta", attrs={"property": "article:published_time"})
        if published_node:
            published = (published_node.get("content") or "")[:10]
        return Article(
            title=title,
            url=url,
            source=source_name,
            category="cybersecurity",
            published_date=published or date.today().isoformat(),
            content="\n".join(paragraphs),
        )

    return get_latest_article_urls, get_article
