import re, html, hashlib, pathlib
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import feedparser, requests, trafilatura

CSV = "data.csv"
OUT = "raw_new_articles.csv"
MIN_ARTICLE_CHARS = 50
MIN_SENT_CHARS = 15
ABBR = re.compile(r"\b(Mr|Mrs|Ms|Dr|Prof|St|Sr|Jr|vs|U\.S|U\.K|No|Inc|Ltd|Co|Gen|Col|Lt|Sen|Rep|Gov)\.$")
SPLIT_RE = re.compile(
    r'(?<=[.!?]["”\'’)])\s+(?=["\'‘’(]?[A-Z0-9])|(?<=[.!?])\s+(?=["\'‘’(]?[A-Z0-9])')
SEG_RE = re.compile(r"[^。!?;]+[。!?;]*|[^。!?;]+$")

FEEDS = {
    "world": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "http://rss.cnn.com/rss/edition_world.rss",
        "https://feeds.skynews.com/feeds/rss/world.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://www.cnbc.com/id/100727362/device/rss/rss.html",
        "https://www.independent.co.uk/news/world/rss",
    ],
    "uk": ["http://feeds.bbci.co.uk/news/uk/rss.xml"],
    "business": [
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.theguardian.com/business/rss",
        "http://rss.cnn.com/rss/edition_business.rss",
        "https://feeds.skynews.com/feeds/rss/business.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    ],
    "technology": [
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://www.theguardian.com/technology/rss",
        "http://rss.cnn.com/rss/edition_technology.rss",
        "https://feeds.skynews.com/feeds/rss/technology.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://www.cnbc.com/id/19854910/device/rss/rss.html",
    ],
    "science": [
        "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://www.theguardian.com/science/rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
    ],
    "health": [
        "http://feeds.bbci.co.uk/news/health/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
    ],
    "sport": [
        "http://feeds.bbci.co.uk/sport/rss.xml",
        "https://www.theguardian.com/sport/rss",
        "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml",
        "https://www.espn.com/espn/rss/news",
    ],
    "entertainment": [
        "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "https://www.theguardian.com/culture/rss",
    ],
    "general": [
        "http://rss.cnn.com/rss/edition.rss",
        "https://rss.dw.com/rdf/rss-en-all",
        "https://feeds.npr.org/1001/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "https://abcnews.go.com/abcnews/topstories",
        "https://moxie.foxnews.com/google-publisher/latest.xml",
    ],
}
CAP_PER_CATEGORY = 200


def clean_text(t):
    t = re.sub(r"<[^>]*>", " ", str(t))
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    t = html.unescape(t)
    t = re.sub(r"\.{3}(?=\s*(\n|$))", "", t)
    t = re.sub(r"\.{3}\s*", " ", t)
    t = t.replace("…", " ")
    t = re.sub(r"[ \t\u00a0]+", " ", t)
    t = re.sub(r" *\n *", "\n", t).strip()
    return t


def split_sentences(t):
    out = []
    for par in re.split(r"\n+", t):
        par = par.strip()
        if not par:
            continue
        chunks = []
        for p in SPLIT_RE.split(par):
            if chunks and ABBR.search(chunks[-1]):
                chunks[-1] += " " + p
            else:
                chunks.append(p)
        for c in chunks:
            for s in SEG_RE.findall(c):
                s = s.strip()
                if s:
                    out.append(s)
    return out


def content_hash(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def fetch_feed(url, category):
    d = feedparser.parse(url)
    arts = []
    for e in d.entries:
        title = re.sub(r"\s+", " ", (e.get("title") or "")).strip()
        link = e.get("link") or ""
        if not title or not link:
            continue
        arts.append(dict(title=title, url=link, summary=e.get("summary") or "",
                         published=e.get("published") or ""))
    return arts


def get_full_text(url, summary):
    if len(summary.strip()) >= 600:
        return summary
    try:
        hdr = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) news-collector/1.0"}
        txt = trafilatura.extract(requests.get(url, headers=hdr, timeout=20).text)
        if txt and len(txt.strip()) >= 400:
            return txt
    except Exception:
        pass
    return summary


def main(target_articles=1300):
    seen_urls = set()
    seen_hashes = set()
    if pathlib.Path(CSV).exists():
        full = pd.read_csv(CSV)
        seen_urls = set(full.url.dropna().astype(str))
        for _, g in full.groupby("article_id"):
            seen_hashes.add(content_hash(" ".join(g.sort_values("sent_idx").sentence)))
        next_id = int(full.article_id.max()) + 1
    else:
        next_id = 1
    rows = []
    n_arts = 0
    cat_counts = {}
    for cat, feeds in FEEDS.items():
        for f in feeds:
            try:
                arts = fetch_feed(f, cat)
            except Exception as e:
                print(f"feed fail {f}: {e}")
                continue
            print(f"{cat} {f}: {len(arts)} entries")
            cands = [a for a in arts if a["url"] not in seen_urls]
            texts = {}
            with ThreadPoolExecutor(max_workers=8) as ex:
                for a, txt in zip(cands, ex.map(lambda a: get_full_text(a["url"], a["summary"]), cands)):
                    texts[a["url"]] = txt
            for a in cands:
                if cat_counts.get(cat, 0) >= CAP_PER_CATEGORY:
                    break
                text = clean_text(texts[a["url"]])
                if len(text) < MIN_ARTICLE_CHARS:
                    continue
                h = content_hash(text)
                if h in seen_hashes:
                    continue
                sents = [s for s in split_sentences(text) if len(s) >= MIN_SENT_CHARS]
                if len(sents) < 3:
                    continue
                seen_urls.add(a["url"])
                seen_hashes.add(h)
                domain = re.sub(r"^https?://(www\.)?", "", a["url"]).split("/")[0]
                for i, s in enumerate(sents):
                    rows.append(dict(article_id=next_id, title=a["title"], id="",
                                     author="", published=a["published"], category=cat,
                                     language="en", source=domain, url=a["url"],
                                     split="", sent_idx=i + 1, sentence=s,
                                     sentence_label="", source_file="fetched_rss.csv"))
                next_id += 1
                n_arts += 1
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
                if n_arts >= target_articles:
                    break
            print(f"  -> kept {cat_counts.get(cat, 0)} from {cat} (total {n_arts})")
            if n_arts >= target_articles:
                break
        if n_arts >= target_articles:
            break
    df = pd.DataFrame(rows, columns=["article_id", "title", "id", "author", "published",
                                     "category", "language", "source", "url", "split",
                                     "sent_idx", "sentence", "sentence_label", "source_file"])
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"saved {OUT}: {df.article_id.nunique()} articles, {len(df)} sentences")
    print(df.category.value_counts().to_dict())


if __name__ == "__main__":
    main()
