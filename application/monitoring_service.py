from repositories.article_repository import (
    ArticleRepository,
    article_repository,
)
from services.analytics_service import (
    get_articles_with_sentiment,
    get_daily_volume,
    get_latest_articles,
    get_sentiment_by_category,
    get_sentiment_by_source,
    get_sentiment_trend,
    get_source_ranking,
    get_top_keywords,
)
from services.data_quality_service import get_data_quality_report


ARTICLE_COLUMNS = (
    "title",
    "source",
    "category",
    "published_date",
    "crawl_date",
    "url",
    "content",
)


class MonitoringService:
    def __init__(self, repository: ArticleRepository = article_repository):
        self.repository = repository

    def list_articles(self):
        return [
            dict(zip(ARTICLE_COLUMNS, article))
            for article in self.repository.get_all()
        ]

    def get_analytics(self, keyword_limit, article_limit):
        enriched_articles = get_articles_with_sentiment(self.repository)

        return {
            "quality": get_data_quality_report(self.repository),
            "daily_volume": get_daily_volume(
                repository=self.repository
            ),
            "trend": get_sentiment_trend(
                self.repository,
                enriched_articles,
            ),
            "category_sentiment": get_sentiment_by_category(
                self.repository,
                enriched_articles,
            ),
            "ranking": get_source_ranking(
                self.repository,
                enriched_articles,
            ),
            "source_sentiment": get_sentiment_by_source(
                self.repository,
                enriched_articles,
            ),
            "keywords": get_top_keywords(
                keyword_limit,
                self.repository,
            ),
            "latest_articles": get_latest_articles(
                article_limit,
                self.repository,
                enriched_articles,
            ),
            "articles": enriched_articles,
        }


monitoring_service = MonitoringService()