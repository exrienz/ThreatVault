import feedparser
from fastapi import APIRouter, Request

from src.config import settings

from ..utils import templates

router = APIRouter(prefix="/thread-intelligence", tags=["thread-intelligence"])


@router.get("/")
async def ti_page(request: Request):
    return templates.TemplateResponse(request, "pages/thread_intelligence/index.html")


@router.get("/newest-cve")
async def newest_cve(request: Request):
    data = feedparser.parse(settings.NEWEST_CVE_URL)
    return templates.TemplateResponse(
        request,
        "pages/thread_intelligence/component/newestCVE.html",
        {"entries": data.entries},
    )
