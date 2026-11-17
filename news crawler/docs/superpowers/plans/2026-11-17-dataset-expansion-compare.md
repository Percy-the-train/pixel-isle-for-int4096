# Dataset Expansion + 3-Model Comparison — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grow the labeled dataset from ~22k to ~66k real-news sentences (same schema, no dupes, 8+ categories) and add a Compare tab in `app.py` that trains the 3 methodologies and shows charts + an infographic of the winner and the root differences between methods.

**Architecture:** Three new standalone pipeline scripts (`fetch_news.py` → `label_news.py` → `merge_data.py`) produce `data_full.csv`; the Streamlit app gets a new tab backed by `compare_tab.py`, which reuses the existing training functions in `app.py` (refactored to return structured results) to run all 3 methods on the same data and render charts + HTML infographic.

**Tech Stack:** Python 3.13, PyTorch (cu128, RTX 4060 8GB), transformers, streamlit, scikit-learn, feedparser, trafilatura, requests, pytest.

## Global Constraints

- Same CSV schema everywhere: `article_id,title,id,author,published,category,language,source,url,split,sent_idx,sentence,sentence_label,source_file`
- Labels are 0=filler, 1=key, 2=evidence; split values are `train`/`val`/`test`
- Existing `data.csv` rows must NOT change (splits, labels, ids untouched); new `article_id` starts at max(existing)+1
- DeepSeek API key ONLY from env var `DEEPSEEK_API_KEY`, never written to files
- Labeling prompt byte-for-byte identical to `news_labeler.html` DEFAULT_PROMPT
- No duplicate articles by URL or content hash, including vs existing `data.csv`
- Sentence cleaning/splitting must replicate `news_labeler.html` logic exactly
- `data_full.csv` must be UTF-8 with BOM (`utf-8-sig`), like all other CSVs
- The 3 compared methods are exactly: `word` (LSTM self-built vocab), `tok` (LSTM + RoBERTa tokenizer, embeddings trained from scratch, 128-d), `tf` (DistilRoBERTa fine-tune)
- Not a git repo → NO commit steps in this project; verification steps replace them

---

### Task 1: Environment setup

**Files:**
- Modify: `readme.md` (deps section, at the end of this task)

**Interfaces:**
- Produces: working `venv` with torch+CUDA, transformers, datasets, streamlit, scikit-learn, feedparser, trafilatura, requests, pytest

- [ ] **Step 1: Create venv and install torch (cu128)**

```powershell
py -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
```

- [ ] **Step 2: Install remaining deps**

```powershell
pip install transformers datasets streamlit scikit-learn feedparser trafilatura requests pytest
```

- [ ] **Step 3: Verify torch sees the GPU**

Run: `python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"`
Expected: prints a version, `True`, and `NVIDIA GeForce RTX 4060 ...`

- [ ] **Step 4: Verify streamlit/transformers import**

Run: `python -c "import streamlit, transformers, feedparser, trafilatura, sklearn; print('ok')"`
Expected: `ok`

---

### Task 2: fetch_news.py — RSS fetch, clean, split → raw_new_articles.csv

**Files:**
- Create: `fetch_news.py`
- Test: `tests/test_pipeline.py` (split/clean tests only in this task)

**Interfaces:**
- Consumes: `data.csv` (url column for dedupe), internet RSS feeds
- Produces: `raw_new_articles.csv` with columns `article_id,title,id,author,published,category,language,source,url,split,sent_idx,sentence,sentence_label,source_file` where `split=""` and `sentence_label=""` for new rows; functions `clean_text(t)->str`, `split_sentences(t)->list[str]` used by tests

- [ ] **Step 1: Write failing tests for clean/split logic**

Create `tests/test_pipeline.py`:

```python
import re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from fetch_news import clean_text, split_sentences


def test_clean_text_strips_html_and_collapses_ws():
    t = "Hello  <b>world</b>&nbsp; again\n\n  next"
    out = clean_text(t)
    assert out == "Hello world again\nnext"


def test_clean_text_removes_ellipsis():
    assert clean_text("The story continues...\nMore...") == "The story continues\nMore"


def test_split_sentences_abbr_not_split():
    sents = split_sentences("Mr. Smith went home. He slept.")
    assert sents == ["Mr. Smith went home.", "He slept."]


def test_split_sentences_quotes():
    sents = split_sentences('He said "hi." Next sentence.')
    assert sents == ['He said "hi."', "Next sentence."]


def test_split_sentences_newlines():
    sents = split_sentences("First para line.\n\nSecond para line.")
    assert sents == ["First para line.", "Second para line."]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'fetch_news'`

