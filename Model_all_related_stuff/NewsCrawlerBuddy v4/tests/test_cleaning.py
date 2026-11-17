import random
import string

from app.cleaning import (canonical_url, clean_records, dedupe, normalize_date, strip_html,
                          word_count)


def test_canonical_url_strips_tracking_fragment_and_slash():
    assert canonical_url("HTTPS://Example.com/a/?utm_source=x&id=1#top") == "https://example.com/a?id=1"


def test_strip_html_removes_tags_and_ads():
    out = strip_html("<p>Hello <b>world</b></p><script>x()</script><p>Advertisement</p><p>Second</p>")
    assert "<" not in out and "x()" not in out
    assert "Advertisement" not in out
    assert "Hello world" in out and "Second" in out


def test_normalize_date():
    assert normalize_date("2024-03-05T10:00:00+00:00") == "2024-03-05"
    assert normalize_date("garbage") is None
    assert normalize_date("") is None


def test_word_count_handles_chinese():
    assert word_count("hello world") == 2
    assert word_count("你好世界") == 4


def test_dedupe_by_url():
    recs = [{"url": "https://a.com/x?utm_source=1", "title": "Alpha story", "text": "one two three"},
            {"url": "https://a.com/x", "title": "Beta other", "text": "four five six"}]
    kept, stats = dedupe(recs)
    assert len(kept) == 1 and stats["url"] == 1


def test_dedupe_by_content():
    recs = [{"url": "https://a.com/1", "title": "Alpha story", "text": "same body text here"},
            {"url": "https://a.com/2", "title": "Totally different", "text": "Same  body TEXT here!"}]
    kept, stats = dedupe(recs)
    assert len(kept) == 1 and stats["content"] == 1


def test_dedupe_by_similar_title():
    recs = [{"url": "https://a.com/1", "title": "Government announces new climate policy today", "text": "aaa bbb ccc"},
            {"url": "https://a.com/2", "title": "Government announces new climate policy today!", "text": "ddd eee fff"}]
    kept, stats = dedupe(recs)
    assert len(kept) == 1 and stats["title"] == 1


def _records(n):
    rng = random.Random(0)
    out = []
    for i in range(n):
        out.append({"url": f"https://a.com/{i}", "title": "".join(rng.choices(string.ascii_lowercase, k=20)),
                    "text": f"article {i} " + " ".join(rng.choices(["alpha", "beta", "gamma", "delta"], k=40)),
                    "category": "A" if i % 2 else "B", "published": "2024-01-01"})
    return out


def test_split_80_10_10_and_stratified():
    opts = {"fields": ["title", "text", "category"],
            "cleaning": {"dedupe": False, "min_words": 0, "detect_language": False},
            "label": {"source": "category"}, "split": {"enabled": True, "train": 80, "val": 10, "test": 10, "stratify": True}}
    df, rep = clean_records(_records(100), opts)
    counts = df["split"].value_counts().to_dict()
    assert counts == {"train": 80, "val": 10, "test": 10}
    assert set(df[df["split"] == "test"]["label"]) == {"A", "B"}
    assert rep["final"] == 100


def test_short_articles_are_filtered_and_reported():
    recs = _records(5) + [{"url": "https://a.com/s", "title": "Short one", "text": "tiny", "category": "A"}]
    opts = {"cleaning": {"dedupe": False, "min_words": 10, "detect_language": False}, "split": {"enabled": False}}
    df, rep = clean_records(recs, opts)
    assert len(df) == 5 and rep["removed"]["short"] == 1


def test_missing_fields_are_counted():
    recs = [{"url": "https://a.com/1", "title": "T", "text": "word " * 40}]
    _, rep = clean_records(recs, {"cleaning": {"min_words": 0, "detect_language": False}, "split": {"enabled": False}})
    assert rep["missing"]["author"] == 1 and rep["missing"]["title"] == 0