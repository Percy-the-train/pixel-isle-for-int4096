"""robots.txt handling: parse, evaluate, traffic-light report."""
from __future__ import annotations

import re
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser


def normalize_url(raw: str) -> str:
    raw = (raw or "").strip()
    if raw and not re.match(r"^https?://", raw, re.I):
        raw = "https://" + raw
    return raw


def origin_of(url: str) -> str:
    p = urlsplit(url)
    return f"{p.scheme}://{p.netloc}"


class RobotsPolicy:
    def __init__(self, text: str | None, url: str, ua: str, reason: str = "ok") -> None:
        self.ua = ua
        self.found = text is not None
        self.reason = reason if self.found else (reason if reason != "ok" else "missing")
        self.origin = origin_of(url)
        self._rp = RobotFileParser()
        self._rp.parse((text or "").splitlines())
        self._rp.modified()  # IMPORTANT: otherwise can_fetch() returns False

    def can_fetch(self, url: str) -> bool:
        return self._rp.can_fetch(self.ua, url)

    @property
    def crawl_delay(self) -> float | None:
        v = self._rp.crawl_delay(self.ua)
        return float(v) if v else None

    @property
    def sitemaps(self) -> list[str]:
        return list(self._rp.site_maps() or [])

    def report(self, target: str) -> dict:
        allowed = self.can_fetch(target)
        root_ok = self.can_fetch(self.origin + "/")
        cd = self.crawl_delay
        if self.reason == "unreachable":
            status, reason = "yellow", "unreachable"
        elif not allowed:
            status, reason = "red", ("restricted" if self.reason == "restricted" else "disallowed")
        elif not root_ok:
            status, reason = "yellow", "partial"
        elif cd:
            status, reason = "yellow", "crawl_delay"
        else:
            status, reason = "green", ("ok" if self.found else "missing")
        return {"status": status, "reason": reason, "found": self.found, "allowed": allowed,
                "crawl_delay": cd, "sitemaps": self.sitemaps, "robots_url": self.origin + "/robots.txt"}


def policy_from_response(resp, url: str, ua: str) -> RobotsPolicy:
    if resp is None:
        return RobotsPolicy(None, url, ua, "unreachable")
    if resp.status_code in (401, 403):
        return RobotsPolicy("User-agent: *\nDisallow: /", url, ua, "restricted")
    if resp.status_code >= 400:
        return RobotsPolicy(None, url, ua, "missing")
    return RobotsPolicy(resp.text, url, ua)