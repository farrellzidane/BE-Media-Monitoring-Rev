from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from application.monitoring_service import monitoring_service


router = APIRouter()


class SentimentUpdate(BaseModel):
    sentiment: str = Field(pattern="^(positive|neutral|negative)$")


class CrawlSettingsUpdate(BaseModel):
    crawl_enabled: bool
    crawl_interval_minutes: int


class SourceCreate(BaseModel):
    name: str = ""
    url: str


class KeywordCreate(BaseModel):
    keyword: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/articles")
def articles():
    return monitoring_service.list_articles()


@router.patch("/articles/{article_url:path}/sentiment")
def update_article_sentiment(article_url: str, payload: SentimentUpdate):
    if not monitoring_service.update_sentiment(article_url, payload.sentiment):
        raise HTTPException(status_code=404, detail="Artikel tidak ditemukan.")
    return {"status": "updated", "url": article_url, "sentiment": payload.sentiment}


@router.get("/settings")
def settings():
    from services.settings_service import get_settings
    return get_settings()


@router.post("/crawl")
def crawl_now():
    from services.crawl_scheduler import trigger_crawl
    process = trigger_crawl()
    return {"status": "started", "pid": process.pid}


@router.patch("/settings/crawl")
def update_crawl_settings(payload: CrawlSettingsUpdate):
    try:
        from services.settings_service import update_crawl_settings as update_settings
        return update_settings(payload.crawl_enabled, payload.crawl_interval_minutes)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/settings/sources")
def add_source(payload: SourceCreate):
    try:
        from services.settings_service import add_source as create_source
        return create_source(payload.name, payload.url)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.delete("/settings/sources/{source_id}")
def delete_source(source_id: int):
    from services.settings_service import remove_source
    if not remove_source(source_id):
        raise HTTPException(status_code=404, detail="Sumber tidak ditemukan.")
    return {"status": "deleted"}


@router.post("/settings/keywords")
def add_keyword(payload: KeywordCreate):
    try:
        from services.settings_service import add_keyword as create_keyword
        return create_keyword(payload.keyword)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.delete("/settings/keywords/{keyword_id}")
def delete_keyword(keyword_id: int):
    from services.settings_service import remove_keyword
    if not remove_keyword(keyword_id):
        raise HTTPException(status_code=404, detail="Keyword tidak ditemukan.")
    return {"status": "deleted"}


@router.get("/analytics")
def analytics(
    keyword_limit: int = Query(default=15, ge=1, le=100),
    article_limit: int = Query(default=15, ge=1, le=100),
):
    return monitoring_service.get_analytics(
        keyword_limit=keyword_limit,
        article_limit=article_limit,
    )


@router.get("/data-quality/rules/{rule_key}/evidence")
def data_quality_rule_evidence(
    rule_key: str,
    result: Literal["all", "passed", "failed"] = "all",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    try:
        return monitoring_service.get_quality_rule_evidence(
            rule_key=rule_key,
            result_filter=result,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
