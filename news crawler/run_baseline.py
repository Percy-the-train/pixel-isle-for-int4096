# -*- coding: utf-8 -*-
"""Run the TF-IDF + Logistic Regression baseline on data_full.csv,
save metrics into compare_results.csv, and export a confusion-matrix PNG."""
import os, time
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, confusion_matrix
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

COL = dict(article="article_id", idx="sent_idx", sent="sentence",
           title="title", label="sentence_label", split="split")
CSV = "data_full.csv"
OUT = "charts"
os.makedirs(OUT, exist_ok=True)

df = pd.read_csv(CSV, low_memory=False).dropna(subset=[COL["sent"], COL["label"]])
df[COL["label"]] = df[COL["label"]].astype(int)
df[COL["label"]] -= df[COL["label"]].min()

tr = df[df[COL["split"]] == "train"]
va = df[df[COL["split"]] == "val"]
te = df[df[COL["split"]] == "test"]

t0 = time.time()
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
Xtr = vec.fit_transform(tr[COL["sent"]])
lr = LogisticRegression(max_iter=2000, class_weight="balanced").fit(Xtr, tr[COL["label"]].values)

Xva = vec.transform(va[COL["sent"]])
val_pred = lr.predict(Xva)
val_f1 = f1_score(va[COL["label"]].values, val_pred, average="macro")

Xte = vec.transform(te[COL["sent"]])
yp = lr.predict(Xte)
yt = te[COL["label"]].values
secs = time.time() - t0

per = f1_score(yt, yp, average=None, labels=[0, 1, 2])
macro = f1_score(yt, yp, average="macro")
binary = f1_score(yt > 0, yp > 0, average="macro")

prob = lr.predict_proba(Xte)
te2 = te.copy()
te2["p_key"] = prob[:, 1]
hit = tot = 0
for _, g in te2.groupby(COL["article"]):
    top = g.nlargest(3, "p_key")
    hit += (top[COL["label"]] == 1).sum()
    tot += len(top)
top3 = hit / max(tot, 1)

params = len(vec.get_feature_names_out()) * 3 + 3

row = dict(name="TF-IDF + Logistic Regression (baseline)",
           macro_f1=round(float(macro), 4), f1_0=round(float(per[0]), 4),
           f1_1=round(float(per[1]), 4), f1_2=round(float(per[2]), 4),
           binary=round(float(binary), 4), top3=round(float(top3), 4),
           best_val=round(float(val_f1), 4), time_min=round(secs / 60, 2),
           params=int(params))
print("baseline:", row)

res = pd.read_csv("compare_results.csv")
res = res[~res["name"].str.contains("TF-IDF", na=False)]
res = pd.concat([res, pd.DataFrame([row])], ignore_index=True)
res.to_csv("compare_results.csv", index=False, encoding="utf-8-sig")
print("updated compare_results.csv")

cm = confusion_matrix(yt, yp, labels=[0, 1, 2])
fig, ax = plt.subplots(figsize=(5.2, 4.6))
im = ax.imshow(cm, cmap="YlGnBu", interpolation="nearest")
ax.set_xticks([0, 1, 2]); ax.set_yticks([0, 1, 2])
ax.set_xticklabels(["0 filler", "1 key", "2 evidence"])
ax.set_yticklabels(["0 filler", "1 key", "2 evidence"])
ax.set_xlabel("Predicted")
ax.set_ylabel("True")
ax.set_title("Confusion matrix — TF-IDF + Logistic Regression (test)")
thresh = cm.max() / 2
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center",
                color="white" if cm[i, j] > thresh else "black", fontsize=13)
fig.colorbar(im, ax=ax, fraction=0.046)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "confusion_matrix.png"), bbox_inches="tight")
plt.close(fig)
print("saved charts/confusion_matrix.png")
