import pytest

from app import indexer

BBC = "https://www.bbc.com/pages/content-index/2026/11/01"


def _page(hrefs):
    return "<html><head><title>Index</title></head><body>" + "".join(f'<a href="{h}">link</a>' for h in hrefs) + "</body></html>"


def test_query_pagination_is_detected():
    articles = [f"/news/articles/c{i}abc" for i in range(8)]
    html = _page([f"{BBC}?page={n}" for n in range(2, 48)] + articles + ["/news", "/sport"])
    r = indexer.analyze(BBC, html)
    p = r["pagination"]
    assert p["kind"] == "query" and p["template"] == BBC + "?page={n}"
    assert (p["start"], p["end"]) == (2, 47) and p["include_first"] and p["confidence"] == "high"


def test_path_pagination_is_detected():
    base = "https://www.sample.com/xxx/"
    html = _page([f"/xxx/{n}/" for n in range(2, 26)] + ["/xxx/some-story/"])
    p = indexer.analyze(base, html)["pagination"]
    assert p["kind"] == "path" and p["template"] == "https://www.sample.com/xxx/{n}/"
    assert (p["start"], p["end"]) == (2, 25)


def test_article_pattern_is_suggested():
    html = _page([f"{BBC}?page={n}" for n in range(2, 6)]
                 + [f"/news/articles/c{i}abc" for i in range(6)] + ["/news", "/sport", "/weather"])
    pats = indexer.analyze(BBC, html)["patterns"]
    rx = indexer.compile_pattern(pats[0]["pattern"])
    assert indexer.matches(rx, "https://www.bbc.com/news/articles/c9zzz")
    assert not indexer.matches(rx, "https://www.bbc.com/news")


def test_next_link_only_enables_follow_mode():
    html = '<html><body><a rel="next" href="/list?cursor=abc">Next</a><a href="/news/articles/a1b2">x</a></body></html>'
    p = indexer.analyze("https://a.com/list", html)["pagination"]
    assert p["kind"] == "next" and p["follow_next"]


def test_build_pages_range_and_first():
    ix = {"url": "www.sample.com/xxx/", "page_template": "https://www.sample.com/xxx/{n}/",
          "page_start": 2, "page_end": 4, "include_first": True}
    assert indexer.build_pages(ix) == ["https://www.sample.com/xxx/", "https://www.sample.com/xxx/2/",
                                        "https://www.sample.com/xxx/3/", "https://www.sample.com/xxx/4/"]


def test_build_pages_is_capped_and_same_site_only():
    ix = {"url": "https://a.com/x", "page_template": "https://a.com/x?p={n}", "page_start": 1,
          "page_end": 10 ** 9, "include_first": False}
    assert len(indexer.build_pages(ix)) == indexer.MAX_PAGES
    with pytest.raises(ValueError):
        indexer.build_pages({**ix, "page_template": "https://evil.test/?p={n}"})
    with pytest.raises(ValueError):
        indexer.build_pages({**ix, "page_start": 5, "page_end": 2})


def test_stop_after_empty_defaults_to_never():
    assert indexer.stop_after_empty({}) == 0
    assert indexer.stop_after_empty({"stop_empty": ""}) == 0
    assert indexer.stop_after_empty({"stop_empty": 3}) == 3
    assert indexer.stop_after_empty({"stop_empty": -5}) == 0


def test_pattern_validation():
    with pytest.raises(ValueError):
        indexer.compile_pattern("")
    with pytest.raises(ValueError):
        indexer.compile_pattern("(")