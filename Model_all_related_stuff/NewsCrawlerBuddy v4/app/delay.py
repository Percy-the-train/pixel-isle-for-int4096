"""Delay engine + RequestGateway.

RequestGateway is the ONLY place that sends outbound HTTP requests. It enforces:
  * wait = max(floor, base + direction * uniform(var_min, var_max))   (Flow C)
  * hourly / daily request limits
  * 429 / 403 auto back-off (delay is multiplied) and retries
  * pause / resume / stop at any time (even while waiting)
"""
from __future__ import annotations

import asyncio
import collections
import random
import time
from typing import Callable

import httpx

DEFAULT_DELAY = {"base": 10.0, "variation": True, "var_min": 1.0, "var_max": 5.0,
                 "direction": "both", "floor": 1.0}


def to_float(v, default: float) -> float:
    try:
        x = float(v)
        return x if x == x else default
    except (TypeError, ValueError):
        return default


def normalize_delay(cfg: dict | None = None) -> dict:
    c = dict(DEFAULT_DELAY)
    c.update({k: v for k, v in (cfg or {}).items() if v is not None and v != ""})
    out = {
        "base": max(0.0, to_float(c["base"], 10.0)),
        "variation": bool(c["variation"]),
        "var_min": max(0.0, to_float(c["var_min"], 1.0)),
        "var_max": max(0.0, to_float(c["var_max"], 5.0)),
        "direction": c["direction"] if c["direction"] in ("both", "plus", "minus") else "both",
        "floor": max(0.0, to_float(c["floor"], 1.0)),
    }
    if out["var_min"] > out["var_max"]:
        out["var_min"], out["var_max"] = out["var_max"], out["var_min"]
    return out


def calc_wait(cfg: dict | None, rng: random.Random | None = None) -> float:
    """wait = max(floor, base + direction * uniform(var_min, var_max))"""
    rng = rng or random
    c = normalize_delay(cfg)
    if not c["variation"]:
        return max(c["floor"], c["base"])
    delta = rng.uniform(c["var_min"], c["var_max"])
    if c["direction"] == "both":
        sign = rng.choice((-1, 1))
    else:
        sign = 1 if c["direction"] == "plus" else -1
    return max(c["floor"], c["base"] + sign * delta)


def wait_ranges(cfg: dict | None) -> list[tuple[float, float]]:
    """Possible wait ranges, e.g. [(5, 9), (11, 15)] for base=10, var 1-5, both."""
    c = normalize_delay(cfg)
    base, lo, hi, floor = c["base"], c["var_min"], c["var_max"], c["floor"]
    if not c["variation"]:
        v = max(floor, base)
        return [(v, v)]
    rs = []
    if c["direction"] in ("both", "minus"):
        rs.append((max(floor, base - hi), max(floor, base - lo)))
    if c["direction"] in ("both", "plus"):
        rs.append((max(floor, base + lo), max(floor, base + hi)))
    rs.sort()
    merged = [rs[0]]
    for a, b in rs[1:]:
        if a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    return merged


def _fmt(x: float) -> str:
    return str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.1f}"


def describe_ranges(cfg: dict | None) -> str:
    parts = [f"{_fmt(a)}s" if a == b else f"{_fmt(a)}–{_fmt(b)}s" for a, b in wait_ranges(cfg)]
    return " or ".join(parts)


def safety(cfg: dict | None) -> dict:
    rs = wait_ranges(cfg)
    lo, hi = min(r[0] for r in rs), max(r[1] for r in rs)
    level = "red" if lo < 3 else "yellow" if lo < 5 else "green"
    return {"level": level, "min": lo, "max": hi, "warn": level != "green"}


def average_wait(cfg: dict | None) -> float:
    c = normalize_delay(cfg)
    if not c["variation"]:
        return max(c["floor"], c["base"])
    m = (c["var_min"] + c["var_max"]) / 2
    if c["direction"] == "plus":
        return c["base"] + m
    if c["direction"] == "minus":
        return max(c["floor"], c["base"] - m)
    return max(c["floor"], c["base"])


class StopJob(Exception):
    """Raised inside the gateway when the user stops the job."""


class JobControl:
    def __init__(self) -> None:
        self._resume = asyncio.Event()
        self._resume.set()
        self.paused = False
        self.stopped = False

    def pause(self) -> None:
        self.paused = True
        self._resume.clear()

    def resume(self) -> None:
        self.paused = False
        self._resume.set()

    def stop(self) -> None:
        self.stopped = True
        self.paused = False
        self._resume.set()

    async def checkpoint(self) -> None:
        if self.stopped:
            raise StopJob()
        if self.paused:
            await self._resume.wait()
        if self.stopped:
            raise StopJob()


