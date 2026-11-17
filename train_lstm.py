import re, random, numpy as np, pandas as pd, torch, torch.nn as nn
from collections import Counter
from sklearn.metrics import f1_score, classification_report, confusion_matrix

CSV = "data.csv"
COL = dict(article="article_id", idx="sent_idx", sent="sentence",
           title="title", label="sentence_label", split="split")
START = 1
SEED, EPOCHS, BATCH, MAXLEN = 42, 20, 32, 120

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
dev = "cuda" if torch.cuda.is_available() else "cpu"
print("device:", dev)

df = pd.read_csv(CSV).sort_values([COL["article"], COL["idx"]]).reset_index(drop=True)
df[COL["label"]] = df[COL["label"]].astype(int)
df[COL["label"]] -= df[COL["label"]].min()          # 確保標籤從 0 開始
print(df[COL["split"]].value_counts().to_dict())
print("labels:", df[COL["label"]].value_counts().sort_index().to_dict())

text = [None] * len(df)
for _, g in df.groupby(COL["article"], sort=False):
    pos = g.index.tolist()
    s = g[COL["sent"]].tolist()
    n = len(s)
    for i, ix in enumerate(pos):
        prev = s[i - 1] if i > 0 else ""
        nxt = s[i + 1] if i < n - 1 else ""
        text[ix] = f"{g[COL['title']].iloc[0]} pos{START + i} of{n} {prev} SEP {s[i]} {nxt}"
df["text"] = text

tok = lambda t: re.findall(r"\w+|[^\w\s]", t.lower())[:MAXLEN]
tr = df[df[COL["split"]] == "train"]
cnt = Counter(w for t in tr["text"] for w in tok(t))
words = [w for w, c in cnt.items() if c >= 2]
vocab = {w: i + 2 for i, w in enumerate(words)}      # 0=PAD, 1=UNK
print("vocab size:", len(vocab) + 2)

def enc(t):
    ids = [vocab.get(w, 1) for w in tok(t)]
    return ids + [0] * (MAXLEN - len(ids))

def tensors(part):
    d = df[df[COL["split"]] == part]
    X = torch.tensor([enc(t) for t in d["text"]])
    y = torch.tensor(d[COL["label"]].values, dtype=torch.long)
    return X, y

(Xtr, ytr), (Xva, yva), (Xte, yte) = tensors("train"), tensors("val"), tensors("test")
print("sizes:", len(ytr), len(yva), len(yte))

class Net(nn.Module):
    def __init__(s, V):
        super().__init__()
        s.emb = nn.Embedding(V, 128, padding_idx=0)
        s.rnn = nn.LSTM(128, 128, batch_first=True, bidirectional=True)
        s.drop = nn.Dropout(0.4)
        s.out = nn.Linear(256, 3)
    def forward(s, x):
        h, _ = s.rnn(s.drop(s.emb(x)))
        h = h.masked_fill((x == 0).unsqueeze(-1), -1e9).max(1).values
        return s.out(s.drop(h))

model = Net(len(vocab) + 2).to(dev)
cls_count = np.bincount(ytr.numpy(), minlength=3)
w = torch.tensor(len(ytr) / (3 * cls_count), dtype=torch.float).to(dev)
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
print(f"\n=== LSTM (test) macro-F1: {f1_score(yte.numpy(), p, average='macro'):.3f} ===")
print(classification_report(yte.numpy(), p, digits=3,
      target_names=["0 filler", "1 key", "2 evidence"]))
print(confusion_matrix(yte.numpy(), p))