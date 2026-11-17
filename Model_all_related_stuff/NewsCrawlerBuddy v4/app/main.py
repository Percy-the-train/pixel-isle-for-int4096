"""FastAPI application."""
from __future__ import annotations

import asyncio
import json
import math
import re
import time
from contextlib import asynccontextmanager

import yaml
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import config, db, keystore, pipeline
from .crawler import TERMINAL, JobManager
from .delay import (JobControl, RequestGateway, average_wait, calc_wait, describe_ranges,
                    normalize_delay, safety, to_float, wait_ranges)
from . import indexer
from .index_api import router as index_router
from .providers import PROVIDERS
from .robots import normalize_url, origin_of, policy_from_response

manager = JobManager()
SAFE = re.compile(r"^[\w\-.]+$")


async def scheduler_loop() -> None:
    """Runs scheduled presets (daily / weekly) while the app is open."""
    while True:
        await asyncio.sleep(60)
        try:
            now = time.time()
            for p in db.list_presets():
                period = {"daily": 86400, "weekly": 604800}.get(p["schedule"] or "")
                if period and now - (p["last_run"] or now) >= period:
                    cfg = _validate(p["config"])
                    jid = db.create_job(f"{p['name']} (scheduled)", cfg["mode"], cfg)
                    manager.start(jid)
                    db.touch_preset(p["id"])
        except Exception:  # noqa: BLE001
            pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.conn()
    db.mark_orphans()  # jobs interrupted by a crash/close can be resumed
    task = asyncio.create_task(scheduler_loop())
    yield
    task.cancel()


