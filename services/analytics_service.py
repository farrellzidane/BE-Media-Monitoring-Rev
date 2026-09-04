import re

from collections import Counter, defaultdict

from config.settings import NEWS_TOPIC, TOPIC_KEYWORDS
from repositories.article_repository import article_repository
from services.sentiment_reason_service import (
    generate_confidence_reason,
    generate_sentiment_reason,
)
from services.sentiment_service import analyze_sentiment


# Longest phrase first so "cybersecurity firm" is counted instead of bare "cybersecurity".
KEYWORD_PATTERNS = [
    (keyword, re.compile(rf"\b{re.escape(keyword)}\b"))
    for keyword in sorted(TOPIC_KEYWORDS[NEWS_TOPIC], key=len, reverse=True)
]

def _normalize_sentiment(value):
    if value is None:
        return "Neutral"

    normalized = str(value).strip().lower()
    if normalized in {"positive", "pos", "1"}:
        return "Positive"
    if normalized in {"negative", "neg", "-1"}:
        return "Negative"
    return "Neutral"


def _as_article_dict(article):
    if isinstance(article, dict):
        return {
            "title": article.get("title"),
            "source": article.get("source"),
            "category": article.get("category"),
            "published_date": article.get("published_date"),
            "crawl_date": article.get("crawl_date"),
            "url": article.get("url"),
            "content": article.get("content"),
            "sentiment": article.get("sentiment"),
            "confidence": article.get("confidence"),
            "sentiment_reason": article.get("sentiment_reason"),
            "confidence_reason": article.get("confidence_reason"),
            "score_negative": article.get("score_negative"),
            "score_neutral": article.get("score_neutral"),
            "score_positive": article.get("score_positive"),
        }

    values = list(article)
    while len(values) < 14:
        values.append(None)

    return {
        "title": values[0],
        "source": values[1],
        "category": values[2],
        "published_date": values[3],
        "crawl_date": values[4],
        "url": values[5],
        "content": values[6],
        "sentiment": values[7],
        "confidence": values[8],
        "sentiment_reason": values[9],
        "confidence_reason": values[10],
        "score_negative": values[11],
        "score_neutral": values[12],
        "score_positive": values[13],
    }


def _normalize_date(value):
    if value is None:
        return None

    if hasattr(value, "isoformat"):
        value = value.isoformat()

    text = str(value).strip()
    if not text:
        return None

    return text.split(" ")[0]


def _sentiment_bucket(value):
    label = _normalize_sentiment(value)
    return label.lower()


def _article_text(article):
    title = article.get("title") or ""
    content = article.get("content") or ""
    return f"{title} {content}".strip()


def get_articles_with_sentiment(repository=None):
    repository = repository or article_repository
    enriched = []

    for article in repository.get_all():
        record = _as_article_dict(article)
        title = record["title"] or ""
        content = record["content"] or ""
        sentiment = _normalize_sentiment(record["sentiment"])
        confidence = record["confidence"]

        try:
            confidence = float(confidence) if confidence is not None else 0.0
        except (TypeError, ValueError):
            confidence = 0.0

        scores = {
            "Negative": record["score_negative"],
            "Neutral": record["score_neutral"],
            "Positive": record["score_positive"],
        }
        if not any(value is not None for value in scores.values()):
            scores = None

        if record["sentiment"] in (None, ""):
            prediction = analyze_sentiment(_article_text(record))
            sentiment = _normalize_sentiment(prediction.get("label"))
            confidence = float(prediction.get("confidence", 0.0) or 0.0)
            scores = prediction.get("scores")

        reason = record["sentiment_reason"] or generate_sentiment_reason(
            title,
            content,
            sentiment,
        )
        confidence_reason = record["confidence_reason"] or generate_confidence_reason(
            sentiment,
            confidence,
            scores,
        )

        enriched.append(
            {
                "title": title,
                "source": record["source"],
                "category": record["category"] or "General Cybersecurity",
                "published_date": _normalize_date(record["published_date"]),
                "crawl_date": _normalize_date(record["crawl_date"]),
                "url": record["url"],
                "content": content,
                "sentiment": sentiment,
                "confidence": confidence,
                "sentiment_reason": reason,
                "confidence_reason": confidence_reason,
                "score_negative": (scores or {}).get("Negative"),
                "score_neutral": (scores or {}).get("Neutral"),
                "score_positive": (scores or {}).get("Positive"),
            }
        )

    return enriched


