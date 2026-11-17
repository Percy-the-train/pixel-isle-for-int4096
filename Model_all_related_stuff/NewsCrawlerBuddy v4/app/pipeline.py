"""Glue between the database and cleaning/export."""
from __future__ import annotations

import json
import time

from . import config, db
from .cleaning import DEFAULT_FIELDS, clean_records
from .exporter import export_dataset


def merge_opts(job_cfg: dict, opts: dict | None) -> dict:
    opts = opts or {}
    base = {k: json.loads(json.dumps(job_cfg.get(k) or {})) for k in ("cleaning", "label", "split")}
    base["fields"] = list(job_cfg.get("fields") or DEFAULT_FIELDS)
    for k in ("cleaning", "label", "split"):
        base[k].update(opts.get(k) or {})
    if opts.get("fields"):
        base["fields"] = opts["fields"]
    return base


def build_dataset(job_id: int, opts: dict | None):
    job = db.get_job(job_id)
    if not job:
        raise KeyError("job not found")
    merged = merge_opts(job["config"], opts)
    return clean_records(db.job_articles(job_id), merged), job


def preview_rows(df, n: int = 50) -> list[dict]:
    return json.loads(df.head(n).to_json(orient="records", force_ascii=False))


def run_export(job_id: int, opts: dict | None, fmt: str) -> dict:
    (df, report), job = build_dataset(job_id, opts)
    version = time.strftime("%Y%m%d_%H%M%S")
    out = config.EXPORT_DIR / f"job_{job_id}" / version
    files = export_dataset(df, out, job["name"] or f"job_{job_id}", fmt, report)
    return {"version": version, "files": files, "report": report}


def list_exports(job_id: int) -> list[dict]:
    root = config.EXPORT_DIR / f"job_{job_id}"
    if not root.exists():
        return []
    out = []
    for d in sorted((p for p in root.iterdir() if p.is_dir()), reverse=True):
        out.append({"version": d.name, "files": sorted(f.name for f in d.iterdir() if f.is_file())})
    return out