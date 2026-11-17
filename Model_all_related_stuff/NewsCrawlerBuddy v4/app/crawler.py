"""Job runner: Domain crawl, API collection and Demo mode. All requests use RequestGateway."""
from __future__ import annotations

import asyncio
import gzip
import json
import math
import re
import time
from collections import deque
from datetime import datetime
from urllib.parse import urljoin, urlsplit

import feedparser
import httpx
from bs4 import BeautifulSoup

from . import db, demo, indexer, keystore
from .cleaning import canonical_url, content_hash, normalize_date
from .config import USER_AGENT
from .delay import JobControl, RequestGateway, StopJob
from .extract import extract_article
from .providers import PROVIDERS, ProviderError
from .robots import normalize_url, origin_of, policy_from_response

TERMINAL = {"completed", "failed", "stopped"}


class JobError(Exception):
    """Message is a short code translated by the UI (msg.<code>)."""


class Live:
    """In-memory live status that the SSE endpoint streams to the browser."""

    def __init__(self, job_id: int, target: int) -> None:
        self.job_id, self.target = job_id, target
        self.state, self.message = "queued", ""
        self.collected = self.requests = self.errors = self.skipped = self.duplicates = 0
        self.countdown, self.last_wait, self.backoff = 0.0, None, 1.0
        self.alert, self.alert_until = None, 0.0
        self.status_codes: dict[str, int] = {}
        self.times: deque = deque(maxlen=60)
        self.logs: deque = deque(maxlen=3000)
        self.seq = 0

    def log(self, level: str, code: str, **args) -> None:
        self.seq += 1
        self.logs.append({"n": self.seq, "t": time.strftime("%H:%M:%S"), "level": level,
                          "code": code, "args": args})

    def avg_ms(self) -> int:
        return int(sum(self.times) / len(self.times)) if self.times else 0

    def counts(self) -> dict:
        return {"collected": self.collected, "target": self.target, "requests": self.requests,
                "errors": self.errors, "skipped": self.skipped, "duplicates": self.duplicates,
                "status_codes": self.status_codes, "avg_ms": self.avg_ms()}

    def snapshot(self, after: int = 0):
        now = time.time()
        alert = self.alert if now < self.alert_until else None
        if self.state == "completed":
            mascot = "celebrate"
        elif self.state in ("paused", "failed", "stopped") or alert:
            mascot = "sleepy"
        elif self.state == "running":
            mascot = "walking"
        else:
            mascot = "idle"
        snap = {**self.counts(), "id": self.job_id, "state": self.state, "message": self.message,
                "countdown": round(self.countdown, 1), "last_wait": self.last_wait,
                "backoff": self.backoff, "alert": alert, "times": list(self.times), "mascot": mascot,
                "logs": [l for l in self.logs if l["n"] > after]}
        return snap, self.seq


def parse_headers(text: str) -> dict:
    out = {}
    for line in (text or "").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            if k.strip():
                out[k.strip()] = v.strip()
    return out


def in_range(published, d_from: str, d_to: str) -> bool:
    p = normalize_date(published)
    if not p:
        return True
    return not ((d_from and p < d_from) or (d_to and p > d_to))


def looks_like_article(url: str) -> bool:
    path = urlsplit(url).path
    last = path.rstrip("/").split("/")[-1]
    return bool(re.search(r"\d{6,}", last) or last.count("-") >= 3
                or re.search(r"/(articles?|story|stories)/", path) or re.search(r"/20\d\d/\d\d/", path))


def same_site(url: str, start: str) -> bool:
    a = urlsplit(url).netloc.lower().removeprefix("www.")
    b = urlsplit(start).netloc.lower().removeprefix("www.")
    return a == b or a.endswith("." + b)


