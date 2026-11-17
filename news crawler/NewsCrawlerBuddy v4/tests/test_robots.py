from app.robots import RobotsPolicy, normalize_url, policy_from_response

UA = "NewsCrawlerBuddy/1.0"
URL = "https://example.com/news"


class Resp:
    def __init__(self, code, text=""):
        self.status_code, self.text = code, text


def test_normalize_url():
    assert normalize_url("bbc.com/news") == "https://bbc.com/news"
    assert normalize_url("http://a.com") == "http://a.com"


def test_allowed_is_green():
    r = RobotsPolicy("User-agent: *\nDisallow: /private", URL, UA).report(URL)
    assert r["status"] == "green" and r["allowed"]


def test_disallowed_is_red():
    r = RobotsPolicy("User-agent: *\nDisallow: /", URL, UA).report(URL)
    assert r["status"] == "red"


def test_partial_is_yellow():
    text = "User-agent: *\nAllow: /news\nDisallow: /"
    r = RobotsPolicy(text, URL, UA).report(URL)
    assert r["status"] == "yellow" and r["reason"] == "partial"


def test_crawl_delay_is_reported_as_yellow():
    pol = RobotsPolicy("User-agent: *\nCrawl-delay: 5", URL, UA)
    assert pol.crawl_delay == 5.0
    assert pol.report(URL)["reason"] == "crawl_delay"


def test_path_rules():
    pol = RobotsPolicy("User-agent: *\nDisallow: /private", URL, UA)
    assert pol.can_fetch("https://example.com/news/a")
    assert not pol.can_fetch("https://example.com/private/a")


def test_missing_robots_means_allowed():
    r = policy_from_response(Resp(404), URL, UA).report(URL)
    assert r["status"] == "green" and r["reason"] == "missing"


def test_access_denied_blocks():
    r = policy_from_response(Resp(403), URL, UA).report(URL)
    assert r["status"] == "red" and r["reason"] == "restricted"


def test_unreachable_is_yellow():
    r = policy_from_response(None, URL, UA).report(URL)
    assert r["status"] == "yellow" and r["reason"] == "unreachable"