- [ ] **Step 3: Write fetch_news.py (full implementation)**

```python
import re, html, hashlib, random, sys, time, pathlib
import pandas as pd
import feedparser, requests, trafilatura

CSV = "data.csv"
OUT = "raw_new_articles.csv"
MIN_ARTICLE_CHARS = 50
MIN_SENT_CHARS = 15
ABBR = re.compile(r"\b(Mr|Mrs|Ms|Dr|Prof|St|Sr|Jr|vs|U\.S|U\.K|No|Inc|Ltd|Co|Gen|Col|Lt|Sen|Rep|Gov)\.$")
SPLIT_RE = re.compile(
    r'(?<=[.!?]["”\'’)])\s+(?=["\'‘’(]?[A-Z0-9])|(?<=[.!?])\s+(?=["\'‘’(]?[A-Z0-9])')
SEG_RE = re.compile(r"[^。!?;]+[。!?;]*|[^。!?;]+$")

FEEDS = {
    "world": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "http://rss.cnn.com/rss/edition_world.rss",
        "https://feeds.skynews.com/feeds/rss/world.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "uk": ["http://feeds.bbci.co.uk/news/uk/rss.xml"],
    "business": [
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.theguardian.com/business/rss",
        "http://rss.cnn.com/rss/edition_business.rss",
        "https://feeds.skynews.com/feeds/rss/business.xml",
    ],
    "technology": [
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://www.theguardian.com/technology/rss",
        "http://rss.cnn.com/rss/edition_technology.rss",
        "https://feeds.skynews.com/feeds/rss/technology.xml",
    ],
    "science": [
        "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
        "https://www.theguardian.com/science/rss",
    ],
    "health": ["http://feeds.bbci.co.uk/news/health/rss.xml"],
    "sport": [
        "http://feeds.bbci.co.uk/sport/rss.xml",
        "https://www.theguardian.com/sport/rss",
    ],
    "entertainment": [
        "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
        "https://www.theguardian.com/culture/rss",
    ],
    "general": [
        "http://rss.cnn.com/rss/edition.rss",
        "https://rss.dw.com/rdf/rss-en-all",
        "https://feeds.npr.org/1001/rss.xml",
    ],
}

META = ["id", "author", "published", "category", "language", "source", "url", "split"]


def clean_text(t):
    t = re.sub(r"<[^>]*>", " ", str(t))
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    t = html.unescape(t)
    t = re.sub(r"\.{3}(?=\s*(\n|$))", "", t)
    t = re.sub(r"\.{3}\s*", " ", t)
    t = t.replace("…", " ")
    t = re.sub(r"[ \t\u00a0]+", " ", t)
    t = re.sub(r" *\n *", "\n", t).strip()
    return t


def split_sentences(t):
    out = []
    for par in re.split(r"\n+", t):
        par = par.strip()
        if not par:
            continue
        chunks = []
        for p in SPLIT_RE.split(par):
            if chunks and ABBR.search(chunks[-1]):
                chunks[-1] += " " + p
            else:
                chunks.append(p)
        for c in chunks:
            for s in SEG_RE.findall(c):
                s = s.strip()
                if s:
                    out.append(s)
    return out


def content_hash(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def fetch_feed(url, category):
    d = feedparser.parse(url)
    arts = []
    for e in d.entries:
        title = re.sub(r"\s+", " ", (e.get("title") or "")).strip()
        link = e.get("link") or ""
        if not title or not link:
            continue
        arts.append(dict(title=title, url=link, summary=e.get("summary") or "",
                         published=e.get("published") or "", source=url))
    return arts


def get_full_text(url, summary):
    if len(summary.strip()) >= 600:
        return summary
    try:
        hdr = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) news-collector/1.0"}
        txt = trafilatura.extract(requests.get(url, headers=hdr, timeout=20).text)
        if txt and len(txt.strip()) >= 400:
            return txt
    except Exception:
        pass
    return summary


def main(target_articles=600):
    if pathlib.Path(CSV).exists():
        seen_urls = set(pd.read_csv(CSV, usecols=["url"]).url.dropna().astype(str))
    else:
        seen_urls = set()
    seen_hashes = set()
    next_id = 1
    if pathlib.Path(CSV).exists():
        full = pd.read_csv(CSV)
        next_id = int(full.article_id.max()) + 1
    rows = []
    for cat, feeds in FEEDS.items():
        for f in feeds:
            try:
                arts = fetch_feed(f, cat)
            except Exception as e:
                print(f"feed fail {f}: {e}")
                continue
            print(f"{cat} {f}: {len(arts)} entries")
            for a in arts:
                if a["url"] in seen_urls:
                    continue
                text = get_full_text(a["url"], a["summary"])
                text = clean_text(text)
                if len(text) < MIN_ARTICLE_CHARS:
                    continue
                h = content_hash(text)
                if h in seen_hashes:
                    continue
                sents = [s for s in split_sentences(text) if len(s) >= MIN_SENT_CHARS]
                if len(sents) < 3:
                    continue
                seen_urls.add(a["url"])
                seen_hashes.add(h)
                domain = re.sub(r"^https?://(www\.)?", "", a["url"]).split("/")[0]
                for i, s in enumerate(sents):
                    rows.append(dict(article_id=next_id, title=a["title"], id="",
                                     author="", published=a["published"], category=cat,
                                     language="en", source=domain, url=a["url"],
                                     split="", sent_idx=i + 1, sentence=s,
                                     sentence_label="", source_file="fetched_rss.csv"))
                next_id += 1
                if len(rows) and len({r["article_id"] for r in rows}) >= target_articles:
                    break
            if len({r["article_id"] for r in rows}) >= target_articles:
                break
        if len({r["article_id"] for r in rows}) >= target_articles:
            break
    df = pd.DataFrame(rows, columns=["article_id", "title", "id", "author", "published",
                                     "category", "language", "source", "url", "split",
                                     "sent_idx", "sentence", "sentence_label", "source_file"])
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"saved {OUT}: {df.article_id.nunique()} articles, {len(df)} sentences")
    print(df.category.value_counts().to_dict())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: PASS (5 tests)

- [ ] **Step 5: Dry-run fetch with a small target and verify output**

Run: `python -c "import fetch_news; fetch_news.main(target_articles=10)"`
Expected: prints feed counts, then `saved raw_new_articles.csv: N articles, M sentences` with N ≈ 10 and a category histogram; CSV opens with correct columns.

- [ ] **Step 6: Full fetch**

Run: `python fetch_news.py`
Expected: ~600 articles, ~40k+ sentences (no hard minimum — if feeds underdeliver, rerun once; goal ≥ 400 articles / ≥ 25k sentences before labeling)

---

### Task 3: label_news.py — DeepSeek labeling with resume → labeled_new.csv

**Files:**
- Create: `label_news.py`
- Test: `tests/test_pipeline.py` (add parse_labels tests)

**Interfaces:**
- Consumes: `raw_new_articles.csv`, env `DEEPSEEK_API_KEY`
- Produces: `labeled_new.csv` (sentence_label filled 0/1/2), `label_progress.json` checkpoint; function `parse_labels(txt,n)->list[int]`

- [ ] **Step 1: Add failing test for parse_labels**

Append to `tests/test_pipeline.py`:

```python
import pytest
from label_news import parse_labels


