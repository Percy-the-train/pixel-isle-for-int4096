import random
import pandas as pd

COLS = ["article_id", "title", "id", "author", "published", "category",
        "language", "source", "url", "split", "sent_idx", "sentence",
        "sentence_label", "source_file"]


def assign_splits(articles, val=0.1, test=0.1, seed=42):
    rng = random.Random(seed)
    by_cat = {}
    for aid, cat in articles:
        by_cat.setdefault(cat if cat else "other", []).append(aid)
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
    new = new[~new.url.astype(str).isin(base_urls)].copy()
    content_first = {}
    for aid, g in new.groupby("article_id"):
        h = " ".join(g.sort_values("sent_idx").sentence)
        if h not in content_first:
            content_first[h] = aid
    keep = set(content_first.values())
    new = new[new.article_id.isin(keep)].copy()
    arts = [(int(aid), g.category.iloc[0]) for aid, g in new.groupby("article_id")]
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
    new_src = out.source_file.astype(str) != "labeled_sentences(10_29).csv"
    print("new rows per category:")
    print(out[new_src].category.value_counts().to_dict())


if __name__ == "__main__":
    main()
