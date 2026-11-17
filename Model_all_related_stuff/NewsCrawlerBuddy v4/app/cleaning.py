"""Cleaning, deduplication, language detection, train/val/test split, quality report."""
from __future__ import annotations

import hashlib
import html as htmllib
import random
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

FIELD_ORDER = ["title", "text", "description", "author", "published", "category", "language",
               "source", "url", "canonical_url", "word_count"]
DEFAULT_FIELDS = [f for f in FIELD_ORDER if f != "canonical_url"]

_AD = re.compile(
    r"^(advertisement|advertising|ad|sponsored( content)?|sign up.*|subscribe.*|read more:?.*|related:?.*|"
    r"follow us on.*|click here.*|share this.*|廣告|訂閱.*|延伸閱讀.*|相關新聞.*|推薦閱讀.*)$", re.I)
_TRACK = re.compile(r"^(utm_.*|fbclid|gclid|mc_cid|mc_eid|ref|ref_src|cmpid)$", re.I)


# ---------- primitives ----------
_BLOCK_TAGS = ["p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "table",
               "section", "article", "header", "footer", "blockquote", "pre", "figure",
               "figcaption", "dd", "dt", "dl", "aside", "main", "nav", "title"]

def strip_html(text: str) -> str:
    text = text or ""
    if "<" in text and ">" in text:
        soup = BeautifulSoup(text, "lxml")
        for t in soup(["script", "style", "noscript", "iframe"]):
            t.decompose()
        for br in soup.find_all("br"):
            br.replace_with("\n")
        for blk in soup.find_all(_BLOCK_TAGS):
            blk.insert_before("\n")
            blk.insert_after("\n")
        text = soup.get_text("")
    text = htmllib.unescape(text)
    lines = [re.sub(r"[ \t\u00a0]+", " ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln and not _AD.match(ln))


def one_line(text: str) -> str:
    return " ".join((text or "").split())


def word_count(text: str) -> int:
    latin = len(re.findall(r"[A-Za-z0-9_'’\-]+", text or ""))
    cjk = len(re.findall(r"[\u4e00-\u9fff\u3040-\u30ff]", text or ""))
    return latin + cjk


def normalize_date(v) -> str | None:
    if v in (None, ""):
        return None
    try:
        d = dateparser.parse(str(v))
        if d.tzinfo is not None:
            d = d.astimezone(__import__("datetime").timezone.utc)
        return d.strftime("%Y-%m-%d")
    except (ValueError, OverflowError, TypeError):
        return None


def detect_language(text: str) -> str:
    sample = (text or "")[:1000]
    if not sample.strip():
        return "unknown"
    try:
        from langdetect import DetectorFactory, detect
        DetectorFactory.seed = 0
        code = detect(sample)
        return "zh" if code.startswith("zh") else code
    except Exception:
        cjk = len(re.findall(r"[\u4e00-\u9fff]", sample))
        if cjk / max(len(sample), 1) > 0.2:
            return "zh"
        return "en" if re.search(r"[A-Za-z]{3,}", sample) else "unknown"


def canonical_url(url: str) -> str:
    if not url:
        return ""
    p = urlsplit(url.strip())
    q = sorted((k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not _TRACK.match(k))
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), urlencode(q), ""))


def content_hash(text: str) -> str:
    words = " ".join(re.findall(r"\w+", (text or "").lower()))
    return hashlib.sha256(words.encode("utf-8")).hexdigest()


def _norm_title(t: str) -> str:
    return re.sub(r"[\W_]+", " ", (t or "").lower()).strip()


# ---------- dedupe ----------
def dedupe(records: list[dict], title_threshold: float = 0.92) -> tuple[list[dict], dict]:
    seen_url, seen_hash = set(), set()
    index: dict[str, list[int]] = defaultdict(list)
    titles: list[str] = []
    kept, stats = [], {"url": 0, "content": 0, "title": 0}
    for r in records:
        cu = r.get("canonical_url") or canonical_url(r.get("url", ""))
        h = content_hash(r["text"]) if r.get("text") else None
        if cu and cu in seen_url:
            stats["url"] += 1
            continue
        if h and h in seen_hash:
            stats["content"] += 1
            continue
        nt = _norm_title(r.get("title"))
        toks = {w for w in nt.split() if len(w) >= 4} or set(nt.split())
        dup = False
        if nt:
            cand = Counter()
            for w in toks:
                for i in index[w]:
                    cand[i] += 1
            for i, _ in cand.most_common(30):
                if SequenceMatcher(None, nt, titles[i]).ratio() >= title_threshold:
                    dup = True
                    break
        if dup:
            stats["title"] += 1
            continue
        idx = len(titles)
        titles.append(nt)
        for w in toks:
            if len(index[w]) <= 200:  # skip very common tokens -> keeps it fast for 10k+ rows
                index[w].append(idx)
        if cu:
            seen_url.add(cu)
        if h:
            seen_hash.add(h)
        kept.append(r)
    return kept, stats


