"""Index crawling helpers: pagination detection, page-URL expansion, article-link pattern suggestions."""
from __future__ import annotations

import re
from collections import defaultdict
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from .robots import normalize_url

MAX_PAGES = 500
PAGE_PARAMS = ("page", "paged", "pagenum", "pageno", "page_no", "pg", "p", "pn")
NEXT_WORDS = {"next", "next page", "next »", "next ›", "older", "older posts", "›", "»", ">", ">>", "→",
              "下一頁", "下一页", "下一頁 »", "下頁", "後一頁"}
_PRE = r"/page/|/page-|/page_|/p/|/"
_SKIP_EXT = re.compile(r"\.(jpe?g|png|gif|svg|webp|ico|css|js|json|xml|rss|pdf|zip|mp3|mp4|woff2?)$", re.I)


# ---------- small helpers ----------
def _host(u: str) -> str:
    return urlsplit(u).netloc.lower().removeprefix("www.")


def _same_site(a: str, b: str) -> bool:
    return urlsplit(a).scheme in ("http", "https") and _host(a) == _host(b)


def _int(v, default: int) -> int:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return default


def _tpl_regex(tpl: str) -> re.Pattern:
    return re.compile(re.escape(tpl).replace(r"\{n\}", r"(\d+)"))


def extract_links(soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        u = urljoin(base_url, href).split("#")[0]
        if urlsplit(u).scheme not in ("http", "https") or u in seen:
            continue
        seen.add(u)
        out.append((u, a.get_text(" ", strip=True)))
    return out


def find_next(soup: BeautifulSoup, page_url: str) -> str | None:
    """rel=next first, then anchors whose text / aria-label / title looks like 'Next'."""
    for tag in soup.find_all(["link", "a"], rel=True):
        rel = tag.get("rel")
        rel = rel if isinstance(rel, list) else str(rel).split()
        if "next" in [r.lower() for r in rel] and tag.get("href"):
            u = urljoin(page_url, tag["href"]).split("#")[0]
            if u != page_url:
                return u
    for a in soup.find_all("a", href=True):
        labels = {x.strip().lower() for x in (a.get_text(" ", strip=True), a.get("aria-label") or "",
                                              a.get("title") or "") if x}
        if labels & NEXT_WORDS:
            u = urljoin(page_url, a["href"]).split("#")[0]
            if u != page_url and urlsplit(u).scheme in ("http", "https"):
                return u
    return None


# ---------- pagination detection ----------
def _query_template(url: str):
    p = urlsplit(url)
    pairs = parse_qsl(p.query, keep_blank_values=True)
    for i, (k, v) in enumerate(pairs):
        if k.lower() in PAGE_PARAMS and v.isdigit():
            new = [(kk, "__N__" if j == i else vv) for j, (kk, vv) in enumerate(pairs)]
            q = urlencode(new).replace("__N__", "{n}")
            return urlunsplit((p.scheme, p.netloc, p.path, q, "")), int(v)
    return None


def _path_templates(base: str, links: list[tuple[str, str]]):
    """Templates like https://site/xxx/{n}/ or https://site/xxx/page/{n}. Returns (tpl, numbers, low_confidence)."""
    b = urlsplit(base)
    roots = [(b.path.rstrip("/"), False)]
    m = re.match(r"^(?P<root>.*?)(?P<pre>" + _PRE + r")(?P<n>\d+)(?P<post>/?)$", b.path)
    if m:  # the index URL may itself be page N
        roots.append((m["root"], True))
    out = []
    for root, stripped in roots:
        rx = re.compile("^" + re.escape(root) + r"(?P<pre>" + _PRE + r")(?P<n>\d+)(?P<post>/?)$")
        groups: dict[str, set] = defaultdict(set)
        for u, _ in links:
            if not _same_site(u, base):
                continue
            s = urlsplit(u)
            mm = rx.match(s.path)
            if mm:
                tpl = urlunsplit((s.scheme, s.netloc, root + mm["pre"] + "{n}" + mm["post"], s.query, ""))
                groups[tpl].add(int(mm["n"]))
        if stripped and m:
            tpl = urlunsplit((b.scheme, b.netloc, root + m["pre"] + "{n}" + m["post"], b.query, ""))
            groups[tpl].add(int(m["n"]))
            groups = {k: v for k, v in groups.items() if len(v) >= 3}  # date-like paths need more proof
        out.extend((k, v, stripped) for k, v in groups.items())
    return out


def detect_pagination(url: str, soup: BeautifulSoup, links: list[tuple[str, str]]) -> dict:
    nxt = find_next(soup, url)
    bp = urlsplit(url)
    cands = []  # (template, numbers, kind, low_confidence)

    qgroups: dict[str, set] = defaultdict(set)
    own = _query_template(url)
    if own:
        qgroups[own[0]].add(own[1])
    for u, _ in links:
        if _same_site(u, url) and urlsplit(u).path.rstrip("/") == bp.path.rstrip("/"):
            r = _query_template(u)
            if r:
                qgroups[r[0]].add(r[1])
    cands += [(tpl, nums, "query", False) for tpl, nums in qgroups.items()]
    cands += [(tpl, nums, "path", low) for tpl, nums, low in _path_templates(url, links)]

    base_info = {"step": 1, "next_url": nxt}
    if cands:
        tpl, nums, kind, low = max(cands, key=lambda c: (not c[3], len(c[1])))
        m = _tpl_regex(tpl).fullmatch(url.split("#")[0])
        base_n = int(m.group(1)) if m else None
        nums = set(nums) | ({base_n} if base_n is not None else set())
        start = base_n if base_n is not None else 2
        return {**base_info, "kind": kind, "template": tpl, "start": start, "end": max(max(nums), start),
                "include_first": base_n is None, "follow_next": False,
                "confidence": "low" if (low or len(nums) < 3) else "high"}
    if nxt:
        return {**base_info, "kind": "next", "template": "", "start": 1, "end": 20,
                "include_first": True, "follow_next": True, "confidence": "low"}
    return {**base_info, "kind": "none", "template": "", "start": 1, "end": 1,
            "include_first": True, "follow_next": False, "confidence": "none"}


# ---------- page URL expansion ----------
def build_pages(ix: dict) -> list[str]:
    base = normalize_url(ix.get("url") or "")
    if not base:
        raise ValueError("url_required")
    if ix.get("follow_next"):
        return [base]
    tpl = (ix.get("page_template") or "").strip()
    if not tpl:
        return [base]
    if "{n}" not in tpl or not _same_site(tpl.replace("{n}", "1"), base):
        raise ValueError("bad_template")
    start = max(0, _int(ix.get("page_start"), 1))
    end = _int(ix.get("page_end"), start)
    step = max(1, _int(ix.get("page_step"), 1))
    if end < start:
        raise ValueError("bad_range")
    urls = [base] if ix.get("include_first", True) else []
    urls += [tpl.replace("{n}", str(n)) for n in range(start, end + 1, step)[:MAX_PAGES]]
    return list(dict.fromkeys(urls))[:MAX_PAGES]


def page_budget(ix: dict) -> int:
    """How many index pages at most will be read."""
    if ix.get("follow_next"):
        return max(1, min(_int(ix.get("page_end"), 20), MAX_PAGES))
    return len(build_pages(ix))


def stop_after_empty(ix: dict) -> int:
    """Stop reading index pages after N pages in a row without new matching links. 0 = never (default)."""
    return max(0, min(_int(ix.get("stop_empty"), 0), MAX_PAGES))


# ---------- article-link pattern ----------
def _last_class(lasts: list[str]) -> str:
    if all(x.isdigit() for x in lasts):
        return r"\d+"
    if all(re.fullmatch(r"[A-Za-z0-9]+", x) for x in lasts):
        return r"[A-Za-z0-9]+"
    if all(re.fullmatch(r"[\w-]+", x) for x in lasts):
        return r"[\w-]+"
    return r"[^/?#]+"


def suggest_patterns(url: str, links: list[tuple[str, str]], pagination: dict, limit: int = 5) -> list[dict]:
    base_path = urlsplit(url).path.rstrip("/")
    tpl_rx = _tpl_regex(pagination["template"]) if pagination.get("template") else None
    groups: dict[tuple, list] = defaultdict(list)
    for u, _ in links:
        s = urlsplit(u)
        if s.scheme not in ("http", "https") or _SKIP_EXT.search(s.path):
            continue
        if s.path.rstrip("/") == base_path or (tpl_rx and tpl_rx.fullmatch(u)):
            continue  # the index itself or its pagination links
        segs = [x for x in s.path.split("/") if x]
        if not segs:
            continue
        mid = tuple(r"\d+" if x.isdigit() else re.escape(x) for x in segs[:-1])
        groups[(_host(u), mid)].append((u, segs[-1]))

    ranked = []
    for (host, mid), items in groups.items():
        lasts = [l for _, l in items]
        depth = len(mid) + 1
        weight = 1.0 if (depth >= 2 or any(re.search(r"\d", l) for l in lasts)) else 0.3  # top-level menu links
        pattern = ("^https?://(?:www\\.)?" + re.escape(host) + "/" + "".join(m + "/" for m in mid)
                   + _last_class(lasts) + r"/?(?:[?#].*)?$")
        ranked.append((len(items) * weight, len(items), pattern, [u for u, _ in items][:3]))
    ranked.sort(key=lambda r: (r[0], r[1]), reverse=True)
    if any(r[1] >= 2 for r in ranked):
        ranked = [r for r in ranked if r[1] >= 2]
    return [{"pattern": p, "count": c, "samples": s} for _, c, p, s in ranked[:limit]]


def compile_pattern(p: str | None) -> re.Pattern:
    p = (p or "").strip()
    if not p:
        raise ValueError("pattern_required")
    try:
        return re.compile(p, re.I)
    except re.error:
        raise ValueError("bad_pattern")


def matches(rx: re.Pattern, url: str) -> bool:
    return len(url) <= 2000 and rx.search(url) is not None


# ---------- one-shot analysis ----------
def analyze(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    links = extract_links(soup, url)
    pag = detect_pagination(url, soup, links)
    return {"url": url, "title": soup.title.get_text(strip=True) if soup.title else "",
            "links": [u for u, _ in links][:2000], "link_count": len(links),
            "pagination": pag, "patterns": suggest_patterns(url, links, pag)}