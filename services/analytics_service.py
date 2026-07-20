from collections import Counter

from repositories.article_repository import (
    ArticleRepository,
    article_repository,
)

from services.sentiment_service import (
    analyze_sentiment
)

from sklearn.feature_extraction.text import (
    TfidfVectorizer
)

from sklearn.cluster import KMeans

from datetime import datetime, timedelta


STOPWORDS = {
    "dan",
    "yang",
    "untuk",
    "dengan",
    "dari",
    "pada",
    "akan",
    "atau",
    "karena",
    "dalam",
    "lebih",
    "soal",
    "usai",
    "atas",
    "hari",
    "baru",
    "indonesia",
    "hasil",
    "setelah",
    "hingga",
    "masih",
    "sudah",
    "sebut",
    "ungkap",
    "jadi",
    "tahun",
    "tim",
    "bakal",
    "saat",
    "agar",
    "bisa",
    "oleh",
    "para",
    "kini"
}

NEGATIVE_FRAMING_WORDS = {
    "ditangkap",
    "korupsi",
    "skandal",
    "hoaks",
    "krisis",
    "gagal",
    "serang",
    "ancam",
    "tewas",
    "penipuan",
    "kasus",
    "diblokir",
    "bocor",
    "kecelakaan",
    "konflik"
}

OBJECTIVE_WORDS = {
    "laporan",
    "data",
    "analisis",
    "rilis",
    "resmi",
    "statistik",
    "survei",
    "penelitian",
    "menurut",
    "berdasarkan"
}

