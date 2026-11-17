import json

import pandas as pd
import pytest

from app.exporter import export_dataset


@pytest.fixture
def df():
    return pd.DataFrame({
        "id": range(1, 11),
        "title": [f"標題 {i}" for i in range(10)],
        "text": [f"text {i}" for i in range(10)],
        "split": ["train"] * 8 + ["val", "test"],
    })


def test_csv_keeps_chinese(tmp_path, df):
    files = export_dataset(df, tmp_path, "My Set", "csv")
    back = pd.read_csv(tmp_path / files[0], encoding="utf-8-sig")
    assert back["title"][0] == "標題 0" and len(back) == 10


def test_json_and_jsonl(tmp_path, df):
    f_json = export_dataset(df, tmp_path, "a", "json")[0]
    assert len(json.loads((tmp_path / f_json).read_text(encoding="utf-8"))) == 10
    f_jsonl = export_dataset(df, tmp_path, "b", "jsonl")[0]
    lines = (tmp_path / f_jsonl).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 10 and json.loads(lines[0])["title"] == "標題 0"


def test_split_files_and_report(tmp_path, df):
    files = export_dataset(df, tmp_path, "set", "csv", report={"final": 10})
    assert {"set.csv", "set_train.csv", "set_val.csv", "set_test.csv", "set_report.json"} <= set(files)
    assert len(pd.read_csv(tmp_path / "set_train.csv", encoding="utf-8-sig")) == 8


def test_unsupported_format_raises(tmp_path, df):
    with pytest.raises(ValueError):
        export_dataset(df, tmp_path, "x", "pdf")


def test_unsafe_name_is_sanitised(tmp_path, df):
    files = export_dataset(df, tmp_path, "../evil name", "csv")
    assert files[0] == "evil_name.csv" and (tmp_path / files[0]).exists()