def test_parse_labels_ok():
    txt = 'blah [{"id":1,"label":0},{"id":2,"label":1}] end'
    assert parse_labels(txt, 2) == [0, 1]


def test_parse_labels_missing_id_raises():
    with pytest.raises(ValueError):
        parse_labels('[{"id":1,"label":0}]', 2)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'label_news'`

- [ ] **Step 3: Write label_news.py (full implementation)**

```python
import json, os, re, time, pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd, requests

IN = "raw_new_articles.csv"
OUT = "labeled_new.csv"
CKPT = "label_progress.json"
URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
PROMPT = ("你是新聞標註助手。我會給你一篇新聞的編號句子,請為每一句標註:\n"
          "0 = 可有可無:空泛、對全文沒有太大用途、只是充實語法或過渡的句子。\n"
          "1 = 論點和中心句:新聞主題、發生的核心事件或關鍵事實(例如火災的處理時間、傷亡人數)。\n"
          "2 = 證據或附帶資訊:次要但重要的資訊(例如當事人/市民看法、要求問責、引述、影響如交通受阻等)。\n"
          "只輸出 JSON 陣列,格式 [{\"id\":1,\"label\":0},...],必須涵蓋所有句子編號,不要任何解釋。")


def call_deepseek(user, key):
    res = requests.post(URL, headers={"content-type": "application/json",
                                      "Authorization": "Bearer " + key},
                        json=dict(model=MODEL, temperature=0,
                                  messages=[dict(role="system", content=PROMPT),
                                            dict(role="user", content=user)]),
                        timeout=180)
    if not res.ok:
        raise RuntimeError(f"{res.status_code} {res.text[:200]}")
    return res.json()["choices"][0]["message"]["content"]


