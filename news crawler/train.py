import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import inspect, math
import numpy as np, pandas as pd, torch
from datasets import Dataset
from transformers import (AutoTokenizer, AutoModelForSequenceClassification,
                          TrainingArguments, Trainer, set_seed)
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

CSV = "labeled_sentences-10_31.csv"
MODEL = "distilroberta-base"      # 跑通後可改 "roberta-base"
MAXLEN, EPOCHS, SEED = 256, 4, 42
BS, ACCUM = 8, 2
set_seed(SEED)
use_gpu = torch.cuda.is_available()
print("GPU:", torch.cuda.get_device_name(0) if use_gpu else "none (CPU)")

# ---------- 資料 ----------
df = pd.read_csv(CSV).dropna(subset=["sentence", "sentence_label"])
df = df.sort_values(["article_id", "sent_idx"]).reset_index(drop=True)
df["n"] = df.groupby("article_id").sent_idx.transform("max")
df["prev"] = df.groupby("article_id").sentence.shift(1).fillna("")
df["next"] = df.groupby("article_id").sentence.shift(-1).fillna("")
df["a"] = (df.title.fillna("") + " | pos " + df.sent_idx.astype(str)
           + "/" + df.n.astype(str) + " | " + df.prev)
df["b"] = df.sentence + " | " + df.next
df["label"] = df.sentence_label.astype(int)
parts = {s: df[df.split == s].reset_index(drop=True) for s in ["train", "val", "test"]}
print({k: len(v) for k, v in parts.items()})

# ---------- 基線 ----------
vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
Xtr = vec.fit_transform(parts["train"].sentence)
lr = LogisticRegression(max_iter=2000, class_weight="balanced").fit(Xtr, parts["train"].label)
bp = lr.predict(vec.transform(parts["test"].sentence))
print("\n=== BASELINE (test) macro-F1: %.3f ===" % f1_score(parts["test"].label, bp, average="macro"))

# ---------- Transformer ----------
tok = AutoTokenizer.from_pretrained(MODEL)
def enc(x): return tok(x["a"], x["b"], truncation=True, max_length=MAXLEN)
sets = {k: Dataset.from_pandas(v[["a", "b", "label"]]).map(enc, batched=True, remove_columns=["a", "b"])
        for k, v in parts.items()}

w = compute_class_weight("balanced", classes=np.array([0, 1, 2]), y=parts["train"].label)
w = torch.tensor(w, dtype=torch.float)

class WTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kw):
        labels = inputs.pop("labels")
        out = model(**inputs)
        loss = torch.nn.functional.cross_entropy(out.logits, labels, weight=w.to(out.logits.device))
        return (loss, out) if return_outputs else loss

def metrics(p):
    return {"macro_f1": f1_score(p.label_ids, p.predictions.argmax(-1), average="macro")}

model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=3)

steps_per_epoch = math.ceil(len(parts["train"]) / (BS * ACCUM))
warmup = int(0.1 * steps_per_epoch * EPOCHS)

kw = dict(output_dir="out", num_train_epochs=EPOCHS,
          per_device_train_batch_size=BS, gradient_accumulation_steps=ACCUM,
          per_device_eval_batch_size=16, learning_rate=2e-5, weight_decay=0.01,
          warmup_steps=warmup, fp16=use_gpu, save_strategy="epoch",
          load_best_model_at_end=True, metric_for_best_model="macro_f1",
          save_total_limit=2, report_to="none", seed=SEED)
sig = inspect.signature(TrainingArguments.__init__).parameters
kw["eval_strategy" if "eval_strategy" in sig else "evaluation_strategy"] = "epoch"
kw = {k: v for k, v in kw.items() if k in sig}

tk = "processing_class" if "processing_class" in inspect.signature(Trainer.__init__).parameters else "tokenizer"
trainer = WTrainer(model=model, args=TrainingArguments(**kw),
                   train_dataset=sets["train"], eval_dataset=sets["val"],
                   compute_metrics=metrics, **{tk: tok})
trainer.train()

# ---------- 測試集評估 ----------
pred = trainer.predict(sets["test"])
logits = pred.predictions
yp, yt = logits.argmax(-1), pred.label_ids
print("\n=== TRANSFORMER (test) macro-F1: %.3f ===" % f1_score(yt, yp, average="macro"))
print(classification_report(yt, yp, digits=3, target_names=["0 filler", "1 key", "2 evidence"]))
print(confusion_matrix(yt, yp))
print("binary macro-F1 (important vs filler):", round(f1_score(yt > 0, yp > 0, average="macro"), 3))

prob = torch.softmax(torch.tensor(logits), -1).numpy()
t = parts["test"].copy()
t["pred"] = yp
t["p_key"] = prob[:, 1]
hit = tot = 0
for _, g in t.groupby("article_id"):
    top = g.nlargest(3, "p_key")
    hit += (top.label == 1).sum()
    tot += len(top)
print("top-3 per article precision for key sentences: %.3f" % (hit / tot))

# ---------- 儲存 ----------
t.drop(columns=["a", "b", "prev", "next"]).to_csv("test_predictions.csv", index=False, encoding="utf-8-sig")
trainer.save_model("my_model")
tok.save_pretrained("my_model")
print("saved: my_model/ and test_predictions.csv")