from collections import defaultdict

from services.analytics_service import (
    get_topic_discovery
)

from services.sentiment_service import (
    analyze_sentiment
)


def get_topic_sentiments():

    topics = get_topic_discovery()

    results = []

    for topic in topics:

        positive = 0
        negative = 0
        neutral = 0

        sentiment_details = []

        source_summary = defaultdict(
            lambda: {
                "Positive": 0,
                "Negative": 0,
                "Neutral": 0
            }
        )

        for article in topic["titles"]:

            title = article["title"]
            source = article["source"]

            sentiment = analyze_sentiment(
                title
            )

            sentiment_details.append({
                "title": title,
                "source": source,
                "sentiment": sentiment
            })

            source_summary[source][
                sentiment
            ] += 1

            if sentiment == "Positive":
                positive += 1

            elif sentiment == "Negative":
                negative += 1

            else:
                neutral += 1

        results.append({
            "topic_id": topic["topic_id"],
            "keywords": topic["keywords"],
            "article_count": len(topic["titles"]),
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "titles": topic["titles"],
            "details": sentiment_details,
            "source_summary": dict(
                source_summary
            )
        })

    return results