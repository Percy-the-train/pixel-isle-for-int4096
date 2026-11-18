# -*- coding: utf-8 -*-
"""
Generate official comparison charts for the INT4096 PowerPoint from:
  - compare_results.csv  (3-model results)
  - data_full.csv        (dataset stats)
  - history_*.csv        (per-epoch training history, if present)

Output: charts/*.png
Run:   py make_charts.py
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = "compare_results.csv"
DATA = "data_full.csv"
OUT = "charts"
os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({
    "savefig.dpi": 200,
    "font.size": 12,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "legend.fontsize": 10,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#444444",
})

SHORT = {
    "LSTM 自建詞表 (word)": "LSTM (self vocab)",
    "LSTM + RoBERTa tokenizer (tok)": "LSTM (RoBERTa tok)",
    "DistilRoBERTa 微調 (tf)": "DistilRoBERTa",
}
COLOR = {
    "LSTM (self vocab)": "#4c78a8",
    "LSTM (RoBERTa tok)": "#54a24b",
    "DistilRoBERTa": "#d9534f",
}
ORDER = ["LSTM (self vocab)", "LSTM (RoBERTa tok)", "DistilRoBERTa"]


def load():
    d = pd.read_csv(CSV)
    d["model"] = d["name"].map(SHORT)
    d = d.dropna(subset=["model"])
    d["model"] = pd.Categorical(d["model"], categories=ORDER, ordered=True)
    d = d.sort_values("model").reset_index(drop=True)
    return d


def bar(d, col, title, ylabel, fname):
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    x = np.arange(len(d))
    colors = [COLOR[m] for m in d["model"]]
    bars = ax.bar(x, d[col], color=colors, width=0.55)
    ax.set_xticks(x)
    ax.set_xticklabels(d["model"])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, d[col].max() * 1.16)
    for b, v in zip(bars, d[col]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.006,
                f"{v:.3f}", ha="center", va="bottom", fontsize=11)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight")
    plt.close(fig)


def grouped(d, cols, labels, title, ylabel, fname):
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(len(d))
    n = len(cols)
    w = 0.8 / n
    for i, (c, lab) in enumerate(zip(cols, labels)):
        off = x - w * (n - 1) / 2 + i * w
        ax.bar(off, d[c], w, label=lab, color=[COLOR[m] for m in d["model"]] if n == 1 else None)
    if n == 1:
        pass
    ax.set_xticks(x)
    ax.set_xticklabels(d["model"])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, d[cols].max().max() * 1.16)
    ax.legend(ncol=n, loc="lower right", frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight")
    plt.close(fig)


def grouped_multicolor(d, cols, labels, title, ylabel, fname):
    # each group = model; each bar colored by model but lighter for secondary
    fig, ax = plt.subplots(figsize=(8, 4.8))
    x = np.arange(len(d))
    n = len(cols)
    w = 0.8 / n
    shades = {"LSTM (self vocab)": ["#7fa2cc", "#4c78a8"],
              "LSTM (RoBERTa tok)": ["#86c476", "#54a24b"],
              "DistilRoBERTa": ["#e8908c", "#d9534f"]}
    for j, (c, lab) in enumerate(zip(cols, labels)):
        off = x - w * (n - 1) / 2 + j * w
        cols_color = [shades[m][j % 2] for m in d["model"]]
        ax.bar(off, d[c], w, label=lab, color=cols_color)
    ax.set_xticks(x)
    ax.set_xticklabels(d["model"])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_ylim(0, d[cols].max().max() * 1.16)
    ax.legend(ncol=n, loc="lower right", frameon=False)
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight")
    plt.close(fig)


def radar(d, fname):
    metrics = [("Macro-F1", "macro_f1"), ("Key F1", "f1_1"), ("Evidence F1", "f1_2"),
               ("Binary F1", "binary"), ("Top-3", "top3")]
    labels = [m[0] for m in metrics]
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    for _, row in d.iterrows():
        vals = [row[m[1]] for m in metrics]
        vals += vals[:1]
        ax.plot(angles, vals, linewidth=2.2, label=row["model"], color=COLOR[row["model"]])
        ax.fill(angles, vals, alpha=0.08, color=COLOR[row["model"]])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(0.4, 1.0)
    ax.set_yticks([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    ax.set_yticklabels(["0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "1.0"], fontsize=8)
    ax.set_title("Model comparison (higher is better)", pad=22)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight")
    plt.close(fig)


def scatter(d, fname):
    fig, ax = plt.subplots(figsize=(8, 4.8))
    for _, row in d.iterrows():
        ax.scatter(row["params"], row["macro_f1"], s=100 + row["time_min"] * 8,
                   color=COLOR[row["model"]], alpha=0.9, edgecolors="black", linewidths=0.6)
        ax.annotate(f"{row['model']}\n{row['params']/1e6:.1f}M, {row['time_min']:.0f} min",
                    (row["params"], row["macro_f1"]),
                    xytext=(6, 6), textcoords="offset points", fontsize=10)
    ax.set_xscale("log")
    ax.set_xlabel("Parameters (log scale)")
    ax.set_ylabel("Test macro-F1")
    ax.set_title("Scale vs. performance (bubble = training time)")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight")
    plt.close(fig)


def dataset_chart(fname):
    if not os.path.exists(DATA):
        return
    dd = pd.read_csv(DATA, low_memory=False)
    counts = dd["sentence_label"].value_counts().sort_index()
    names = ["0 filler", "1 key", "2 evidence"]
    colors = ["#9aa5b1", "#f2a33c", "#4c78a8"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2))
    a1.bar([names[i] for i in counts.index], counts.values, color=colors, width=0.55)
    a1.set_title("Label distribution (n = %d sentences)" % len(dd))
    a1.set_ylabel("count")
    for i, v in enumerate(counts.values):
        a1.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=10)
    splits = dd["split"].value_counts()
    a2.bar(splits.index.astype(str), splits.values, color="#54a24b", width=0.5)
    a2.set_title("Train / val / test split")
    a2.set_ylabel("count")
    for i, v in enumerate(splits.values):
        a2.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight")
    plt.close(fig)


def training_progress(fname):
    files = {"LSTM (self vocab)": "history_word.csv",
             "LSTM (RoBERTa tok)": "history_tok.csv",
             "DistilRoBERTa": "history_tf.csv"}
    present = {k: f for k, f in files.items() if os.path.exists(f)}
    if not present:
        print("[skip] no history_*.csv -> training-progress chart not generated "
              "(re-run training with history saving).")
        return False
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, (name, f) in zip(axes, present.items()):
        h = pd.read_csv(f)
        ax.plot(h["epoch"], h["train_loss"], color=COLOR[name], label="train loss")
        ax2 = ax.twinx()
        ax2.plot(h["epoch"], h["val_f1"], color="#e45756", marker="o", label="val F1")
        ax.set_title(name)
        ax.set_xlabel("epoch")
        ax.set_ylabel("train loss")
        ax2.set_ylabel("val macro-F1", color="#e45756")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight")
    plt.close(fig)
    return True


def overview(d):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    x = np.arange(len(d))
    # (0,0) macro F1
    ax = axes[0, 0]
    ax.bar(x, d["macro_f1"], color=[COLOR[m] for m in d["model"]], width=0.55)
    ax.set_xticks(x); ax.set_xticklabels(d["model"])
    ax.set_title("Test macro-F1")
    ax.set_ylim(0, d["macro_f1"].max() * 1.15)
    for b, v in zip(ax.patches, d["macro_f1"]):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.006, f"{v:.3f}", ha="center", fontsize=10)
    # (0,1) per-class
    ax = axes[0, 1]
    w = 0.25
    for j, (c, lab) in enumerate(zip(["f1_0", "f1_1", "f1_2"], ["filler", "key", "evidence"])):
        off = x - w + j * w
        ax.bar(off, d[c], w, label=lab)
    ax.set_xticks(x); ax.set_xticklabels(d["model"])
    ax.set_title("Per-class F1")
    ax.set_ylim(0, d[["f1_0", "f1_1", "f1_2"]].max().max() * 1.15)
    ax.legend(frameon=False, fontsize=9)
    # (1,0) binary + top3
    ax = axes[1, 0]
    w = 0.35
    ax.bar(x - w / 2, d["binary"], w, label="binary F1", color="#54a24b")
    ax.bar(x + w / 2, d["top3"], w, label="top-3 precision", color="#f2a33c")
    ax.set_xticks(x); ax.set_xticklabels(d["model"])
    ax.set_title("Binary F1 & top-3 key precision")
    ax.set_ylim(0, d[["binary", "top3"]].max().max() * 1.15)
    ax.legend(frameon=False, fontsize=9)
    # (1,1) params vs f1
    ax = axes[1, 1]
    for _, row in d.iterrows():
        ax.scatter(row["params"], row["macro_f1"], s=100 + row["time_min"] * 8, color=COLOR[row["model"]],
                   alpha=0.9, edgecolors="black", linewidths=0.6)
        ax.annotate(f"{row['model']} ({row['params']/1e6:.1f}M, {row['time_min']:.0f} min)",
                    (row["params"], row["macro_f1"]), xytext=(6, 6), textcoords="offset points", fontsize=9)
    ax.set_xscale("log")
    ax.set_xlabel("Parameters (log)")
    ax.set_ylabel("macro-F1")
    ax.set_title("Scale vs performance")
    ax.grid(True, which="both", linestyle="--", alpha=0.35)
    fig.suptitle("Sentence-importance model comparison (INT4096)", fontsize=16, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(os.path.join(OUT, "comparison_overview.png"), bbox_inches="tight")
    plt.close(fig)


def confusion_matrices(fname, d):
    """FIG.04 — test-set confusion matrices for the three neural models."""
    from sklearn.metrics import confusion_matrix
    files = {"LSTM (self vocab)": "preds_word.csv",
             "LSTM (RoBERTa tok)": "preds_tok.csv",
             "DistilRoBERTa": "preds_tf.csv"}
    present = {k: f for k, f in files.items() if os.path.exists(f)}
    if not present:
        print("[skip] no preds_*.csv -> confusion-matrix chart not generated "
              "(re-run training that saves predictions).")
        return False
    fig, axes = plt.subplots(1, len(present), figsize=(5.2 * len(present), 4.4))
    if len(present) == 1:
        axes = [axes]
    class_names = ["filler", "key", "evidence"]
    for ax, (name, f) in zip(axes, present.items()):
        p = pd.read_csv(f)
        cm = confusion_matrix(p["true"], p["pred"], labels=[0, 1, 2])
        mf1 = d.loc[d["model"] == name, "macro_f1"].iloc[0]
        im = ax.imshow(cm, cmap="Blues", vmin=0)
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(class_names)
        ax.set_yticks([0, 1, 2]); ax.set_yticklabels(class_names)
        ax.set_xlabel("predicted"); ax.set_ylabel("true")
        ax.set_title(f"{name}\n(macro-F1 {mf1:.3f})", fontsize=11)
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center",
                        fontsize=10, color="white" if cm[i, j] > cm.max() / 2 else "#1a1a1a")
    fig.suptitle("Confusion matrices — test set", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(os.path.join(OUT, fname), bbox_inches="tight")
    plt.close(fig)
    return True


def main():
    d = load()
    win = d.loc[d["macro_f1"].idxmax(), "model"]
    print("models compared:", len(d))
    print("winner:", win, f"(macro-F1 {d.loc[d['model'] == win, 'macro_f1'].iloc[0]:.3f})")
    bar(d, "macro_f1", "Test macro-F1 by model (higher is better)", "macro-F1", "macro_f1.png")
    grouped_multicolor(d, ["f1_0", "f1_1", "f1_2"], ["filler (0)", "key (1)", "evidence (2)"],
                       "Per-class F1 by model", "F1", "per_class_f1.png")
    grouped_multicolor(d, ["binary", "top3"], ["binary F1", "top-3 key precision"],
                       "Binary F1 & top-3 key-sentence precision", "score", "binary_top3.png")
    scatter(d, "params_vs_f1.png")
    radar(d, "radar.png")
    dataset_chart("dataset_distribution.png")
    training_progress("training_progress.png")
    confusion_matrices("neural_confusion.png", d)
    overview(d)
    print("charts written to", OUT)


if __name__ == "__main__":
    main()
