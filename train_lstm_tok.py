import random, numpy as np, pandas as pd, torch, torch.nn as nn
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from transformers import AutoTokenizer

CSV = "data.csv"
COL = dict(article="article_id", idx="sent_idx", sent="sentence",
           title="title", label="sentence_label", split="split")
START = 1
SEED, EPOCHS, BATCH, MAXLEN = 42, 20, 32, 256

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", dev)

df = pd.read_csv(CSV).sort_values([COL["article"], COL["idx"]]).reset_index(drop=True)
df[COL["label"]] = df[COL["label"]].astype(int)
df[COL["label"]] -= df[COL["label"]].min()
print(df[COL["split"]].value_counts().to_dict())
print("labels:", df[COL["label"]].value_counts().sort_index().to_dict())

text = [None] * len(df)
for _, g in df.groupby(COL["article"], sort=False):
    pos, s, n = g.index.tolist(), g[COL["sent"]].tolist(), len(g)
    title = g[COL["title"]].iloc[0]
    for i, ix in enumerate(pos):
        prev = s[i - 1] if i > 0 else ""
        nxt = s[i + 1] if i < n - 1 else ""
        text[ix] = f"{title} pos{START + i} of{n} {prev} SEP {s[i]} {nxt}"
df["text"] = text

tk = AutoTokenizer.from_pretrained("distilroberta-base")
PAD = tk.pad_token_id
print("vocab size:", len(tk), " pad id:", PAD)

def tensors(split):
    d = df[df[COL["split"]] == split]
    e = tk(d["text"].tolist(), truncation=True, max_length=MAXLEN,
           padding="max_length", return_tensors="pt")
    return e["input_ids"], torch.tensor(d[COL["label"]].values, dtype=torch.long)

(Xtr, ytr), (Xva, yva), (Xte, yte) = tensors("train"), tensors("val"), tensors("test")
print("sizes:", len(ytr), len(yva), len(yte))
print("example decoded:", tk.decode(Xtr[0], skip_special_tokens=True)[:200])

class Net(nn.Module):
    def __init__(s, V, pad):
        super().__init__()
        s.pad = pad
        s.emb = nn.Embedding(V, 128, padding_idx=pad)
        s.rnn = nn.LSTM(128, 128, batch_first=True, bidirectional=True)
        s.drop = nn.Dropout(0.4)
        s.out = nn.Linear(256, 3)
    def forward(s, x):
        h, _ = s.rnn(s.drop(s.emb(x)))
        h = h.masked_fill((x == s.pad).unsqueeze(-1), -1e9).max(1).values
        return s.out(s.drop(h))

model = Net(len(tk), PAD).to(dev)
w = torch.tensor(len(ytr) / (3 * np.bincount(ytr.numpy(), minlength=3)),
                 dtype=torch.float).to(dev)
lossf = nn.CrossEntropyLoss(weight=w)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)

def predict(X):
    model.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(X), 256):
            out.append(model(X[i:i + 256].to(dev)).argmax(-1).cpu())
    return torch.cat(out).numpy()

best, state = -1, None
for ep in range(1, EPOCHS + 1):
    model.train()
    perm = torch.randperm(len(Xtr))
    for i in range(0, len(perm), BATCH):
        b = perm[i:i + BATCH]
        opt.zero_grad()
        lossf(model(Xtr[b].to(dev)), ytr[b].to(dev)).backward()
        opt.step()
    f1 = f1_score(yva.numpy(), predict(Xva), average="macro")
    print(f"epoch {ep:2d}  val macro-F1 {f1:.3f}")
    if f1 > best:
        best, state = f1, {k: v.clone() for k, v in model.state_dict().items()}

model.load_state_dict(state)
p = predict(Xte)
print(f"\n=== LSTM + tokenizer (test) macro-F1: {f1_score(yte.numpy(), p, average='macro'):.3f} ===")
print(classification_report(yte.numpy(), p, digits=3,
      target_names=["0 filler", "1 key", "2 evidence"]))
print(confusion_matrix(yte.numpy(), p))