def get_articles_with_sentiment(
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()

    enriched_articles = []

    for article in articles:

        title = article[0]
        source = article[1]
        category = article[2]
        published_date = article[3]
        crawl_date = article[4]
        url = article[5]
        content = article[6] or ""

        full_text = (
            title
            + "\n\n"
            + content
        )

        sentiment_data = analyze_sentiment(
            full_text
        )

        enriched_articles.append(
            {
                "title": title,
                "source": source,
                "category": category,
                "published_date": published_date,
                "crawl_date": crawl_date,
                "url": url,
                "content": content,
                "sentiment": sentiment_data["label"],
                "confidence": sentiment_data["confidence"]
            }
        )

    return enriched_articles

def get_average_confidence(
    repository: ArticleRepository = article_repository
):

    articles = get_articles_with_sentiment(repository)

    if not articles:
        return 0.0

    total = sum(
        article["confidence"]
        for article in articles
    )

    return round(
        total / len(articles),
        4
    )

def get_daily_volume(
    days=30,
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()
    counter = Counter()

    today = datetime.today().date()
    start_date = today - timedelta(days=days - 1)

    for article in articles:
        date = article[3]

        if not date:
            continue

        try:
            article_date = datetime.strptime(
                date,
                "%Y-%m-%d"
            ).date()

        except:
            continue

        if article_date < start_date:
            continue

        counter[date] += 1
    
    current = start_date

    while current <= today:
        key = current.strftime(
            "%Y-%m-%d"
        )

        if key not in counter:
            counter[key] = 0
        
        current += timedelta(days=1)

    return dict(
        sorted(counter.items())
    )


def get_source_statistics(
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()
    counter = Counter()

    for article in articles:
        source = article[1]
        counter[source] += 1

    return counter


def get_category_statistics(
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()
    counter = Counter()

    for article in articles:
        category = article[2]
        counter[category] += 1

    return counter


def get_top_keywords(
    top_n=20,
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()
    keyword_counter = Counter()

    for article in articles:

        title = article[0]
        words = str(title).lower().split()

        for word in words:

            word = word.strip(
                ".,!?():;\"'[]{}"
            )

            if len(word) < 4:
                continue

            if word.isdigit():
                continue

            if word in STOPWORDS:
                continue

            keyword_counter[word] += 1

    return keyword_counter.most_common(top_n)


def get_topic_discovery(
    n_clusters=10,
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()

    valid_articles = []

    for article in articles:
        title = article[0]
        source = article[1]

        if not title:
            continue

        valid_articles.append({
            "title": title,
            "source": source
        })

    titles = [
        article["title"]
        for article in valid_articles
    ]

    if len(titles) < 5:
        return []

    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words=list(STOPWORDS)
    )

    X = vectorizer.fit_transform(titles)

    n_clusters = min(
        n_clusters,
        len(titles)
    )

    model = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10
    )

    model.fit(X)

    feature_names = (
        vectorizer
        .get_feature_names_out()
    )

    clusters = {}

    for i, label in enumerate(model.labels_):

        if label not in clusters:
            clusters[label] = []

        clusters[label].append(
            valid_articles[i]
        )

    results = []

    for cluster_id in sorted(clusters.keys()):

        indices = []

        for idx, lbl in enumerate(model.labels_):
            if lbl == cluster_id:
                indices.append(idx)

        cluster_matrix = X[indices]

        scores = (
            cluster_matrix
            .sum(axis=0)
            .A1
        )

        topic_words = []

        for idx in scores.argsort()[::-1]:

            word = feature_names[idx]

            if word in STOPWORDS:
                continue

            if len(word) < 4:
                continue

            if word.isdigit():
                continue

            topic_words.append(word)

            if len(topic_words) >= 5:
                break

        results.append({
            "topic_id": cluster_id + 1,
            "keywords": topic_words,
            "article_count": len(clusters[cluster_id]),
            "titles": clusters[cluster_id]
        })

    return results


def get_sentiment_by_source(
    repository: ArticleRepository = article_repository,
    articles=None,
):

    if articles is None:
        articles = get_articles_with_sentiment(repository)

    source_stats = {}

    for article in articles:

        source = article["source"]
        sentiment = article["sentiment"]

        if source not in source_stats:
            source_stats[source] = {
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }

        if sentiment == "Positive":
            source_stats[source]["positive"] += 1

        elif sentiment == "Negative":
            source_stats[source]["negative"] += 1

        else:
            source_stats[source]["neutral"] += 1

    return source_stats


def get_category_by_source(
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()

    results = {}

    for article in articles:

        source = article[1]
        category = article[2]

        if source not in results:
            results[source] = {}

        if category not in results[source]:
            results[source][category] = 0

        results[source][category] += 1

    return results


def get_source_ranking(
    repository: ArticleRepository = article_repository,
    articles=None,
):

    sentiment_data = get_sentiment_by_source(repository, articles)

    rankings = []

    for source, stats in sentiment_data.items():
        score = stats["positive"] - stats["negative"]

        rankings.append({
            "source": source,
            "score": score
        })

    rankings.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return rankings


def get_sentiment_trend(
    repository: ArticleRepository = article_repository,
    articles=None,
):

    if articles is None:
        articles = get_articles_with_sentiment(repository)

    trend = {}

    for article in articles:

        published_date = article["published_date"]
        sentiment = article["sentiment"]

        if not published_date:
            continue

        if published_date not in trend:
            trend[published_date] = {
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }

        if sentiment == "Positive":
            trend[published_date]["positive"] += 1

        elif sentiment == "Negative":
            trend[published_date]["negative"] += 1

        else:
            trend[published_date]["neutral"] += 1

    return dict(sorted(trend.items()))

def get_sentiment_by_category(
    repository: ArticleRepository = article_repository,
    articles=None,
):

    if articles is None:
        articles = get_articles_with_sentiment(repository)

    category_stats = {}

    for article in articles:

        category = article["category"]
        sentiment = article["sentiment"]

        if category not in category_stats:
            category_stats[category] = {
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }

        if sentiment == "Positive":
            category_stats[category]["positive"] += 1

        elif sentiment == "Negative":
            category_stats[category]["negative"] += 1

        else:
            category_stats[category]["neutral"] += 1

    return category_stats

def get_media_framing_analysis(
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()

    category_stats = {}

    for article in articles:

        title = str(article[0]).lower()
        category = article[2]

        if category not in category_stats:
            category_stats[category] = {
                "negative": 0,
                "objective": 0
            }

        negative_score = 0
        objective_score = 0

        for word in NEGATIVE_FRAMING_WORDS:
            if word in title:
                negative_score += 1

        for word in OBJECTIVE_WORDS:
            if word in title:
                objective_score += 1

        if negative_score > objective_score:
            category_stats[category]["negative"] += 1
        else:
            category_stats[category]["objective"] += 1

    return category_stats

def get_source_authority_map(
    repository: ArticleRepository = article_repository
):

    articles = get_articles_with_sentiment(repository)

    source_data = {}

    TIER_MAP = {
        "cnn indonesia": 3,
        "kompas": 3,
        "tempo": 3,
        "detik": 3,

        "tribun": 2,
        "cnbc indonesia": 2,
        "liputan6": 2,
        "kumparan": 2,

        "okezone": 1,
        "sindonews": 1
    }

    for article in articles:

        source = str(article["source"]).lower()
        sentiment = article["sentiment"]

        if source not in source_data:
            source_data[source] = {
                "volume": 0,
                "positive": 0,
                "negative": 0,
                "neutral": 0
            }

        source_data[source]["volume"] += 1

        if sentiment == "Positive":
            source_data[source]["positive"] += 1

        elif sentiment == "Negative":
            source_data[source]["negative"] += 1

        else:
            source_data[source]["neutral"] += 1

    results = []

    for source, stats in source_data.items():

        tier = TIER_MAP.get(source, 1)
        total = stats["volume"]

        score = (
            stats["positive"] - stats["negative"]
        ) / total

        if score > 0.05:
            sentiment = "Positive"
        elif score < -0.05:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        results.append({
            "source": source.title(),
            "volume": stats["volume"],
            "score": round(score, 2),
            "tier": tier,
            "sentiment": sentiment
        })

    return results

def get_latest_articles(
    limit=15,
    repository: ArticleRepository = article_repository,
    articles=None,
):

    if articles is None:
        articles = get_articles_with_sentiment(repository)

    grouped = {}

    for article in articles:

        source = article["source"]

        item = {
            "title": article["title"],
            "source": source,
            "category": article["category"],
            "published_date": article["published_date"],
            "crawl_date": article["crawl_date"],
            "url": article["url"],
            "content": article["content"],
            "sentiment": article["sentiment"],
            "confidence": article["confidence"]
        }

        if source not in grouped:
            grouped[source] = []

        grouped[source].append(item)

    results = []

    for source_articles in grouped.values():

        source_articles.sort(
            key=lambda x: x["published_date"] or "",
            reverse=True
        )

        results.extend(source_articles[:2])

    results.sort(
        key=lambda x: x["published_date"] or "",
        reverse=True
    )

    return results[:limit]