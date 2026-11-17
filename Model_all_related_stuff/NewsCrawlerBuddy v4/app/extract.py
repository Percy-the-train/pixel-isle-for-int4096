"""Article extraction: custom selectors -> trafilatura -> BeautifulSoup fallback."""
from __future__ import annotations

import json
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

try:
    import trafilatura
except Exception:  # optional dependency
    trafilatura = None


def _meta(soup, *names) -> str:
    for n in names:
        tag = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n}) \
              or soup.find("meta", attrs={"itemprop": n})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return ""


def _name(v) -> str:
    if isinstance(v, list):
        return ", ".join(filter(None, (_name(x) for x in v)))
    if isinstance(v, dict):
        return str(v.get("name", ""))
    return str(v or "")


def _json_ld(soup) -> dict:
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
        except Exception:
            continue
        nodes = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for n in nodes:
            if isinstance(n, dict) and "Article" in str(n.get("@type", "")):
                sec = n.get("articleSection")
                return {"datePublished": n.get("datePublished", ""), "author": _name(n.get("author")),
                        "articleSection": sec[0] if isinstance(sec, list) and sec else (sec or "")}
    return {}


def _text_from_expr(html: str, soup, expr: str | None) -> str:
    expr = (expr or "").strip()
    if not expr:
        return ""
    if expr.startswith(("/", "(")):  # XPath
        try:
            import lxml.html
            res = lxml.html.fromstring(html).xpath(expr)
            parts = [r if isinstance(r, str) else r.text_content() for r in res]
            return "\n".join(p.strip() for p in parts if p and p.strip())
        except Exception:
            return ""
    try:
        els = soup.select(expr)
    except Exception:
        return ""
    return "\n".join(e.get_text(" ", strip=True) for e in els if e.get_text(strip=True))


def extract_article(html: str, url: str, selectors: dict | None = None) -> dict:
    sel = selectors or {}
    soup = BeautifulSoup(html, "lxml")
    ld = _json_ld(soup)

    title = (_text_from_expr(html, soup, sel.get("title")) or _meta(soup, "og:title", "twitter:title")
             or (soup.h1.get_text(" ", strip=True) if soup.h1 else "")
             or (soup.title.get_text(strip=True) if soup.title else ""))
    time_tag = soup.find("time", attrs={"datetime": True})
    published = (_text_from_expr(html, soup, sel.get("date"))
                 or _meta(soup, "article:published_time", "datePublished", "pubdate", "date")
                 or ld.get("datePublished") or (time_tag["datetime"] if time_tag else ""))
    author = (_text_from_expr(html, soup, sel.get("author")) or _meta(soup, "author", "article:author")
              or ld.get("author", ""))
    category = _meta(soup, "article:section", "section") or ld.get("articleSection", "")
    description = _meta(soup, "og:description", "description")
    link = soup.find("link", rel="canonical")
    canonical = link["href"].strip() if link and link.get("href") else ""

    text = _text_from_expr(html, soup, sel.get("content"))
    if not text and trafilatura is not None:
        try:
            text = trafilatura.extract(html, url=url, include_comments=False, include_tables=False) or ""
        except Exception:
            text = ""
    if not text:
        box = soup.find("article") or soup
        paras = [p.get_text(" ", strip=True) for p in box.find_all("p")]
        text = "\n".join(p for p in paras if len(p) >= 40)

    return {"title": title.strip(), "text": text.strip(), "description": description,
            "author": author, "published": published, "category": category,
            "canonical_url": canonical, "source": urlsplit(url).netloc, "url": url}