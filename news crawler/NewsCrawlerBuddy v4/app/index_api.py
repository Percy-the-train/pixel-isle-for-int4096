"""Index-crawl helper endpoints: analyze an index page, preview page URLs, test a link pattern."""
from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException

from . import config, indexer
from .delay import JobControl, RequestGateway
from .robots import normalize_url, origin_of, policy_from_response

router = APIRouter(prefix="/api/index")


@router.post("/analyze")
async def analyze(payload: dict = Body(...)):
    url = normalize_url(payload.get("url") or "")
    if not url:
        raise HTTPException(400, "url_required")
    # user-initiated: robots.txt + the index page itself (>= 1 s apart)
    gw = RequestGateway({"base": 1, "variation": False, "floor": 1}, JobControl(),
                        user_agent=config.USER_AGENT, retries=1, timeout=15)
    try:
        resp = await gw.fetch(origin_of(url) + "/robots.txt")
        rep = policy_from_response(resp, url, config.USER_AGENT).report(url)
        if rep["status"] == "red":
            raise HTTPException(409, "robots_blocked")
        page = await gw.fetch(url)
    finally:
        await gw.aclose()
    if page is None or page.status_code >= 400:
        raise HTTPException(400, "fetch_failed")
    return {"robots": rep, **indexer.analyze(url, page.text)}


@router.post("/pages")
def pages(payload: dict = Body(...)):
    try:
        urls = indexer.build_pages(payload)
        count = indexer.page_budget(payload)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if len(urls) <= 5:
        return {"count": count, "first": urls, "last": []}
    return {"count": count, "first": urls[:3], "last": urls[-2:]}


@router.post("/test")
def test_pattern(payload: dict = Body(...)):
    try:
        rx = indexer.compile_pattern(payload.get("pattern"))
    except ValueError as e:
        raise HTTPException(400, str(e))
    links = [str(x) for x in (payload.get("links") or [])][:2000]
    hits = [u for u in links if indexer.matches(rx, u)]
    return {"count": len(hits), "total": len(links), "samples": hits[:15]}