class RequestGateway:
    def __init__(self, delay_cfg: dict, control: JobControl, emit: Callable | None = None,
                 client: httpx.AsyncClient | None = None, user_agent: str = "NewsCrawlerBuddy/1.0",
                 ua_pool: list[str] | None = None, extra_headers: dict | None = None,
                 max_per_hour: int = 0, max_per_day: int = 0, retries: int = 2,
                 timeout: float = 20.0, secrets: list[str] | None = None) -> None:
        self.cfg = normalize_delay(delay_cfg)
        self.control = control
        self.emit = emit or (lambda kind, **d: None)
        self.client = client or httpx.AsyncClient(follow_redirects=True)
        self.user_agent = user_agent
        self.ua_pool = ua_pool or []
        self.extra_headers = extra_headers or {}
        self.max_hour, self.max_day = max_per_hour, max_per_day
        self.retries, self.timeout = max(0, retries), timeout
        self.secrets = list(secrets or [])
        self.backoff = 1.0
        self.request_count = 0
        self._lock = asyncio.Lock()
        self._last: float | None = None
        self._stamps: collections.deque = collections.deque()
        self._ua_i = 0

    # ----- helpers -----
    async def aclose(self) -> None:
        await self.client.aclose()

    def raise_base(self, seconds: float) -> None:
        """Respect a site's Crawl-delay: never go below it."""
        self.cfg["base"] = max(self.cfg["base"], float(seconds))
        self.cfg["floor"] = max(self.cfg["floor"], float(seconds))

    def raise_floor(self, seconds: float) -> None:
        """Provider rate limits (e.g. NYT 5 req/min)."""
        self.cfg["floor"] = max(self.cfg["floor"], float(seconds))
        self.cfg["base"] = max(self.cfg["base"], float(seconds))

    def _scrub(self, s: str) -> str:
        for sec in self.secrets:
            if sec and len(sec) >= 4:
                s = s.replace(sec, "••••")
        return s

    def _say(self, level: str, code: str, **args) -> None:
        clean = {k: (self._scrub(v) if isinstance(v, str) else v) for k, v in args.items()}
        self.emit("log", level=level, code=code, **clean)

    def _ua(self) -> str:
        if self.ua_pool:
            self._ua_i = (self._ua_i + 1) % len(self.ua_pool)
            return self.ua_pool[self._ua_i]
        return self.user_agent

    async def _sleep(self, seconds: float) -> None:
        end = time.monotonic() + seconds
        while True:
            if self.control.stopped:
                raise StopJob()
            if self.control.paused:
                t0 = time.monotonic()
                self.emit("countdown", seconds=0)
                await self.control.checkpoint()
                end += time.monotonic() - t0
                continue
            rem = end - time.monotonic()
            if rem <= 0:
                self.emit("countdown", seconds=0)
                return
            self.emit("countdown", seconds=rem)
            await asyncio.sleep(min(0.25, rem))

    async def _respect_limits(self) -> None:
        for window, limit, code in ((3600, self.max_hour, "limit_hour"), (86400, self.max_day, "limit_day")):
            if limit <= 0:
                continue
            while True:
                now = time.monotonic()
                while self._stamps and self._stamps[0] < now - 86400:
                    self._stamps.popleft()
                recent = [s for s in self._stamps if s > now - window]
                if len(recent) < limit:
                    break
                wait = recent[0] + window - now + 1
                self._say("warn", code, seconds=int(wait))
                await self._sleep(wait)

    async def _throttle(self) -> None:
        await self.control.checkpoint()
        await self._respect_limits()
        if self._last is not None:
            w = calc_wait(self.cfg) * self.backoff
            self.emit("wait", seconds=w, backoff=self.backoff)
            remaining = w - (time.monotonic() - self._last)
            if remaining > 0:
                await self._sleep(remaining)
        self._last = time.monotonic()
        self._stamps.append(self._last)

    # ----- the single outbound door -----
    async def fetch(self, url: str, params: dict | None = None,
                    headers: dict | None = None) -> httpx.Response | None:
        last_resp = None
        for attempt in range(self.retries + 1):
            async with self._lock:
                await self._throttle()
            hdrs = {"User-Agent": self._ua(), "Accept": "*/*"}
            hdrs.update(self.extra_headers)
            hdrs.update(headers or {})
            t0 = time.monotonic()
            try:
                r = await self.client.get(url, params=params, headers=hdrs, timeout=self.timeout)
            except httpx.HTTPError as e:
                self._last = time.monotonic()
                self.request_count += 1
                self.emit("request", url=url, status=0, ms=int((self._last - t0) * 1000))
                self._say("warn", "net_error", error=type(e).__name__, url=url)
                continue
            self._last = time.monotonic()
            self.request_count += 1
            self.emit("request", url=url, status=r.status_code, ms=int((self._last - t0) * 1000))
            if r.status_code in (429, 403):
                self.backoff = min(self.backoff * 2, 16.0)
                self.emit("alert", status=r.status_code, backoff=self.backoff)
                try:
                    ra = float(r.headers.get("retry-after", ""))
                    self._say("warn", "retry_after", seconds=int(min(ra, 300)))
                    await self._sleep(min(ra, 300))
                except ValueError:
                    pass
                last_resp = r
                continue
            if r.status_code >= 500:
                last_resp = r
                continue
            if r.status_code < 400:
                self.backoff = max(1.0, self.backoff * 0.75)
            return r
        return last_resp