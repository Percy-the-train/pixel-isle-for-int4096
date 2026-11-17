"""Demo mode: a fake news website served through httpx.MockTransport (no real network)."""
from __future__ import annotations

import html
import random
import re
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx

DEMO_HOST = "demo.news.local"
DEMO_BASE = f"https://{DEMO_HOST}"
FEED_URL = f"{DEMO_BASE}/rss.xml"

VERBS = ["reaches a new milestone", "faces fresh scrutiny", "surprises analysts", "enters a new phase",
         "draws record interest", "sparks a wide debate"]
TOPICS = {
    "Technology": (
        ["Open-source AI toolkit", "Quantum chip prototype", "City-wide 6G trial", "Battery recycling startup",
         "Privacy-first browser", "Humanoid warehouse robot", "Satellite internet service", "Low-power smartwatch"],
        ["Engineers said the new approach cuts energy use by nearly a third compared with last year's models.",
         "Developers around the world have already begun testing the release in real production environments.",
         "Critics warn that rapid adoption could outpace the safety reviews that regulators have requested.",
         "Investors responded quickly, and several large technology companies announced partnership talks.",
         "A spokesperson noted that the roadmap includes better documentation and wider language support."]),
    "Business": (
        ["Regional bank", "Global shipping group", "Electric bus maker", "Coffee retail chain",
         "Online marketplace", "Renewable energy fund", "Airline alliance", "Food delivery platform"],
        ["Quarterly revenue rose faster than expected, driven mainly by strong demand in overseas markets.",
         "Executives told shareholders that cost controls will continue through the rest of the financial year.",
         "Analysts remain divided on whether the recent rally can last if interest rates stay elevated.",
         "Labour groups asked the company to share more details about planned changes to working schedules.",
         "The board approved a modest dividend and promised an update on its sustainability targets."]),
    "Sports": (
        ["National football team", "Young sprinter", "City marathon", "Basketball champions",
         "Tennis veteran", "Cycling tour leader", "Swimming relay squad", "Rugby club"],
        ["The coach praised the discipline of the players after a demanding schedule of back-to-back matches.",
         "Thousands of fans filled the stadium and created an atmosphere that many described as unforgettable.",
         "Medical staff confirmed that two athletes are recovering well and could return within weeks.",
         "Organisers said ticket sales for the next round have already surpassed the previous season's total.",
         "Commentators highlighted the tactical changes that allowed the team to control the second half."]),
    "Health": (
        ["Community clinic", "Sleep research team", "Vaccine programme", "Hospital network",
         "Nutrition study", "Mental health helpline", "Rural telemedicine pilot", "Public fitness campaign"],
        ["Researchers followed thousands of volunteers for several years to understand long-term effects.",
         "Doctors advise patients to speak with a professional before making any major change to their routine.",
         "Officials said the programme will expand to more neighbourhoods if early results continue to improve.",
         "Experts stressed that small daily habits can add up to meaningful improvements over time.",
         "Funding for the initiative comes from a mix of public grants and private donations."]),
    "World": (
        ["Regional summit", "Climate agreement", "Border trade talks", "Humanitarian mission",
         "Election commission", "Cultural festival", "Port authority", "Disaster relief effort"],
        ["Leaders from several countries met for two days to discuss cooperation on energy and security.",
         "Local residents described a mix of hope and caution as negotiators announced a preliminary outline.",
         "International observers said the process was orderly and that results will be published shortly.",
         "Aid workers reported that supplies have reached most affected areas despite difficult road conditions.",
         "Diplomats expect further meetings next month, with a final statement planned for the autumn."]),
}
CHINESE = [
    ("新型電池技術讓電動車續航力大幅提升", "Technology",
     ["研究團隊今天發表新一代固態電池，實驗顯示能量密度比現有產品高出約百分之三十。",
      "業界人士認為，這項技術若能量產，將明顯降低電動車的成本，並縮短充電所需時間。"]),
    ("本季消費信心回升 零售業者看好年底買氣", "Business",
     ["最新調查指出，民眾對未來半年的經濟情勢較為樂觀，百貨與電商平台的業績同步成長。",
      "專家提醒，通膨壓力尚未完全消退，企業仍需謹慎規劃庫存與人力配置。"]),
    ("城市馬拉松開跑 上萬名跑者齊聚河濱", "Sports",
     ["今年的城市馬拉松吸引上萬名跑者參加，主辦單位表示，補給站與醫療人員皆已就位。",
      "冠軍選手完賽後表示，天氣涼爽加上沿途民眾加油，讓他順利刷新個人最佳成績。"]),
]


