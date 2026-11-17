"""Pluggable News API adapters (NewsAPI, GNews, The Guardian, NYT)."""
from __future__ import annotations

import math
import re


class ProviderError(Exception):
    pass


def _ymd(d): return (d or "").replace("-", "")
def _iso(d, end=False): return f"{d}T{'23:59:59' if end else '00:00:00'}Z" if d else None
def _clean(p): return {k: v for k, v in p.items() if v not in (None, "")}


def _item(title, text, description, author, published, category, source, url):
    return {"title": title, "text": text or "", "description": description, "author": author,
            "published": published, "category": category, "source": source, "url": url}


class Provider:
    id = name = ""
    page_size = 10
    max_pages = 10
    min_delay = 1.0
    full_text = False
    daily_quota: int | None = None

    def info(self) -> dict:
        return {"id": self.id, "name": self.name, "page_size": self.page_size, "max_pages": self.max_pages,
                "min_delay": self.min_delay, "full_text": self.full_text, "daily_quota": self.daily_quota}

    def build(self, q: dict, page: int, key: str):
        raise NotImplementedError

    def parse(self, data: dict):
        raise NotImplementedError


class NewsAPI(Provider):
    id, name = "newsapi", "NewsAPI"
    page_size, max_pages, daily_quota = 100, 5, 100

    def build(self, q, page, key):
        kw, country, cat = q.get("keyword"), q.get("country"), q.get("category")
        headers = {"X-Api-Key": key}
        if kw and not (country or cat):
            params = {"q": kw, "language": q.get("language"), "from": q.get("date_from"),
                      "to": q.get("date_to"), "sortBy": "publishedAt",
                      "pageSize": self.page_size, "page": page}
            return "https://newsapi.org/v2/everything", _clean(params), headers
        params = {"q": kw, "country": country or (None if cat else "us"), "category": cat,
                  "pageSize": self.page_size, "page": page}
        return "https://newsapi.org/v2/top-headlines", _clean(params), headers

    def parse(self, data):
        if data.get("status") == "error":
            raise ProviderError(data.get("message", "error"))
        items = []
        for a in data.get("articles", []):
            content = re.sub(r"\s*\[\+\d+ chars\]$", "", a.get("content") or "")
            items.append(_item(a.get("title"), content or a.get("description"), a.get("description"),
                               a.get("author"), a.get("publishedAt"), None,
                               (a.get("source") or {}).get("name"), a.get("url")))
        total = data.get("totalResults", 0) or 0
        return items, math.ceil(total / self.page_size)


class GNews(Provider):
    id, name = "gnews", "GNews"
    page_size, max_pages, daily_quota = 10, 10, 100

    def build(self, q, page, key):
        kw = q.get("keyword")
        url = "https://gnews.io/api/v4/" + ("search" if kw else "top-headlines")
        params = {"q": kw, "lang": q.get("language"), "country": q.get("country"),
                  "category": None if kw else q.get("category"),
                  "from": _iso(q.get("date_from")), "to": _iso(q.get("date_to"), True),
                  "max": self.page_size, "page": page, "apikey": key}
        return url, _clean(params), {}

    def parse(self, data):
        if data.get("errors"):
            raise ProviderError(str(data["errors"])[:200])
        items = [_item(a.get("title"), a.get("content") or a.get("description"), a.get("description"),
                       None, a.get("publishedAt"), None, (a.get("source") or {}).get("name"), a.get("url"))
                 for a in data.get("articles", [])]
        return items, math.ceil((data.get("totalArticles", 0) or 0) / self.page_size)


class Guardian(Provider):
    id, name = "guardian", "The Guardian"
    page_size, max_pages, daily_quota, full_text = 50, 100, 5000, True

    def build(self, q, page, key):
        params = {"q": q.get("keyword"), "from-date": q.get("date_from"), "to-date": q.get("date_to"),
                  "section": (q.get("category") or "").lower() or None, "page": page,
                  "page-size": self.page_size, "order-by": "newest",
                  "show-fields": "bodyText,trailText,byline", "api-key": key}
        return "https://content.guardianapis.com/search", _clean(params), {}

    def parse(self, data):
        r = data.get("response", {})
        if r.get("status") != "ok":
            raise ProviderError(r.get("message", "error"))
        items = []
        for a in r.get("results", []):
            f = a.get("fields") or {}
            items.append(_item(a.get("webTitle"), f.get("bodyText") or f.get("trailText"),
                               f.get("trailText"), f.get("byline"), a.get("webPublicationDate"),
                               a.get("sectionName"), "The Guardian", a.get("webUrl")))
        return items, int(r.get("pages", 0) or 0)


class NYT(Provider):
    id, name = "nyt", "New York Times"
    page_size, max_pages, daily_quota, min_delay = 10, 100, 500, 12.0  # 5 requests / minute

    def build(self, q, page, key):
        cat = q.get("category")
        params = {"q": q.get("keyword"), "begin_date": _ymd(q.get("date_from")),
                  "end_date": _ymd(q.get("date_to")), "page": page - 1, "sort": "newest",
                  "fq": f'section_name:("{cat}")' if cat else None, "api-key": key}
        return "https://api.nytimes.com/svc/search/v2/articlesearch.json", _clean(params), {}

    def parse(self, data):
        if data.get("fault"):
            raise ProviderError(data["fault"].get("faultstring", "error"))
        resp = data.get("response", {})
        items = []
        for d in resp.get("docs", []):
            items.append(_item((d.get("headline") or {}).get("main"),
                               d.get("lead_paragraph") or d.get("abstract"), d.get("abstract"),
                               (d.get("byline") or {}).get("original"), d.get("pub_date"),
                               d.get("section_name"), "The New York Times", d.get("web_url")))
        hits = (resp.get("meta") or {}).get("hits", 0) or 0
        return items, min(100, math.ceil(hits / self.page_size))


PROVIDERS = {p.id: p for p in (NewsAPI(), GNews(), Guardian(), NYT())}