# ---------- split ----------
def split_dataset(df: pd.DataFrame, ratios=(80, 10, 10), stratify_col: str | None = None,
                  seed: int = 42) -> pd.DataFrame:
    tr, va, te = (max(0.0, float(x)) for x in ratios)
    total = (tr + va + te) or 1.0
    rng = random.Random(seed)
    split = pd.Series("train", index=df.index, dtype=object)
    if stratify_col and stratify_col in df.columns:
        groups = [g.index.tolist() for _, g in df.groupby(stratify_col, dropna=False)]
    else:
        groups = [df.index.tolist()]
    for idx in groups:
        rng.shuffle(idx)
        n = len(idx)
        n_tr = min(round(n * tr / total), n)
        if te <= 0:
            n_va = (n - n_tr) if va > 0 else 0
            n_tr = n if va <= 0 else n_tr
        else:
            n_va = min(round(n * va / total), n - n_tr)
        for i in idx[n_tr:n_tr + n_va]:
            split[i] = "val"
        for i in idx[n_tr + n_va:]:
            split[i] = "test"
    out = df.copy()
    out["split"] = split
    return out


# ---------- full pipeline ----------
def clean_records(records: list[dict], opts: dict) -> tuple[pd.DataFrame, dict]:
    cl, lab, sp = opts.get("cleaning", {}), opts.get("label", {}), opts.get("split", {})
    fields = opts.get("fields") or DEFAULT_FIELDS
    lf = (cl.get("language_filter") or "").strip().lower()
    do_strip = cl.get("strip_html", True)
    stats = {"short": 0, "language": 0, "url": 0, "content": 0, "title": 0}

    rows = []
    for r in records:
        x = dict(r)
        x["title"] = one_line(strip_html(x.get("title") or "")) if do_strip else (x.get("title") or "")
        x["text"] = strip_html(x.get("text") or "") if do_strip else (x.get("text") or "")
        x["description"] = one_line(strip_html(x.get("description") or "")) if do_strip else x.get("description")
        x["word_count"] = word_count(x["text"])
        if cl.get("normalize_dates", True):
            x["published"] = normalize_date(x.get("published"))
        if cl.get("detect_language", True) or lf:
            x["language"] = detect_language(x["text"] or x["title"])
        x["canonical_url"] = x.get("canonical_url") or canonical_url(x.get("url", ""))
        rows.append(x)

    raw = len(rows)
    missing = {f: sum(1 for x in rows if x.get(f) in (None, "")) for f in FIELD_ORDER if f != "word_count"}

    min_words = int(cl.get("min_words") or 0)
    if min_words > 0:
        kept = [x for x in rows if x["word_count"] >= min_words]
        stats["short"], rows = len(rows) - len(kept), kept
    if lf:
        kept = [x for x in rows if (x.get("language") or "").lower().startswith(lf)]
        stats["language"], rows = len(rows) - len(kept), kept
    if cl.get("dedupe", True):
        rows, d = dedupe(rows)
        stats.update(d)

    src = lab.get("source", "category")
    for x in rows:
        if src == "category":
            x["label"] = x.get("category") or "unknown"
        elif src == "manual":
            x["label"] = lab.get("manual") or ""

    cols = ["id"] + [f for f in FIELD_ORDER if f in fields] + (["label"] if src != "none" else [])
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=cols)
    else:
        df["id"] = range(1, len(df) + 1)
        for c in cols:
            if c not in df.columns:
                df[c] = None
        df = df[cols].reset_index(drop=True)
    if sp.get("enabled") and len(df) > 0:
        df = split_dataset(df, (sp.get("train", 80), sp.get("val", 10), sp.get("test", 10)),
                           "label" if sp.get("stratify", True) and src != "none" else None,
                           int(sp.get("seed") or 42))

    wc = [x["word_count"] for x in rows]
    labels = ["<50", "50-99", "100-199", "200-399", "400-799", "800-1599", "1600+"]
    counts = [0] * len(labels)
    if wc:
        cut = pd.cut(pd.Series(wc), bins=[0, 50, 100, 200, 400, 800, 1600, float("inf")],
                     labels=labels, right=False)
        counts = [int(v) for v in cut.value_counts().reindex(labels).fillna(0)]
    removed_dup = stats["url"] + stats["content"] + stats["title"]
    report = {
        "raw": raw, "final": int(len(df)), "removed": stats,
        "duplicate_rate": (removed_dup / raw) if raw else 0.0,
        "missing": missing,
        "word_count": {"labels": labels, "counts": counts,
                       "mean": float(pd.Series(wc).mean()) if wc else 0.0,
                       "median": float(pd.Series(wc).median()) if wc else 0.0},
        "categories": dict(Counter((x.get("category") or "unknown") for x in rows).most_common(20)),
        "languages": dict(Counter((x.get("language") or "unknown") for x in rows).most_common(10)),
        "split_counts": ({k: int(v) for k, v in df["split"].value_counts().items()}
                         if "split" in df.columns else {}),
    }
    return df, report