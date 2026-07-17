from repositories.article_repository import (
    ArticleRepository,
    article_repository,
)


def get_data_quality_report(
    repository: ArticleRepository = article_repository
):

    articles = repository.get_all()

    total_articles = len(
        articles
    )

    missing_dates = 0
    empty_titles = 0
    duplicate_titles = 0
    old_articles = 0

    seen_titles = set()

    for article in articles:

        title = article[0]
        date = article[3]

        if not title:
            empty_titles += 1

        if title in seen_titles:
            duplicate_titles += 1

        seen_titles.add(title)

        if not date:
            missing_dates += 1

        elif date < "2026-06-01":
            old_articles += 1

    score = 100

    score -= (
        missing_dates * 5
    )

    score -= (
        empty_titles * 5
    )

    score -= (
        duplicate_titles * 3
    )

    score -= (
        old_articles * 1
    )

    score = max(
        score,
        0
    )

    return {
        "total_articles":
            total_articles,

        "missing_dates":
            missing_dates,

        "empty_titles":
            empty_titles,

        "duplicate_titles":
            duplicate_titles,

        "old_articles":
            old_articles,

        "quality_score":
            score
    }
