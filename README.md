# Pixel Isle — INT4096

A pixel-art detective game powered by real daily news, turned into playable murder-mystery clues by a trained NLP model.

## The Whole Flow

```
┌─────────────────────┐        ┌──────────────────────────────┐        ┌─────────────────────┐
│  PART 2             │        │  best model picks key        │        │  PART 1             │
│  news crawler       │ ───►   │  sentences from today's      │ ───►   │  Pixel Isle         │
│  (NLP pipeline)     │        │  BBC story                   │        │  detective game     │
└─────────────────────┘        └──────────────────────────────┘        └─────────────────────┘
```

1. **Collect**: the crawler pulls today's real news from public RSS feeds (BBC, CNN, The Guardian, ...).
2. **Label & train**: sentences are labeled `0 filler / 1 key / 2 evidence`, three models are trained and compared, the best one wins.
3. **Generate clues**: the best model extracts the key sentences of one daily BBC news story, and they are rewritten as in-game clues — coherent with each other and grounded in the game's fiction (a victim has died).
4. **Play**: the clues are placed in the game world; the player walks around, inspects objects, collects clues, and submits a conclusion on *why the victim died*.

---

## Part 1 — The Detective Game

Top-down pixel adventure where you play the detective.

| File | What it is |
|---|---|
| `index.html` | Landing page (Play / Edit links) |
| `play.html` | The detective game: two scenes, NPC dialogue, inspect objects for clues, "Explain the death" answer modal |
| `game.js` | Shared engine (tiles, sprites, scenes, NPCs, storage) |
| `edit.html` | Tile/room editor |
| `sprite-editor.html` | Sprite editor |

**Status:** movement, scenes, NPC dialogue, clue-inspection mechanics, and the answer modal are in place. **Missing:** real clue content — clues currently show "Clue details are coming soon" (this is the merge point with Part 2).

**Run:** open `index.html` in a browser (no build step).

## Part 2 — News Crawler Models (`news crawler/`)

An NLP pipeline that crawls news and learns to rank how important each sentence is.

| File | What it is |
|---|---|
| `fetch_news.py` | Pulls articles from 30+ RSS feeds, cleans + splits sentences → `raw_new_articles.csv` |
| `label_news.py` | Labels every sentence 0/1/2 via DeepSeek (same prompt as `news_labeler.html`), resume-able → `labeled_new.csv` |
| `merge_data.py` | Merges into one dataset with 80/10/10 article-level splits → `data_full.csv` (67,647 rows, 1,322 articles, 9 categories) |
| `app.py` | Streamlit UI: single-model training tab + **three-model comparison tab** (charts + methodology infographic) |
| `train_common.py` | Shared training code for all three methods |
| `compare_tab.py` | Comparison tab: fixed hyperparameters, one seed, fair benchmark |
| `train.py` / `train_lstm.py` / `train_lstm_tok.py` | Standalone training scripts for each method |
| `news_labeler.html` / `merger.html.html` | Browser tools: AI labeling, CSV/JSON merging |
| `tests/` | Pipeline tests (`python -m pytest tests/ -v`) |

### The three methods compared (on `data_full.csv`, seed 42)

| Method | test macro-F1 | key-F1 | time | params |
|---|---|---|---|---|
| LSTM + self-built vocab | 0.709 | 0.543 | 10 min | 5.2M |
| LSTM + RoBERTa tokenizer | 0.736 | 0.552 | 9 min | 6.7M |
| **DistilRoBERTa fine-tune** | **0.798** | **0.660** | 26 min | 82.1M |

**Best model: DistilRoBERTa fine-tune** — also leads in binary F1 (0.887) and top-3 key-sentence precision (0.706). Results live in `compare_results.csv`.

**Run:**
```
py -m venv venv
venv\Scripts\activate
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install transformers datasets streamlit scikit-learn feedparser trafilatura requests pytest
streamlit run app.py
```

## The Merge (in progress)

- [ ] Save the best model (DistilRoBERTa) and an inference script that scores every sentence of a given news article
- [ ] Fetch one daily BBC story, keep the top-scored key sentences
- [ ] Rewrite those sentences as coherent in-game clues (murder-mystery framing, grounded in the game's fiction)
- [ ] Feed clues into `play.html` / `game.js` so each playthrough is built from a real news story

See `docs/superpowers/` for design + implementation plans.
