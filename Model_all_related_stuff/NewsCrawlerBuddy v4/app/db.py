"""Tiny SQLite layer (jobs, articles, visited URLs, presets, settings)."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from typing import Any

from . import config

_lock = threading.RLock()
_conn: sqlite3.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, mode TEXT, config TEXT,
  state TEXT, progress TEXT, message TEXT, created REAL, updated REAL);
CREATE TABLE IF NOT EXISTS articles(
  id INTEGER PRIMARY KEY AUTOINCREMENT, job_id INTEGER, url TEXT,
  canonical_url TEXT, content_hash TEXT, data TEXT,
  UNIQUE(job_id, canonical_url));
CREATE INDEX IF NOT EXISTS idx_art_job ON articles(job_id);
CREATE TABLE IF NOT EXISTS visited(job_id INTEGER, url TEXT, PRIMARY KEY(job_id, url));
CREATE TABLE IF NOT EXISTS presets(
  id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, config TEXT,
  schedule TEXT, last_run REAL, created REAL);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
"""


def conn() -> sqlite3.Connection:
    global _conn
    with _lock:
        if _conn is None:
            config.ensure_dirs()
            _conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
            _conn.row_factory = sqlite3.Row
            _conn.execute("PRAGMA journal_mode=WAL")
            _conn.executescript(SCHEMA)
            _conn.commit()
        return _conn


def execute(sql: str, params: tuple = ()) -> int:
    with _lock:
        cur = conn().execute(sql, params)
        conn().commit()
        return cur.lastrowid


def query(sql: str, params: tuple = ()) -> list[dict]:
    with _lock:
        return [dict(r) for r in conn().execute(sql, params).fetchall()]


def _dec(job: dict) -> dict:
    job["config"] = json.loads(job.get("config") or "{}")
    job["progress"] = json.loads(job.get("progress") or "{}")
    return job


# ---------- jobs ----------
def create_job(name: str, mode: str, cfg: dict) -> int:
    now = time.time()
    return execute(
        "INSERT INTO jobs(name,mode,config,state,progress,message,created,updated) VALUES(?,?,?,?,?,?,?,?)",
        (name, mode, json.dumps(cfg), "queued", "{}", "", now, now))


def update_job(job_id: int, **fields: Any) -> None:
    fields["updated"] = time.time()
    cols, vals = [], []
    for k, v in fields.items():
        cols.append(f"{k}=?")
        vals.append(json.dumps(v) if isinstance(v, (dict, list)) else v)
    execute(f"UPDATE jobs SET {','.join(cols)} WHERE id=?", (*vals, job_id))


def get_job(job_id: int) -> dict | None:
    rows = query("SELECT * FROM jobs WHERE id=?", (job_id,))
    return _dec(rows[0]) if rows else None


def list_jobs() -> list[dict]:
    rows = query("SELECT j.*, (SELECT COUNT(*) FROM articles a WHERE a.job_id=j.id) AS collected "
                 "FROM jobs j ORDER BY j.id DESC LIMIT 200")
    return [_dec(r) for r in rows]


def delete_job(job_id: int) -> None:
    for tbl in ("articles", "visited"):
        execute(f"DELETE FROM {tbl} WHERE job_id=?", (job_id,))
    execute("DELETE FROM jobs WHERE id=?", (job_id,))


def mark_orphans() -> None:
    execute("UPDATE jobs SET state='stopped', message='interrupted' "
            "WHERE state IN ('queued','running','paused')")


# ---------- articles ----------
def add_article(job_id: int, url: str, canon: str, chash: str | None, data: dict) -> bool:
    with _lock:
        cur = conn().execute(
            "INSERT OR IGNORE INTO articles(job_id,url,canonical_url,content_hash,data) VALUES(?,?,?,?,?)",
            (job_id, url, canon, chash, json.dumps(data, ensure_ascii=False)))
        conn().commit()
        return cur.rowcount == 1


def job_articles(job_id: int) -> list[dict]:
    return [json.loads(r["data"]) for r in
            query("SELECT data FROM articles WHERE job_id=? ORDER BY id", (job_id,))]


def article_keys(job_id: int) -> list[dict]:
    return query("SELECT canonical_url, content_hash FROM articles WHERE job_id=?", (job_id,))


def count_articles(job_id: int) -> int:
    return query("SELECT COUNT(*) AS n FROM articles WHERE job_id=?", (job_id,))[0]["n"]


def mark_visited(job_id: int, url: str) -> None:
    execute("INSERT OR IGNORE INTO visited(job_id,url) VALUES(?,?)", (job_id, url))


def visited_set(job_id: int) -> set[str]:
    return {r["url"] for r in query("SELECT url FROM visited WHERE job_id=?", (job_id,))}


# ---------- presets ----------
def list_presets() -> list[dict]:
    rows = query("SELECT * FROM presets ORDER BY id DESC")
    for r in rows:
        r["config"] = json.loads(r["config"] or "{}")
    return rows


def add_preset(name: str, cfg: dict, schedule: str | None) -> int:
    now = time.time()
    return execute("INSERT INTO presets(name,config,schedule,last_run,created) VALUES(?,?,?,?,?)",
                   (name, json.dumps(cfg), schedule, now, now))


def set_preset_schedule(pid: int, schedule: str | None) -> None:
    execute("UPDATE presets SET schedule=?, last_run=? WHERE id=?", (schedule, time.time(), pid))


def touch_preset(pid: int) -> None:
    execute("UPDATE presets SET last_run=? WHERE id=?", (time.time(), pid))


def delete_preset(pid: int) -> None:
    execute("DELETE FROM presets WHERE id=?", (pid,))


# ---------- settings ----------
def get_setting(key: str) -> str | None:
    rows = query("SELECT value FROM settings WHERE key=?", (key,))
    return rows[0]["value"] if rows else None


def set_setting(key: str, value: str) -> None:
    execute("INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def delete_setting(key: str) -> None:
    execute("DELETE FROM settings WHERE key=?", (key,))