def get_daily_volume(repository=None):
    repository = repository or article_repository
    totals = defaultdict(int)

    for article in repository.get_all():
        data = _as_article_dict(article)
        date_key = _normalize_date(data.get("published_date")) or _normalize_date(
            data.get("crawl_date")
        )
        if date_key:
            totals[date_key] += 1

    return dict(sorted(totals.items()))


def get_sentiment_trend(repository=None, enriched_articles=None):
    repository = repository or article_repository
    articles = enriched_articles or get_articles_with_sentiment(repository)
    totals = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})

    for article in articles:
        date_key = _normalize_date(article.get("published_date")) or _normalize_date(
            article.get("crawl_date")
        )
        if not date_key:
            continue

        bucket = _sentiment_bucket(article.get("sentiment"))
        totals[date_key][bucket] += 1

    return dict(sorted(totals.items()))


def get_sentiment_by_category(repository=None, enriched_articles=None):
    repository = repository or article_repository
    articles = enriched_articles or get_articles_with_sentiment(repository)
    totals = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})

    for article in articles:
        category = article.get("category") or "General Cybersecurity"
        bucket = _sentiment_bucket(article.get("sentiment"))
        totals[category][bucket] += 1

    return dict(sorted(totals.items()))


def get_sentiment_by_source(repository=None, enriched_articles=None):
    repository = repository or article_repository
    articles = enriched_articles or get_articles_with_sentiment(repository)
    totals = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})

    for article in articles:
        source = article.get("source") or "Unknown"
        bucket = _sentiment_bucket(article.get("sentiment"))
        totals[source][bucket] += 1

    return dict(sorted(totals.items()))


def get_source_ranking(repository=None, enriched_articles=None):
    repository = repository or article_repository
    articles = enriched_articles or get_articles_with_sentiment(repository)
    totals = defaultdict(int)

    for article in articles:
        source = article.get("source") or "Unknown"
        totals[source] += 1

    return [
        (source, count)
        for source, count in sorted(
            totals.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]


def get_top_keywords(keyword_limit=15, repository=None):
    """Count mentions of the topic vocabulary only, so generic words never trend."""
    repository = repository or article_repository
    counts = Counter()

    for article in repository.get_all():
        data = _as_article_dict(article)
        text = f"{data.get('title') or ''} {data.get('content') or ''}".lower()

        for keyword, pattern in KEYWORD_PATTERNS:
            # Consume matches so a phrase is not counted again via its shorter parts.
            text, hits = pattern.subn(" ", text)
            if hits:
                counts[keyword] += hits

    return counts.most_common(keyword_limit)


def get_latest_articles(article_limit=15, repository=None, enriched_articles=None):
    repository = repository or article_repository
    articles = enriched_articles or get_articles_with_sentiment(repository)

    def sort_key(article):
        published = _normalize_date(article.get("published_date"))
        crawled = _normalize_date(article.get("crawl_date"))
        return (
            published or crawled or "",
            crawled or "",
        )

    return sorted(
        articles,
        key=sort_key,
        reverse=True,
    )[:article_limit]


def get_topic_discovery(repository=None):
    repository = repository or article_repository
    results = []

    for topic_name, keywords in TOPIC_KEYWORDS.items():
        titles = []
        for article in repository.get_all():
            data = _as_article_dict(article)
            haystack = f"{data.get('title') or ''} {data.get('content') or ''}".lower()
            if any(keyword.lower() in haystack for keyword in keywords):
                titles.append(
                    {
                        "title": data.get("title"),
                        "source": data.get("source"),
                        "url": data.get("url"),
                    }
                )

        if titles:
            results.append(
                {
                    "topic_id": topic_name,
                    "keywords": keywords[:10],
                    "titles": titles,
                }
            )

    return results
