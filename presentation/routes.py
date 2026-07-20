from typing import Literal

from fastapi import APIRouter, HTTPException, Query

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
