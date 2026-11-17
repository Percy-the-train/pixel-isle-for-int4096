"""Dataset export: CSV / JSON / JSONL (+ Excel / Parquet if libraries exist)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

EXT = {"csv": "csv", "json": "json", "jsonl": "jsonl", "xlsx": "xlsx", "parquet": "parquet"}


def write_df(df: pd.DataFrame, path: Path, fmt: str) -> None:
    if fmt == "csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")  # BOM so Excel shows Chinese correctly
    elif fmt == "json":
        df.to_json(path, orient="records", force_ascii=False, indent=2)
    elif fmt == "jsonl":
        df.to_json(path, orient="records", lines=True, force_ascii=False)
    elif fmt == "xlsx":
        df.to_excel(path, index=False)
    elif fmt == "parquet":
        df.to_parquet(path, index=False)
    else:
        raise ValueError(f"unsupported format: {fmt}")


def export_dataset(df: pd.DataFrame, out_dir: Path, name: str, fmt: str,
                   report: dict | None = None) -> list[str]:
    if fmt not in EXT:
        raise ValueError(f"unsupported format: {fmt}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = re.sub(r"[^\w\-]+", "_", name).strip("_") or "dataset"
    files = [f"{base}.{EXT[fmt]}"]
    write_df(df, out_dir / files[0], fmt)
    if "split" in df.columns:
        for s in ("train", "val", "test"):
            part = df[df["split"] == s]
            if len(part):
                fn = f"{base}_{s}.{EXT[fmt]}"
                write_df(part, out_dir / fn, fmt)
                files.append(fn)
    if report is not None:
        fn = f"{base}_report.json"
        (out_dir / fn).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        files.append(fn)
    return files