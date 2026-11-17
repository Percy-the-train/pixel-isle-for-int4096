# Dataset Expansion + 3-Model Comparison — Design

Date: 2026-11-17
Status: Approved by user ("go for it")

## Goal

1. Enlarge `data.csv` (~22,239 sentences / 294 BBC articles) to ~66k rows using real news from diverse categories and outlets, same schema, no duplication.
2. Train the 3 existing methodologies on the enlarged dataset.
3. Add a "Compare" tab in `app.py` with charts + an infographic showing which methodology wins and the root difference between them.

## Decisions (user-confirmed)

- Data sourcing: auto-fetch from public RSS feeds (no API keys).
- Labeling: automated Python script calling **DeepSeek** (`deepseek-chat`) with the identical prompt used by `news_labeler.html` (0 filler / 1 key / 2 evidence). Key from `DEEPSEEK_API_KEY` env var, never stored.
- Target size: ~66k rows total (~44k new, ~600 articles).
- Deliverable: new Compare tab inside `app.py`.

## Phase 1 — Fetch (`fetch_news.py`)

- Sources: public RSS feeds across 8+ categories: BBC (World, UK, Business, Technology, Science, Health, Sport, Entertainment), The Guardian, CNN, Sky News, Al Jazeera, NPR, DW. Validate feeds at runtime; swap dead ones.
- Full text: use RSS description when complete, otherwise fetch article page and extract main text with `trafilatura`.
- Cleaning + sentence splitting: port the exact logic from `news_labeler.html` (ABBR merge, HTML strip, whitespace collapse, `...` removal, min article/sentence length).
- Dedupe: by URL, by content hash, and against existing `data.csv` URLs. Also dedupe within new batch.
- Output: `raw_new_articles.csv` — columns: `article_id, title, id, author, published, category, language, source, url, split, sent_idx, sentence, sentence_label, source_file`. `article_id` continues after the max in `data.csv`. `sentence_label` empty, `split` empty (assigned in Phase 3).

## Phase 2 — Label (`label_news.py`)

- Read `raw_new_articles.csv`, group by article, send numbered sentence list to DeepSeek with the same system prompt as `news_labeler.html`.
- Robustness: retries with backoff, JSON-array response parsing, resumable checkpoint (`label_progress.json`), small concurrency (2–3).
- Output: `labeled_new.csv` (same schema, `sentence_label` filled 0/1/2). Estimated cost ≈ $0.5–1.

## Phase 3 — Merge (`merge_data.py`)

- Concatenate `data.csv` + `labeled_new.csv` → `data_full.csv`.
- Existing rows keep their split untouched. New articles split 80/10/10 train/val/test at article level, stratified by category (approximate), no sentence leakage.
- Final checks: no duplicate article URLs/content hashes, label + split distribution report.

## Phase 4 — Environment

- `venv`, torch cu128, transformers, datasets, streamlit, scikit-learn, feedparser, trafilatura, requests.

## Phase 5 — Compare tab in `app.py`

- New tab "三模型比較". One button runs all 3 methods on the same `data_full.csv`, same seed(s), fixed default configs:
  1. LSTM + self-built vocab (`mode="word"`)
  2. LSTM + RoBERTa tokenizer/embeddings (`mode="tok"`)
  3. DistilRoBERTa fine-tune (`mode="tf"`)
- Reuse existing `train_lstm` / `train_tf` / `baseline` logic; refactor them to return structured results instead of printing only.
- Charts: test macro-F1, per-class F1 (0 filler / 1 key / 2 evidence), binary F1 (important vs filler), top-3 key-sentence precision, training time, parameter count.
- Infographic: HTML/CSS panels explaining each pipeline and the root difference:
  1. From-scratch embeddings + BiLSTM — learns language from this corpus only.
  2. Pretrained subword embeddings (768-d, frozen) + BiLSTM — borrows general language knowledge, but sequential context only.
  3. Pretrained deep bidirectional transformer fine-tuned — strongest language prior, global attention context, most params.
  - Winner callout tying measured numbers to these methodological differences.
- Standalone scripts (`train.py`, `train_lstm.py`, `train_lstm_tok.py`) stay working with `data_full.csv`.

## Phase 6 — Docs

- Update `readme.md`: data pipeline usage, labeling env var, compare tab.

## Risks

- Dead/truncated RSS feeds → validate and swap sources; use `trafilatura` fallback for full text.
- LLM label noise → spot-check distribution + a few articles in `news_labeler.html`.
- Training time: DistilRoBERTa on ~53k train rows, RTX 4060 8GB, bs=8 → expected well under 2h; LSTM models minutes.

## Out of scope

- Changing the labeling tool or merger tool.
- New model architectures (only the existing 3 methods are compared).
- Deploying/integrating the best model into any downstream app.