app = FastAPI(title=config.APP_NAME, version=config.VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")
app.include_router(index_router)


@app.get("/")
def index():
    return FileResponse(config.STATIC_DIR / "index.html")


@app.get("/api/meta")
def meta():
    return {"version": config.VERSION, "providers": [p.info() for p in PROVIDERS.values()]}


# ---------- delay ----------
@app.post("/api/delay/preview")
def delay_preview(payload: dict = Body(...)):
    c = normalize_delay(payload)
    s = safety(c)
    return {"ranges": wait_ranges(c), "text": describe_ranges(c), "level": s["level"], "warn": s["warn"],
            "min": s["min"], "max": s["max"], "floor": c["floor"],
            "samples": [round(calc_wait(c), 2) for _ in range(30)]}


# ---------- robots ----------
@app.post("/api/robots")
async def robots_check(payload: dict = Body(...)):
    if not (payload.get("url") or "").strip():
        raise HTTPException(400, "url_required")
    url = normalize_url(payload["url"])
    gw = RequestGateway({"base": 0, "variation": False, "floor": 0}, JobControl(),
                        user_agent=config.USER_AGENT, retries=0, timeout=10)
    try:
        resp = await gw.fetch(origin_of(url) + "/robots.txt")  # single user-initiated request
    finally:
        await gw.aclose()
    return policy_from_response(resp, url, config.USER_AGENT).report(url)


# ---------- keys & providers ----------
@app.get("/api/keys")
def keys():
    return keystore.masked_all(PROVIDERS.keys())


@app.post("/api/keys/{pid}")
def save_key(pid: str, payload: dict = Body(...)):
    if pid not in PROVIDERS or not (payload.get("key") or "").strip():
        raise HTTPException(400, "invalid")
    keystore.set_key(pid, payload["key"])
    return {"ok": True}


@app.delete("/api/keys/{pid}")
def del_key(pid: str):
    keystore.delete_key(pid)
    return {"ok": True}


@app.post("/api/providers/{pid}/test")
async def test_provider(pid: str):
    prov = PROVIDERS.get(pid)
    key = keystore.get_key(pid)
    if not prov or not key:
        return {"ok": False, "message": "api_key_missing"}
    gw = RequestGateway({"base": 0, "variation": False, "floor": 0}, JobControl(), retries=0,
                        timeout=15, secrets=[key])
    try:
        url, params, headers = prov.build({"keyword": "news"}, 1, key)
        r = await gw.fetch(url, params, headers)
    finally:
        await gw.aclose()
    if r is None:
        return {"ok": False, "message": "fetch_failed"}
    if r.status_code in (401, 403):
        return {"ok": False, "message": "auth_failed"}
    if r.status_code >= 400:
        return {"ok": False, "message": f"HTTP {r.status_code}"}
    quota = {k: v for k, v in r.headers.items() if "remaining" in k.lower()}
    return {"ok": True, "quota": quota, "daily_quota": prov.daily_quota}


# ---------- jobs ----------
def _validate(cfg: dict) -> dict:
    cfg = json.loads(json.dumps(cfg or {}))
    mode = cfg.get("mode")
    if mode not in ("domain", "api", "demo", "index"):
        raise HTTPException(400, "invalid_mode")
    if mode == "index":
        ix = cfg.setdefault("index", {})
        try:
            ix["url"] = normalize_url(ix.get("url", ""))
            indexer.build_pages(ix)
            indexer.compile_pattern(ix.get("link_pattern"))
        except ValueError as e:
            raise HTTPException(400, str(e))
    if mode == "domain" and not (cfg.get("source", {}).get("url") or "").strip():
        raise HTTPException(400, "url_required")
    if mode == "api" and cfg.get("api", {}).get("provider") not in PROVIDERS:
        raise HTTPException(400, "invalid_provider")
    lim = cfg.setdefault("limits", {})
    lim["max_articles"] = max(1, min(int(to_float(lim.get("max_articles"), 50)), 100000))
    d = cfg.setdefault("delay", {})
    if mode != "demo":
        d["floor"] = max(1.0, to_float(d.get("floor"), 1.0))
    return cfg


@app.post("/api/jobs/estimate")
def estimate(payload: dict = Body(...)):
    cfg = _validate(payload.get("config", payload))
    n = cfg["limits"]["max_articles"]
    if cfg["mode"] == "api":
        req = math.ceil(n / PROVIDERS[cfg["api"]["provider"]].page_size)
    elif cfg["mode"] == "index":
        req = indexer.page_budget(cfg["index"]) + 1 + n
    elif cfg["mode"] == "demo":
        req = min(n, 48) + 2
    else:
        req = n + 3 + 5 * (max(1, int(to_float(cfg["limits"].get("depth"), 1))) - 1)
    return {"requests": req, "seconds": req * average_wait(cfg.get("delay"))}


@app.post("/api/jobs")
async def create_job(payload: dict = Body(...)):
    cfg = _validate(payload.get("config"))
    name = (payload.get("name") or f"{cfg['mode']}-{time.strftime('%Y%m%d-%H%M')}").strip()[:80]
    jid = db.create_job(name, cfg["mode"], cfg)
    manager.start(jid)
    return {"id": jid}


@app.get("/api/jobs")
def jobs():
    return db.list_jobs()


@app.get("/api/jobs/{job_id}")
def job(job_id: int):
    j = db.get_job(job_id)
    if not j:
        raise HTTPException(404, "not_found")
    j["collected"] = db.count_articles(job_id)
    return j


@app.delete("/api/jobs/{job_id}")
def remove_job(job_id: int):
    r = manager.get(job_id)
    if r and r.live.state not in TERMINAL:
        raise HTTPException(409, "job_active")
    db.delete_job(job_id)
    manager.runners.pop(job_id, None)
    return {"ok": True}


@app.post("/api/jobs/{job_id}/pause")
def pause(job_id: int):
    r = manager.get(job_id)
    if not r or r.live.state != "running":
        raise HTTPException(409, "not_running")
    r.pause()
    return {"ok": True}


@app.post("/api/jobs/{job_id}/resume")
def resume(job_id: int):
    r = manager.get(job_id)
    if r and r.live.state == "paused":
        r.resume()
        return {"ok": True}
    j = db.get_job(job_id)
    if j and j["state"] in ("stopped", "failed") and not (r and r.live.state not in TERMINAL):
        manager.start(job_id)  # continues from saved articles + visited URLs
        return {"ok": True}
    raise HTTPException(409, "cannot_resume")


@app.post("/api/jobs/{job_id}/stop")
def stop(job_id: int):
    r = manager.get(job_id)
    if not r or r.live.state in TERMINAL:
        raise HTTPException(409, "not_active")
    r.stop()
    return {"ok": True}


@app.get("/api/jobs/{job_id}/events")
async def events(job_id: int, request: Request):
    async def gen():
        cursor = 0
        while True:
            if await request.is_disconnected():
                break
            r = manager.get(job_id)
            if r:
                snap, cursor = r.live.snapshot(cursor)
                yield f"data: {json.dumps(snap)}\n\n"
                if snap["state"] in TERMINAL:
                    break
            else:
                j = db.get_job(job_id)
                if not j:
                    break
                snap = {**j["progress"], "id": job_id, "state": j["state"], "message": j["message"],
                        "logs": [], "times": [], "mascot": "celebrate" if j["state"] == "completed" else "sleepy",
                        "countdown": 0, "alert": None}
                yield f"data: {json.dumps(snap)}\n\n"
                break
            await asyncio.sleep(0.5)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ---------- results / export ----------
@app.post("/api/jobs/{job_id}/process")
async def process(job_id: int, payload: dict = Body(default={})):
    try:
        (df, report), _ = await asyncio.to_thread(pipeline.build_dataset, job_id, payload)
    except KeyError:
        raise HTTPException(404, "not_found")
    return {"columns": list(df.columns), "rows": pipeline.preview_rows(df), "report": report}


@app.post("/api/jobs/{job_id}/export")
async def export(job_id: int, payload: dict = Body(...)):
    fmt = payload.get("format", "csv")
    try:
        return await asyncio.to_thread(pipeline.run_export, job_id, payload.get("opts"), fmt)
    except KeyError:
        raise HTTPException(404, "not_found")
    except ImportError as e:
        raise HTTPException(400, f"Missing library for {fmt}: {e}")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/jobs/{job_id}/exports")
def exports(job_id: int):
    return pipeline.list_exports(job_id)


@app.get("/api/exports/{job_id}/{version}/{name}")
def download(job_id: int, version: str, name: str):
    if not (SAFE.match(version) and SAFE.match(name)) or version.startswith(".") or name.startswith("."):
        raise HTTPException(400, "bad_path")
    p = config.EXPORT_DIR / f"job_{job_id}" / version / name
    if not p.is_file():
        raise HTTPException(404, "not_found")
    return FileResponse(p, filename=name)


# ---------- presets ----------
@app.get("/api/presets")
def presets():
    return db.list_presets()


@app.post("/api/presets")
def add_preset(payload: dict = Body(...)):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "name_required")
    return {"id": db.add_preset(name[:80], payload.get("config") or {}, payload.get("schedule"))}


@app.post("/api/presets/{pid}/schedule")
def preset_schedule(pid: int, payload: dict = Body(...)):
    sch = payload.get("schedule")
    db.set_preset_schedule(pid, sch if sch in ("daily", "weekly") else None)
    return {"ok": True}


@app.delete("/api/presets/{pid}")
def del_preset(pid: int):
    db.delete_preset(pid)
    return {"ok": True}


# ---------- config import / export (JSON <-> YAML) ----------
@app.post("/api/config/parse")
def cfg_parse(payload: dict = Body(...)):
    text = payload.get("text", "")
    try:
        data = json.loads(text)
    except ValueError:
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError:
            raise HTTPException(400, "invalid_config")
    if not isinstance(data, dict):
        raise HTTPException(400, "invalid_config")
    return data


@app.post("/api/config/dump")
def cfg_dump(payload: dict = Body(...)):
    cfg, fmt = payload.get("config", {}), payload.get("format", "json")
    text = yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False) if fmt == "yaml" \
        else json.dumps(cfg, ensure_ascii=False, indent=2)
    return {"text": text}