def _build() -> list[dict]:
    now = datetime.now(timezone.utc)
    arts = []
    i = 0
    for topic, (subjects, sentences) in TOPICS.items():
        for j, subj in enumerate(subjects):
            rng = random.Random(i * 7 + 3)
            head = f"{subj} {VERBS[(i + j) % len(VERBS)]}"
            paras = [f"{head}, according to officials familiar with the matter. " + rng.choice(sentences)]
            paras += [" ".join(rng.sample(sentences, 3)) for _ in range(3)]
            arts.append({"id": i, "title": head.capitalize(), "category": topic,
                         "author": rng.choice(["Alex Morgan", "Sam Rivera", "Jamie Lee", "Chris Wong"]),
                         "published": (now - timedelta(hours=3 * i + 1)).isoformat(timespec="seconds"),
                         "paragraphs": paras})
            i += 1
    arts.append({**arts[3], "id": i, "title": arts[3]["title"]})  # content duplicate (different URL)
    i += 1
    arts.append({"id": i, "title": "Breaking: more details soon", "category": "World", "author": "Desk",
                 "published": now.isoformat(timespec="seconds"),
                 "paragraphs": ["Breaking: more details soon."]})  # too short -> cleaned away
    i += 1
    for title, cat, paras in CHINESE:
        arts.append({"id": i, "title": title, "category": cat, "author": "編輯部",
                     "published": (now - timedelta(hours=i)).isoformat(timespec="seconds"),
                     "paragraphs": paras})
        i += 1
    return arts


ARTICLES = _build()


def render_html(a: dict) -> str:
    e = lambda s: html.escape(str(s), quote=True)
    body = "".join(f"<p>{e(p)}</p>" for p in a["paragraphs"])
    return (f'<!doctype html><html><head><meta charset="utf-8"><title>{e(a["title"])} - Demo News</title>'
            f'<meta property="og:title" content="{e(a["title"])}">'
            f'<meta property="article:published_time" content="{e(a["published"])}">'
            f'<meta property="article:section" content="{e(a["category"])}">'
            f'<meta name="author" content="{e(a["author"])}">'
            f'<meta name="description" content="{e(a["paragraphs"][0][:120])}">'
            f'<link rel="canonical" href="{DEMO_BASE}/article/{a["id"]}"></head><body>'
            f'<nav>Home | World | Tech</nav><article><h1>{e(a["title"])}</h1><p>Advertisement</p>{body}'
            f'<p>Sign up for our newsletter</p></article><footer>Demo News</footer></body></html>')


def render_feed() -> str:
    items = ""
    for a in ARTICLES:
        pub = format_datetime(datetime.fromisoformat(a["published"]))
        items += (f'<item><title>{html.escape(a["title"])}</title><link>{DEMO_BASE}/article/{a["id"]}</link>'
                  f'<pubDate>{pub}</pubDate><category>{html.escape(a["category"])}</category>'
                  f'<description>{html.escape(a["paragraphs"][0][:100])}</description></item>')
    return (f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Demo News</title>'
            f'<link>{DEMO_BASE}</link><description>Fake news for testing</description>{items}</channel></rss>')


def handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/robots.txt":
        return httpx.Response(200, text=f"User-agent: *\nAllow: /\nSitemap: {DEMO_BASE}/sitemap.xml\n")
    if path == "/rss.xml":
        return httpx.Response(200, text=render_feed(), headers={"content-type": "application/rss+xml"})
    m = re.match(r"^/article/(\d+)$", path)
    if m and int(m.group(1)) < len(ARTICLES):
        return httpx.Response(200, text=render_html(ARTICLES[int(m.group(1))]),
                              headers={"content-type": "text/html; charset=utf-8"})
    return httpx.Response(404, text="not found")


def demo_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), follow_redirects=True)