class JobRunner:
    def __init__(self, job_id: int, cfg: dict) -> None:
        self.job_id, self.cfg = job_id, cfg
        self.control = JobControl()
        lim = cfg.get("limits", {})
        self.max_articles = int(lim.get("max_articles") or 50)
        self.live = Live(job_id, self.max_articles)
        self.gateway: RequestGateway | None = None
        self.task: asyncio.Task | None = None
        self.visited: set[str] = set()
        self.seen_urls: set[str] = set()
        self.seen_hashes: set[str] = set()
        self.policies: dict = {}

    # ----- control -----
    def start(self) -> None:
        self.task = asyncio.create_task(self._main())

    def pause(self) -> None:
        self.control.pause()
        self._set_state("paused")

    def resume(self) -> None:
        self.control.resume()
        self._set_state("running")

    def stop(self) -> None:
        self.control.stop()

    def _set_state(self, state: str, message: str = "") -> None:
        self.live.state, self.live.message = state, message
        db.update_job(self.job_id, state=state, message=message, progress=self.live.counts())

    def _persist(self) -> None:
        db.update_job(self.job_id, progress=self.live.counts())

    # ----- events from the gateway -----
    def _emit(self, kind: str, **d) -> None:
        L = self.live
        if kind == "countdown":
            L.countdown = d.get("seconds", 0)
        elif kind == "wait":
            L.last_wait, L.backoff = d["seconds"], d.get("backoff", 1)
            L.log("info", "wait", seconds=round(d["seconds"], 1), backoff=d.get("backoff", 1))
        elif kind == "request":
            L.requests += 1
            k = str(d["status"])
            L.status_codes[k] = L.status_codes.get(k, 0) + 1
            L.times.append(d["ms"])
            L.log("info", "req", status=d["status"], ms=d["ms"], url=d["url"][:120])
        elif kind == "alert":
            L.alert = {"status": d["status"], "backoff": d["backoff"]}
            L.alert_until = time.time() + 25
            L.log("warn", "rate_limited", status=d["status"], backoff=d["backoff"])
        elif kind == "log":
            L.log(d.pop("level", "info"), d.pop("code"), **d)

    # ----- main -----
    async def _main(self) -> None:
        L, cfg = self.live, self.cfg
        final, msg = "completed", ""
        try:
            self._build_gateway()
            self.visited = db.visited_set(self.job_id)
            for r in db.article_keys(self.job_id):
                self.seen_urls.add(r["canonical_url"])
                if r["content_hash"]:
                    self.seen_hashes.add(r["content_hash"])
            L.collected = db.count_articles(self.job_id)
            self._set_state("running")
            if L.collected:
                L.log("info", "resumed", n=L.collected)
            if cfg["mode"] == "demo":
                L.log("info", "demo")
                cfg["source"] = {"url": demo.FEED_URL, "start": "rss"}
                await self._run_domain()
            elif cfg["mode"] == "api":
                await self._run_api()
            elif cfg["mode"] == "index":
                await self._run_index()
            else:
                await self._run_domain()
            if self.control.stopped:
                final = "stopped"
        except StopJob:
            final = "stopped"
        except JobError as e:
            final, msg = "failed", str(e)
        except Exception as e:  # noqa: BLE001
            final, msg = "failed", f"{type(e).__name__}: {e}"
        finally:
            if self.gateway:
                await self.gateway.aclose()
        L.countdown = 0
        self._set_state(final, msg)

    def _build_gateway(self) -> None:
        cfg = self.cfg
        adv, lim = cfg.get("advanced", {}), cfg.get("limits", {})
        delay = dict(cfg.get("delay", {}))
        client = None
        if cfg["mode"] == "demo":
            delay.update(base=1.0, var_min=0.2, var_max=0.5, floor=0.2, variation=True, direction="both")
            client = demo.demo_client()
        else:
            delay["floor"] = max(1.0, float(delay.get("floor") or 1.0))
            if adv.get("proxy"):
                client = httpx.AsyncClient(proxy=adv["proxy"], follow_redirects=True)
        pool = [u.strip() for u in (adv.get("ua_list") or "").splitlines() if u.strip()]

        def to_int(v, d):
            try:
                return int(v)
            except (TypeError, ValueError):
                return d
        self.gateway = RequestGateway(
            delay, self.control, emit=self._emit, client=client,
            user_agent=adv.get("user_agent") or USER_AGENT, ua_pool=pool,
            extra_headers=parse_headers(adv.get("headers", "")),
            max_per_hour=to_int(lim.get("max_per_hour"), 0), max_per_day=to_int(lim.get("max_per_day"), 0),
            retries=to_int(adv.get("retries"), 2))

    # ----- storing -----
    def _store(self, rec: dict) -> bool:
        L = self.live
        cu = canonical_url(rec.get("canonical_url") or rec.get("url") or "")
        rec["canonical_url"] = cu
        rec["fetched_at"] = datetime.utcnow().isoformat(timespec="seconds")
        h = content_hash(rec["text"]) if rec.get("text") else None
        if (cu and cu in self.seen_urls) or (h and h in self.seen_hashes):
            L.duplicates += 1
            L.log("info", "dup", url=(rec.get("url") or "")[:120])
            return False
        if not db.add_article(self.job_id, rec.get("url", ""), cu, h, rec):
            L.duplicates += 1
            return False
        self.seen_urls.add(cu)
        if h:
            self.seen_hashes.add(h)
        L.collected += 1
        L.log("info", "saved", title=(rec.get("title") or "")[:80])
        if L.collected % 5 == 0:
            self._persist()
        return True

    # ----- domain mode -----
    async def _run_domain(self) -> None:
        cfg, L, gw = self.cfg, self.live, self.gateway
        src = cfg.get("source", {})
        start_url = normalize_url(src.get("url", ""))
        kind = src.get("start", "section")
        base = origin_of(start_url)
        self.start_url = start_url

        resp = await gw.fetch(base + "/robots.txt")
        pol = policy_from_response(resp, start_url, gw.user_agent)
        self.policies[base] = pol
        rep = pol.report(start_url)
        L.log("info", "robots", status=rep["status"])
        if rep["status"] == "red":
            raise JobError("robots_blocked")
        if pol.crawl_delay:
            gw.raise_base(pol.crawl_delay)
            L.log("info", "crawl_delay", seconds=pol.crawl_delay)

        cands = await self._discover(start_url, kind, pol)
        await self._process(cands)

    async def _process(self, cands: list[dict]) -> None:
        cfg, L = self.cfg, self.live
        L.log("info", "discovered", n=len(cands))
        if not cands:
            raise JobError("no_candidates")

        queue: asyncio.Queue = asyncio.Queue()
        for c in cands:
            queue.put_nowait(c)

        async def worker():
            while not self.control.stopped and L.collected < self.max_articles:
                try:
                    c = queue.get_nowait()
                except asyncio.QueueEmpty:
                    return
                try:
                    await self._handle(c)
                except StopJob:
                    return

        conc = max(1, min(int(cfg.get("advanced", {}).get("concurrency") or 1), 5))
        results = await asyncio.gather(*[worker() for _ in range(conc)], return_exceptions=True)
        for r in results:
            if isinstance(r, Exception) and not isinstance(r, StopJob):
                raise r

    async def _run_index(self) -> None:
        """Index mode: read index pages -> keep links matching the user's regex -> extract each article."""
        cfg, L, gw = self.cfg, self.live, self.gateway
        ix = cfg.get("index", {})
        try:
            pages = indexer.build_pages(ix)
            rx = indexer.compile_pattern(ix.get("link_pattern"))
        except ValueError as e:
            raise JobError(str(e))
        first_url = pages[0]
        base = origin_of(first_url)
        resp = await gw.fetch(base + "/robots.txt")
        pol = policy_from_response(resp, first_url, gw.user_agent)
        self.policies[base] = pol
        rep = pol.report(first_url)
        L.log("info", "robots", status=rep["status"])
        if rep["status"] == "red":
            raise JobError("robots_blocked")
        if pol.crawl_delay:
            gw.raise_base(pol.crawl_delay)
            L.log("info", "crawl_delay", seconds=pol.crawl_delay)

        follow = bool(ix.get("follow_next"))
        limit = indexer.page_budget(ix)
        want = min(self.max_articles * 3 + 20, 20000)
        L.log("info", "index_pages", n=limit)
        queue, scanned, seen = deque(pages), set(), set()
        cands: list[dict] = []
        misses = 0
        stop_empty = indexer.stop_after_empty(ix)
        while queue and len(scanned) < limit and not self.control.stopped:
            if len(cands) >= want:
                L.log("info", "index_enough", n=len(cands), pages=len(scanned))
                break
            page_url = queue.popleft()
            if page_url in scanned:
                continue
            scanned.add(page_url)
            p = await self._policy_for(page_url)
            if not p.can_fetch(page_url):
                L.skipped += 1
                L.log("warn", "robots_skip", url=page_url[:120])
                continue
            r = await gw.fetch(page_url)
            if r is not None and r.status_code in (404, 410) and len(scanned) > 1:
                L.log("info", "index_end", page=len(scanned))
                break
            if r is None or r.status_code >= 400:
                L.errors += 1
                L.log("warn", "fail", url=page_url[:120], status=r.status_code if r is not None else 0)
                continue
            soup = BeautifulSoup(r.text, "lxml")
            new = 0
            for u, text in indexer.extract_links(soup, page_url):
                cu = canonical_url(u)
                if cu in seen or not indexer.matches(rx, u):
                    continue
                seen.add(cu)
                cands.append({"url": u, "title": text})
                new += 1
            L.log("info", "index_page", page=len(scanned), n=new, url=page_url[:120])
            misses = 0 if new else misses + 1
            if stop_empty and misses >= stop_empty:
                L.log("info", "index_empty_stop", n=misses, page=len(scanned))
                break
            if follow:
                nxt = indexer.find_next(soup, page_url)
                if nxt and nxt not in scanned:
                    queue.append(nxt)
        if self.control.stopped:
            return
        await self._process(cands)

    async def _policy_for(self, url: str):
        o = origin_of(url)
        if o not in self.policies:
            resp = await self.gateway.fetch(o + "/robots.txt")
            self.policies[o] = policy_from_response(resp, url, self.gateway.user_agent)
        return self.policies[o]

    async def _discover(self, start_url: str, kind: str, pol) -> list[dict]:
        L, gw = self.live, self.gateway
        want = min(self.max_articles * 2 + 10, 5000)
        cands: list[dict] = []
        seen: set[str] = set()

        def add(c: dict) -> None:
            u = c.get("url") or ""
            cu = canonical_url(u)
            if u.startswith("http") and cu not in seen:
                seen.add(cu)
                cands.append(c)

        def feed_entries(content: bytes) -> bool:
            feed = feedparser.parse(content)
            for e in feed.entries:
                pub = None
                if e.get("published_parsed"):
                    pub = datetime(*e.published_parsed[:6]).strftime("%Y-%m-%d")
                tags = e.get("tags") or []
                add({"url": e.get("link"), "title": e.get("title"), "published": pub,
                     "category": tags[0].get("term") if tags else None})
            return bool(feed.entries)

        if kind == "rss":
            r = await gw.fetch(start_url)
            if r is None or r.status_code >= 400:
                raise JobError("fetch_failed")
            if not feed_entries(r.content):
                soup = BeautifulSoup(r.text, "lxml")
                link = soup.find("link", attrs={"type": re.compile("rss|atom", re.I)})
                if link and link.get("href"):
                    r2 = await gw.fetch(urljoin(start_url, link["href"]))
                    if r2 is not None and r2.status_code < 400:
                        feed_entries(r2.content)

        elif kind == "sitemap":
            first = [start_url] if re.search(r"sitemap|\.xml", start_url, re.I) \
                else (pol.sitemaps or [origin_of(start_url) + "/sitemap.xml"])
            queue, fetched = list(first), 0
            while queue and fetched < 6 and len(cands) < want:
                u = queue.pop(0)
                r = await gw.fetch(u)
                fetched += 1
                if r is None or r.status_code >= 400:
                    continue
                data = r.content
                if u.endswith(".gz"):
                    try:
                        data = gzip.decompress(data)
                    except OSError:
                        pass
                soup = BeautifulSoup(data, "xml")
                if soup.find("sitemapindex"):
                    kids = [l.get_text(strip=True) for l in soup.find_all("loc")]
                    kids.sort(key=lambda k: "news" not in k.lower())
                    queue = kids[:4] + queue
                else:
                    for el in soup.find_all("url"):
                        loc, mod = el.find("loc"), el.find("lastmod")
                        if loc:
                            add({"url": loc.get_text(strip=True),
                                 "published": mod.get_text(strip=True) if mod else None})
            cands.sort(key=lambda c: c.get("published") or "", reverse=True)

        else:  # section page(s)
            depth = max(1, min(int(self.cfg.get("limits", {}).get("depth") or 1), 3))
            max_pages = 1 + 5 * (depth - 1)
            frontier, pages, seen_pages = [(start_url, 1)], 0, {start_url}
            prefix = "/" + (urlsplit(start_url).path.strip("/").split("/")[0] if urlsplit(start_url).path.strip("/") else "")
            while frontier and len(cands) < want and pages < max_pages:
                url, d = frontier.pop(0)
                p = await self._policy_for(url)
                if not p.can_fetch(url):
                    continue
                r = await gw.fetch(url)
                pages += 1
                if r is None or r.status_code >= 400:
                    continue
                soup = BeautifulSoup(r.text, "lxml")
                for a in soup.find_all("a", href=True):
                    u = urljoin(url, a["href"]).split("#")[0]
                    if not u.startswith("http") or not same_site(u, start_url):
                        continue
                    if looks_like_article(u):
                        add({"url": u, "title": a.get_text(" ", strip=True)})
                    elif d < depth and u not in seen_pages and urlsplit(u).path.startswith(prefix) \
                            and "." not in urlsplit(u).path.split("/")[-1]:
                        seen_pages.add(u)
                        frontier.append((u, d + 1))
        return cands

    async def _handle(self, c: dict) -> None:
        L, gw, lim = self.live, self.gateway, self.cfg.get("limits", {})
        url = c["url"]
        cu = canonical_url(url)
        if cu in self.visited or L.collected >= self.max_articles:
            return
        self.visited.add(cu)
        try:
            if not in_range(c.get("published"), lim.get("date_from", ""), lim.get("date_to", "")):
                L.skipped += 1
                L.log("info", "filtered", url=url[:120])
                return
            pol = await self._policy_for(url)
            if not pol.can_fetch(url):
                L.skipped += 1
                L.log("warn", "robots_skip", url=url[:120])
                return
            r = await gw.fetch(url)
            if r is None or r.status_code >= 400 or "html" not in r.headers.get("content-type", "html"):
                L.errors += 1
                L.log("warn", "fail", url=url[:120], status=r.status_code if r is not None else 0)
                return
            art = extract_article(r.text, url, self.cfg.get("advanced", {}).get("selectors"))
            art["published"] = art.get("published") or c.get("published")
            art["category"] = art.get("category") or c.get("category")
            art["title"] = art.get("title") or c.get("title") or ""
            if not art["text"]:
                L.skipped += 1
                L.log("warn", "empty", url=url[:120])
                return
            kws = [k.strip().lower() for k in re.split(r"[,\n]", lim.get("keywords") or "") if k.strip()]
            hay = (art["title"] + " " + art["text"]).lower()
            if (kws and not any(k in hay for k in kws)) or \
                    not in_range(art["published"], lim.get("date_from", ""), lim.get("date_to", "")):
                L.skipped += 1
                L.log("info", "filtered", url=url[:120])
                return
            self._store(art)
        except StopJob:
            raise
        except Exception as e:  # noqa: BLE001
            L.errors += 1
            L.log("warn", "net_error", error=type(e).__name__, url=url[:120])
        finally:
            db.mark_visited(self.job_id, cu)

    # ----- API mode -----
    async def _run_api(self) -> None:
        cfg, L, gw = self.cfg, self.live, self.gateway
        q = cfg.get("api", {})
        prov = PROVIDERS.get(q.get("provider"))
        if not prov:
            raise JobError("api_error")
        key = keystore.get_key(prov.id)
        if not key:
            raise JobError("api_key_missing")
        gw.secrets.append(key)
        gw.raise_floor(prov.min_delay)
        lim = cfg.get("limits", {})
        pages = min(prov.max_pages, math.ceil(self.max_articles / prov.page_size))
        fails = 0
        for page in range(1, pages + 1):
            if L.collected >= self.max_articles or self.control.stopped:
                break
            marker = f"__page__{page}"
            if marker in self.visited:
                continue
            url, params, headers = prov.build(q, page, key)
            r = await gw.fetch(url, params, headers)
            if r is None:
                fails += 1
                L.errors += 1
                if fails >= 3:
                    raise JobError("fetch_failed")
                continue
            if r.status_code in (401, 403):
                raise JobError("auth_failed")
            try:
                data = r.json()
            except ValueError:
                data = {}
            if r.status_code >= 400:
                L.log("error", "api_error", message=str(data)[:150])
                raise JobError("api_error")
            try:
                items, total_pages = prov.parse(data)
            except ProviderError as e:
                L.log("error", "api_error", message=str(e)[:150])
                raise JobError("api_error")
            L.log("info", "page", page=page, items=len(items))
            for it in items:
                if L.collected >= self.max_articles:
                    break
                if not it.get("url") or not in_range(it.get("published"), lim.get("date_from", ""),
                                                     lim.get("date_to", "")):
                    L.skipped += 1
                    continue
                it["category"] = it.get("category") or q.get("category") or None
                it["source"] = it.get("source") or prov.name
                self._store(it)
            db.mark_visited(self.job_id, marker)
            self.visited.add(marker)
            if page >= total_pages or not items:
                break


class JobManager:
    def __init__(self) -> None:
        self.runners: dict[int, JobRunner] = {}

    def start(self, job_id: int) -> JobRunner:
        job = db.get_job(job_id)
        runner = JobRunner(job_id, job["config"])
        self.runners[job_id] = runner
        runner.start()
        return runner

    def get(self, job_id: int) -> JobRunner | None:
        return self.runners.get(job_id)