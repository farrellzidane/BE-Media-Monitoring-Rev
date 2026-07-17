from fastapi import APIRouter, Query

from application.monitoring_service import monitoring_service


router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/articles")
def articles():
    return monitoring_service.list_articles()


@router.get("/analytics")
def analytics(
    keyword_limit: int = Query(default=15, ge=1, le=100),
    article_limit: int = Query(default=15, ge=1, le=100),
):
    return monitoring_service.get_analytics(
        keyword_limit=keyword_limit,
        article_limit=article_limit,
    )