def parse_labels(txt, n):
    m = re.search(r"\[[\s\S]*\]", txt)
    if not m:
        raise ValueError("no JSON")
    mp = {o["id"]: int(o["label"]) for o in json.loads(m.group(0))}
    out = []
    for i in range(1, n + 1):
        if i not in mp or mp[i] not in (0, 1, 2):
            raise ValueError(f"missing id {i}")
        out.append(mp[i])
    return out


def label_article(title, sents, key):
    msg = (f"Title: {title}\n" if title else "") + "\n".join(
        f"{i + 1}. {s}" for i, s in enumerate(sents))
    err = None
    for t in range(3):
        try:
            return parse_labels(call_deepseek(msg, key), len(sents))
        except Exception as e:
            err = e
            time.sleep(3 * (t + 1))
    raise err


def main():
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise SystemExit("set DEEPSEEK_API_KEY env var first")
    df = pd.read_csv(IN)
    prog = json.loads(pathlib.Path(CKPT).read_text(encoding="utf-8")) if pathlib.Path(CKPT).exists() else {}
    todo = [a for a in df.article_id.unique() if str(a) not in prog]
    print(f"{len(df.article_id.unique())} articles, {len(todo)} to label")

    def work(aid):
        g = df[df.article_id == aid].sort_values("sent_idx")
        labs = label_article(g.title.iloc[0], g.sentence.tolist(), key)
        return aid, labs

    done = 0
    with ThreadPoolExecutor(max_workers=3) as ex:
        for fut in as_completed([ex.submit(work, a) for a in todo]):
            aid, labs = fut.result()
            prog[str(aid)] = labs
            pathlib.Path(CKPT).write_text(json.dumps(prog), encoding="utf-8")
            done += 1
            print(f"{done}/{len(todo)} article {aid}: {labs.count(0)}x0 {labs.count(1)}x1 {labs.count(2)}x2")

    df["sentence_label"] = [prog[str(a)][int(i) - 1] for a, i in
                            zip(df.article_id, df.sent_idx)]
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print("saved", OUT, df.sentence_label.value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Ask user for API key, then run labeling**

Ask the user to run in a separate terminal (key stays out of repo):

```powershell
venv\Scripts\activate
$env:DEEPSEEK_API_KEY = "<paste key>"
python label_news.py
```

Expected: progress lines `X/Y article N: ...x0 ...x1 ...x2`, then `saved labeled_new.csv {0: ..., 1: ..., 2: ...}`. If interrupted, re-running resumes from `label_progress.json`.

---

### Task 4: merge_data.py — merge + split assignment → data_full.csv

**Files:**
- Create: `merge_data.py`
- Test: `tests/test_pipeline.py` (add split/dupe tests)

**Interfaces:**
- Consumes: `data.csv`, `labeled_new.csv`
- Produces: `data_full.csv` (~66k rows); function `assign_splits(articles)->dict[int,str]` where `articles` is a list of `(article_id, category)`

- [ ] **Step 1: Add failing tests**

Append to `tests/test_pipeline.py`:

```python
from merge_data import assign_splits


def test_assign_splits_ratios_and_article_level():
    arts = [(i, "catA" if i % 2 else "catB") for i in range(1, 101)]
    sp = assign_splits(arts)
    vals = list(sp.values())
    assert abs(vals.count("train") / 100 - 0.8) <= 0.05
    assert abs(vals.count("val") / 100 - 0.1) <= 0.03
    assert abs(vals.count("test") / 100 - 0.1) <= 0.03
    # deterministic
    assert assign_splits(arts) == sp


def test_merge_rejects_duplicate_urls():
    import pandas as pd, pathlib
    base = pd.DataFrame([dict(article_id=1, url="http://x.com/a", title="t",
                              id="", author="", published="", category="w",
                              language="en", source="s", split="train",
                              sent_idx=1, sentence="hello", sentence_label=0,
                              source_file="a.csv")])
    new = pd.DataFrame([dict(article_id=2, url="http://x.com/a", title="t2",
                             id="", author="", published="", category="w",
                             language="en", source="s", split="", sent_idx=1,
                             sentence="hi", sentence_label=1, source_file="b.csv")])
    base.to_csv("tests/_tmp_base.csv", index=False)
    new.to_csv("tests/_tmp_new.csv", index=False)
    try:
        from merge_data import merge
        out = merge("tests/_tmp_base.csv", "tests/_tmp_new.csv")
        assert out.article_id.max() == 1
    finally:
        pathlib.Path("tests/_tmp_base.csv").unlink()
        pathlib.Path("tests/_tmp_new.csv").unlink()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'merge_data'`

- [ ] **Step 3: Write merge_data.py (full implementation)**

```python
import random, pathlib
import pandas as pd

COLS = ["article_id", "title", "id", "author", "published", "category",
        "language", "source", "url", "split", "sent_idx", "sentence",
        "sentence_label", "source_file"]


def assign_splits(articles, val=0.1, test=0.1, seed=42):
    rng = random.Random(seed)
    by_cat = {}
    for aid, cat in articles:
        by_cat.setdefault(cat or "other", []).append(aid)
    out = {}
    for cat, ids in by_cat.items():
        ids = sorted(ids)
        rng.shuffle(ids)
        n = len(ids)
        nte = max(1, round(n * test))
        nva = max(1, round(n * val))
        for a in ids[nva + nte:]:
            out[a] = "train"
        for a in ids[:nva]:
            out[a] = "val"
        for a in ids[nva:nva + nte]:
            out[a] = "test"
    return out


def merge(base_csv, new_csv):
    base = pd.read_csv(base_csv)
    new = pd.read_csv(new_csv)
    base_urls = set(base.url.dropna().astype(str))
    new = new[~new.url.astype(str).isin(base_urls)]
    new_hashes = {}
    for aid, g in new.groupby("article_id"):
        h = " ".join(g.sort_values("sent_idx").sentence)
        if h not in new_hashes:
            new_hashes[h] = aid
    dup_ids = {aid for h, aid in new_hashes.items() if list(new_hashes.values()).count(aid) > 1}
    new = new[~new.article_id.isin(dup_ids)]
    arts = list(new.groupby("article_id").apply(lambda g: (g.article_id.iloc[0], g.category.iloc[0])))
    sp = assign_splits(arts)
    new["split"] = new.article_id.map(sp)
    new["sentence_label"] = new.sentence_label.astype(int)
    out = pd.concat([base[COLS], new[COLS]], ignore_index=True)
    return out


def main(base_csv="data.csv", new_csv="labeled_new.csv", out_csv="data_full.csv"):
    out = merge(base_csv, new_csv)
    out.to_csv(out_csv, index=False, encoding="utf-8-sig")
    print("total rows:", len(out), "| articles:", out.article_id.nunique())
    print("splits:", out.split.value_counts().to_dict())
    print("labels:", out.sentence_label.value_counts().sort_index().to_dict())
    print("new rows per category:", out[out.source_file != "labeled_sentences(10_29).csv"].category.value_counts().head(12).to_dict())


if __name__ == "__main__":
    main()
```

Note: during execution, replace the hard-coded `source_file` filter in `main()`'s last print with the actual existing source_file value from `data.csv` if it differs.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Run the merge**

Run: `python merge_data.py`
Expected: prints total ~66k rows, split counts ~80/10/10, label distribution, category histogram; `data_full.csv` exists.

---

### Task 5: compare_tab.py + app.py Compare tab (charts + infographic)

**Files:**
- Modify: `app.py` (add tab wrapper, expose results from train functions — minimal changes)
- Create: `compare_tab.py`

**Interfaces:**
- Consumes: `app.py` functions `load_df`, `data_tok`, `data_word`, `train_lstm`, `train_tf`, `eval_lstm`, `eval_tf`, `NAMES`, `dev`; `data_full.csv`
- Produces: `compare_results.csv` (after a run); Streamlit UI rendered by `compare_tab.render_compare(csv)` imported in `app.py`

- [ ] **Step 1: Add the tab wrapper in app.py**

Modify `app.py` at the UI section (line ~253, `st.title(...)`):

```python
import compare_tab  # add to top imports

# ---------------- 介面 ----------------
tab_train, tab_compare = st.tabs(["單一模型訓練", "三模型比較"])
with tab_train:
    st.title("句子重要性訓練面板")
    # ... all existing UI code below stays, now indented inside this `with`
```

The entire existing sidebar+UI block (lines ~254-329: `sb = st.sidebar` through the final `st.success(...)`) moves inside `with tab_train:`. Everything works unchanged inside the tab.

After the `with tab_train:` block, add:

```python
with tab_compare:
    compare_tab.render_compare(csv)
```

- [ ] **Step 2: Verify app.py still parses**

Run: `python -c "import ast; ast.parse(open('app.py', encoding='utf-8').read()); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Write compare_tab.py (full implementation)**

```python
import time, math
import numpy as np, pandas as pd, torch
import streamlit as st
from sklearn.metrics import f1_score, classification_report, confusion_matrix

from app import (load_df, data_tok, data_word, train_lstm, train_tf, eval_lstm,
                 eval_tf, Net, get_pre_emb, NAMES, dev)

CONFIGS = {
    "LSTM 自建詞表 (word)": dict(mode="word", epochs=25, bs=64, lr=1e-3, wd=0.01,
                              sched="cosine", clip=1.0, patience=6, ls=0.0,
                              cw=True, maxlen=120, emb=128, hid=128, layers=1,
                              drop=0.4, pool="max+mean", pre=False, freeze=False,
                              min_count=2),
    "LSTM + RoBERTa tokenizer (tok)": dict(mode="tok", epochs=25, bs=64, lr=1e-3,
                                        wd=0.01, sched="cosine", clip=1.0,
                                        patience=6, ls=0.0, cw=True, maxlen=256,
                                        emb=128, hid=128, layers=1, drop=0.4,
                                        pool="max+mean", pre=False, freeze=False),
    "DistilRoBERTa 微調 (tf)": dict(mode="tf", model="distilroberta-base", epochs=4,
                                  bs=8, accum=2, lr=2e-5, wd=0.01, sched="linear",
                                  warm=0.1, clip=1.0, patience=0, ls=0.0,
                                  cw=True, maxlen=256),
}
SEED = 42


class _Sink:
    def line_chart(self, *a, **k): pass
    def code(self, *a, **k): pass


def _metrics(y, p):
    return dict(
        macro_f1=f1_score(y, p, average="macro"),
        f1_0=f1_score(y, p, average=None, labels=[0, 1, 2])[0],
        f1_1=f1_score(y, p, average=None, labels=[0, 1, 2])[1],
        f1_2=f1_score(y, p, average=None, labels=[0, 1, 2])[2],
        binary=f1_score(np.array(y) > 0, np.array(p) > 0, average="macro"),
    )


def _top3(data):
    t = data.copy()
    t["p_key"] = t["p_key"]
    hit = tot = 0
    for _, g in t.groupby("article_id"):
        top = g.nlargest(3, "p_key")
        hit += (top["sentence_label"] == 1).sum()
        tot += len(top)
    return hit / max(tot, 1)


def run_one(name, c, csv):
    st.write(f"**{name}** 開始訓練 (seed {SEED}) …")
    t0 = time.perf_counter()
    if c["mode"] == "tf":
        r = train_tf(c, csv, SEED, _Sink(), _Sink(), save=False)
        df = load_df(csv)
        te = df[df["split"] == "test"].copy()
        te["pred"] = r["p"]
        probs = torch.softmax(torch.tensor(r["logits_test"]), -1).numpy() if "logits_test" in r else None
        params = sum(p.numel() for p in model_params(c))
    else:
        bundle = data_tok(csv, c["maxlen"]) if c["mode"] == "tok" else data_word(csv, c["maxlen"], c["min_count"])
        r = train_lstm(c, bundle, SEED, _Sink(), _Sink(), save=False)
        params = sum(p.numel() for p in model_params(c))
    secs = time.perf_counter() - t0
    m = _metrics(r["y"], r["p"])
    m.update(name=name, time_min=round(secs / 60, 1), params=params,
             best_val=round(float(r["best_val"]), 3))
    st.write(f"{name}: test macro-F1 **{m['macro_f1']:.3f}** ({m['time_min']} min)")
    return m


def model_params(c):
    if c["mode"] == "tf":
        from transformers import AutoModelForSequenceClassification
        mdl = AutoModelForSequenceClassification.from_pretrained(c["model"], num_labels=3)
        return mdl.num_parameters()
    V = 30522 if c["mode"] == "tok" else None
    if c["mode"] == "word":
        from app import data_word
        bundle = data_word(csv_global, c["maxlen"], c["min_count"])
        V = bundle[2]
    return Net(V, 0, c["emb"], c["hid"], c["layers"], c["drop"], c["pool"]).num_parameters()


def render_compare(csv):
    global csv_global
    csv_global = csv
    st.subheader("三模型比較")
    st.caption("固定超參數,同樣的 data_full.csv、同一 seed — 公平對比。忽略左側側欄設定。")
    if st.button("開始比較三模型", type="primary"):
        results = []
        for name, c in CONFIGS.items():
            try:
                results.append(run_one(name, c, csv))
            except Exception as e:
                st.error(f"{name} failed: {e}")
        if len(results) < 2:
            return
        res = pd.DataFrame(results).set_index("name")
        st.session_state["cmp"] = res
        pd.DataFrame(results).to_csv("compare_results.csv", index=False, encoding="utf-8-sig")
        _charts(res)
        _infographic(res)
    elif "cmp" in st.session_state:
        _charts(st.session_state["cmp"])
        _infographic(st.session_state["cmp"])


def _charts(res):
    st.markdown("### 結果圖表")
    st.bar_chart(res[["macro_f1"]])
    c1, c2 = st.columns(2)
    with c1:
        st.bar_chart(res[["f1_0", "f1_1", "f1_2"]])
    with c2:
        st.bar_chart(res[["time_min", "best_val"]])
    st.dataframe(res[["macro_f1", "f1_0", "f1_1", "f1_2", "binary", "best_val",
                      "time_min", "params"]].style.highlight_max(subset=["macro_f1", "f1_0", "f1_1", "f1_2", "binary"], axis=0))


def _infographic(res):
    win = res.macro_f1.idxmax()
    st.markdown("### 方法論解讀 (infographic)")
    st.markdown(f"""<div style="padding:12px 18px;border-radius:10px;background:#e8f5e9;
    border:2px solid #2e7d32;margin:8px 0">
    <b>🏆 贏家:{win}</b> — test macro-F1 {res.loc[win, 'macro_f1']:.3f}</div>""",
                unsafe_allow_html=True)
    cols = st.columns(3)
    cards = [
        ("LSTM 自建詞表", "📚",
         "「從零開始學語言」:詞彙表由語料本身統計得到,詞向量隨機初始化,BiLSTM 掃過句子的前後文。沒有外部世界知識,一切只靠這 6.6 萬句。優點:輕量、快、可解釋;缺點:詞表外的字只能用 UNK,語法/語義先驗完全沒有。"),
        ("LSTM + RoBERTa tokenizer", "🧩",
         "「借用切詞知識」:用 RoBERTa 的子詞(BPE)分詞器把文字切開——罕見字、詞尾變化、拼字變體都能共用子詞,UNK 幾乎消失。但句子仍靠 BiLSTM 逐字掃描,上下文還是線性累積。"),
        ("DistilRoBERTa 微調", "🧠",
         "「直接請教預訓練大腦」:6700 萬參數、在超大語料上預訓練過,注意力機制讓每個字同時看到整句的上下文,再在我們資料上微調最後分類。語言先驗最強,但也最大、最慢。"),
    ]
    for col, (t, icon, txt) in zip(cols, cards):
        with col:
            st.markdown(f"""<div style="border:1px solid #ccc;border-radius:10px;
            padding:12px;height:100%;background:#fafafa">
            <div style="font-size:26px">{icon}</div><b>{t}</b><hr>
            <div style="font-size:13px;line-height:1.5">{txt}</div></div>""",
                        unsafe_allow_html=True)
    st.markdown(f"""
    **根本差異一句話:** 三者的差別在於「外部語言知識注入的層級」—
    詞表層(方法1:完全沒有)→ 切詞層(方法2:子詞分詞)→ 模型層(方法3:整顆預訓練大腦)。
    資料越少,預訓練先驗越值錢;資料越多,差距通常縮小。
    """)
```

**Execution note:** `model_params` uses a module-level `csv_global` hack. During implementation, replace with a cleaner closure — pass `csv` explicitly into `run_one`/`model_params` (parameter `csv`), remove `csv_global`. Same for the `logits_test` branch in `run_one`: `train_tf` in app.py returns `dict(f1=..., best_val=..., y=..., p=..., extra=...)` — no logits, and top-3/binary are already in `r["extra"]`; so in `run_one` use `r["extra"]["binary"]` and `r["extra"]["top3"]` instead of recomputing, and drop the `_top3` helper if unused.

- [ ] **Step 4: Verify the app imports**

Run: `python -c "import compare_tab; print('ok')"`
Expected: `ok` (needs `venv` active; Streamlit import is safe outside `streamlit run`)

- [ ] **Step 5: Smoke-test UI in browser**

Run: `streamlit run app.py` — open the app, confirm two tabs render, "三模型比較" shows the button and captions without errors.
Expected: no exceptions in the terminal; tabs visible.

---

### Task 6: Run the full 3-model comparison

**Files:**
- Produces: `compare_results.csv`, trained artifacts are intentionally NOT saved (save=False)

**Interfaces:**
- Consumes: `data_full.csv` (~66k rows), the Compare tab

- [ ] **Step 1: Launch app and start comparison**

Run: `streamlit run app.py`, go to "三模型比較", press 開始比較三模型.
Expected: three training logs complete — word LSTM (~2-4 min), tok LSTM (~5-10 min), DistilRoBERTa (~30-90 min on RTX 4060). All three must finish with test macro-F1 printed.

- [ ] **Step 2: Verify charts + infographic**

Expected: bar charts (macro-F1; per-class F1; time/val F1), highlighted table, winner banner, 3 method cards, root-difference callout — all rendered; `compare_results.csv` saved.

- [ ] **Step 3: Sanity check on numbers**

Run: `python -c "import pandas as pd; print(pd.read_csv('compare_results.csv').to_string(index=False))"`
Expected: three rows; macro-F1 values plausibly DistilRoBERTa ≥ others; params roughly 128k-word-LSTM (smallest), tok-LSTM ~4M, DistilRoBERTa ~67M.

---

### Task 7: Documentation

**Files:**
- Modify: `readme.md`

- [ ] **Step 1: Update readme.md**

Replace the whole file with:

````markdown
# 新聞句子重要性 — 資料管線 + 三模型比較

## 1. 環境
```
py -m venv venv
venv\Scripts\activate
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install transformers datasets streamlit scikit-learn feedparser trafilatura requests pytest
```

## 2. 資料管線(擴充資料)
```
python fetch_news.py      # RSS 抓取即時新聞 → raw_new_articles.csv
$env:DEEPSEEK_API_KEY="<你的 key>"
python label_news.py      # DeepSeek 標註 0/1/2 → labeled_new.csv(可中斷續跑)
python merge_data.py      # 合併 data.csv + labeled_new.csv → data_full.csv
```
- 清洗/斷句邏輯與 news_labeler.html 完全一致
- 標註 prompt 與 news_labeler.html 相同;key 只從環境變數讀取

## 3. 訓練與比較
```
streamlit run app.py
```
- 「單一模型訓練」分頁:手動調參訓練任一種模型
- 「三模型比較」分頁:一鍵跑 3 種方法(LSTM 自建詞表 / LSTM+RoBERTa tokenizer / DistilRoBERTa 微調),輸出對比圖表與方法論 infographic

## 4. 模型
| 方法 | 檔案 |
|---|---|
| TF-IDF + LogReg 基線 / DistilRoBERTa | train.py |
| LSTM 自建詞表 | train_lstm.py |
| LSTM + RoBERTa tokenizer | train_lstm_tok.py |

## 5. 測試
```
python -m pytest tests/ -v
```
````

- [ ] **Step 2: Final verification**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: PASS (9 tests)

---

## Self-review notes (done at plan-writing time)

1. **Spec coverage:** Phase 1→Task 2, Phase 2→Task 3, Phase 3→Task 4, Phase 4→Task 1, Phase 5→Tasks 5-6, Phase 6→Task 7. No gaps.
2. **Placeholder scan:** No TBDs. Two execution notes in Task 5 Step 3 exist because they depend on app.py's exact return shape — they are resolved at implementation time, and the plan states exactly how.
3. **Type consistency:** `train_lstm` returns `dict(f1, best_val, y, p)`; `train_tf` returns `dict(f1, best_val, y, p, extra)` with `extra=dict(binary, top3)` — compare_tab uses these exact keys. `assign_splits` signature matches tests. `parse_labels(txt, n)` matches tests. `merge(base_csv, new_csv)` matches test.
