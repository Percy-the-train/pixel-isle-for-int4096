import math, random, numpy as np, pandas as pd, torch, torch.nn as nn, re
from collections import Counter
import streamlit as st
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from transformers import (AutoTokenizer, AutoModel,
                          AutoModelForSequenceClassification)

st.set_page_config(page_title="Sentence Trainer", layout="wide")
COL = dict(article="article_id", idx="sent_idx", sent="sentence",
           title="title", label="sentence_label", split="split")
START = 1
NAMES = ["0 filler", "1 key", "2 evidence"]
dev = "cuda" if torch.cuda.is_available() else "cpu"

# ---------------- 共用資料 ----------------
@st.cache_data
def load_df(csv):
    df = pd.read_csv(csv).dropna(subset=[COL["sent"], COL["label"]])
    df = df.sort_values([COL["article"], COL["idx"]]).reset_index(drop=True)
    df[COL["label"]] = df[COL["label"]].astype(int)
    df[COL["label"]] -= df[COL["label"]].min()
    text = [None] * len(df)
    for _, g in df.groupby(COL["article"], sort=False):
        pos, s, n = g.index.tolist(), g[COL["sent"]].tolist(), len(g)
        title = g[COL["title"]].iloc[0]
        for i, ix in enumerate(pos):
            prev = s[i - 1] if i > 0 else ""
            nxt = s[i + 1] if i < n - 1 else ""
            text[ix] = f"{title} pos{START + i} of{n} {prev} SEP {s[i]} {nxt}"
    df["text"] = text
    return df

@st.cache_resource
def get_tok(name="distilroberta-base"):
    return AutoTokenizer.from_pretrained(name)

@st.cache_resource
def get_pre_emb():
    return AutoModel.from_pretrained("distilroberta-base").embeddings.word_embeddings.weight.detach().clone()

@st.cache_data
def data_tok(csv, maxlen):
    df, tk = load_df(csv), get_tok()
    out = {}
    for sp in ["train", "val", "test"]:
        d = df[df[COL["split"]] == sp]
        e = tk(d["text"].tolist(), truncation=True, max_length=maxlen,
               padding="max_length", return_tensors="pt")
        out[sp] = (e["input_ids"], torch.tensor(d[COL["label"]].values, dtype=torch.long))
    return out, tk.pad_token_id, len(tk)

@st.cache_data
def data_word(csv, maxlen, min_count):
    df = load_df(csv)
    tok = lambda t: re.findall(r"\w+|[^\w\s]", t.lower())[:maxlen]
    tr = df[df[COL["split"]] == "train"]
    cnt = Counter(w for t in tr["text"] for w in tok(t))
    vocab = {w: i + 2 for i, w in enumerate([w for w, c in cnt.items() if c >= min_count])}
    def enc(t):
        ids = [vocab.get(w, 1) for w in tok(t)]
        return ids + [0] * (maxlen - len(ids))
    out = {}
    for sp in ["train", "val", "test"]:
        d = df[df[COL["split"]] == sp]
        out[sp] = (torch.tensor([enc(t) for t in d["text"]]),
                   torch.tensor(d[COL["label"]].values, dtype=torch.long))
    return out, 0, len(vocab) + 2

def log_line(status, text):
    buf = st.session_state.setdefault("live_log", [])
    buf.append(text)
    status.code("\n".join(buf), language="text")

# ---------------- LSTM ----------------
class Net(nn.Module):
    def __init__(s, V, pad, emb_dim, hid, layers, drop, pool, pre=None, freeze=False):
        super().__init__()
        s.pad, s.pool = pad, pool
        s.emb = nn.Embedding(V, emb_dim, padding_idx=pad)
        if pre is not None:
            s.emb.weight.data.copy_(pre); s.emb.weight.requires_grad = not freeze
        s.rnn = nn.LSTM(emb_dim, hid, num_layers=layers, batch_first=True,
                        bidirectional=True, dropout=drop if layers > 1 else 0.0)
        s.drop = nn.Dropout(drop)
        s.out = nn.Linear(2 * hid * (2 if pool == "max+mean" else 1), 3)
    def forward(s, x):
        mask = x != s.pad
        L = int(mask.sum(1).max()); x, mask = x[:, :L], mask[:, :L]
        lens = mask.sum(1).clamp(min=1).cpu()
        e = s.drop(s.emb(x))
        pk = nn.utils.rnn.pack_padded_sequence(e, lens, batch_first=True, enforce_sorted=False)
        h, _ = s.rnn(pk)
        h, _ = nn.utils.rnn.pad_packed_sequence(h, batch_first=True, total_length=L)
        m = mask.unsqueeze(-1)
        mx = h.masked_fill(~m, -1e9).max(1).values
        mn = (h * m).sum(1) / m.sum(1).clamp(min=1)
        z = mx if s.pool == "max" else mn if s.pool == "mean" else torch.cat([mx, mn], -1)
        return s.out(s.drop(z))

def eval_lstm(model, X, y, lossf):
    model.eval(); preds, tot = [], 0.0
    with torch.no_grad():
        for i in range(0, len(X), 256):
            xb, yb = X[i:i+256].to(dev), y[i:i+256].to(dev)
            lo = model(xb); tot += lossf(lo, yb).item() * len(xb)
            preds.append(lo.argmax(-1).cpu())
    return tot / len(X), torch.cat(preds).numpy()

def lr_lambda(c, total, warm):
    def f(step):
        if c["sched"] == "constant": return 1.0
        if step < warm: return (step + 1) / max(1, warm)
        p = (step - warm) / max(1, total - warm)
        return 0.5 * (1 + math.cos(math.pi * p)) if c["sched"] == "cosine" else max(0.0, 1 - p)
    return f

def train_lstm(c, bundle, seed, chart, status, save):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    data, pad, V = bundle
    Xtr, ytr = data["train"]; Xva, yva = data["val"]; Xte, yte = data["test"]
    use_pre = c["pre"] and c["mode"] == "tok"
    model = Net(V, pad, 768 if use_pre else c["emb"], c["hid"], c["layers"], c["drop"],
                c["pool"], get_pre_emb() if use_pre else None, c["freeze"]).to(dev)
    cnt = np.bincount(ytr.numpy(), minlength=3)
    w = torch.tensor(len(ytr) / (3 * cnt), dtype=torch.float).to(dev) if c["cw"] else None
    lossf = nn.CrossEntropyLoss(weight=w, label_smoothing=c["ls"]); plain = nn.CrossEntropyLoss()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],
                            lr=c["lr"], weight_decay=c["wd"])
    total = math.ceil(len(Xtr) / c["bs"]) * c["epochs"]
    sch = torch.optim.lr_scheduler.LambdaLR(opt, lr_lambda(c, total, int(0.1 * total)))
    hist, best, state, bad = [], -1, None, 0
    for ep in range(1, c["epochs"] + 1):
        model.train(); perm = torch.randperm(len(Xtr)); run, nb = 0.0, 0
        for i in range(0, len(perm), c["bs"]):
            b = perm[i:i+c["bs"]]; opt.zero_grad()
            loss = lossf(model(Xtr[b].to(dev)), ytr[b].to(dev)); loss.backward()
            if c["clip"] > 0: nn.utils.clip_grad_norm_(model.parameters(), c["clip"])
            opt.step(); sch.step(); run += loss.item(); nb += 1
        vl, vp = eval_lstm(model, Xva, yva, plain)
        f1 = f1_score(yva.numpy(), vp, average="macro")
        hist.append(dict(epoch=ep, train_loss=run/nb, val_loss=vl, val_f1=f1))
        chart.line_chart(pd.DataFrame(hist).set_index("epoch"))
        log_line(status, f"seed {seed} | epoch {ep}/{c['epochs']} | train {run/nb:.3f} | val loss {vl:.3f} | val F1 {f1:.3f}")
        if f1 > best:
            best, bad = f1, 0; state = {k: v.clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if c["patience"] > 0 and bad >= c["patience"]:
                log_line(status, f"early stop at epoch {ep}"); break
    model.load_state_dict(state)
    _, tp = eval_lstm(model, Xte, yte, plain)
    if save: torch.save(dict(state=state, cfg=c), "lstm_best.pt")
    return dict(f1=f1_score(yte.numpy(), tp, average="macro"), best_val=best, y=yte.numpy(), p=tp)

# ---------------- Transformer ----------------
def tf_batches(ids, labels, bs, tk, shuffle):
    order = np.random.permutation(len(ids)) if shuffle else np.arange(len(ids))
    for i in range(0, len(order), bs):
        ch = order[i:i+bs]
        b = tk.pad({"input_ids": [ids[j] for j in ch]}, return_tensors="pt")
        yield b["input_ids"], b["attention_mask"], torch.tensor(labels[ch])

def eval_tf(model, ids, labels, tk, w):
    model.eval(); logits = []
    with torch.no_grad():
        for x, m, _ in tf_batches(ids, labels, 64, tk, False):
            with torch.autocast("cuda", dtype=torch.float16, enabled=dev == "cuda"):
                logits.append(model(input_ids=x.to(dev), attention_mask=m.to(dev)).logits.float().cpu())
    lg = torch.cat(logits)
    loss = nn.functional.cross_entropy(lg, torch.tensor(labels)).item()
    return loss, lg.numpy()

def train_tf(c, csv, seed, chart, status, save):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    df = load_df(csv).copy()
    g = df.groupby(COL["article"])
    df["n"] = g[COL["idx"]].transform("max")
    df["prev"] = g[COL["sent"]].shift(1).fillna("")
    df["next"] = g[COL["sent"]].shift(-1).fillna("")
    df["a"] = (df[COL["title"]].fillna("") + " | pos " + df[COL["idx"]].astype(str)
               + "/" + df["n"].astype(str) + " | " + df["prev"])
    df["b"] = df[COL["sent"]] + " | " + df["next"]
    parts = {s: df[df[COL["split"]] == s].reset_index(drop=True) for s in ["train", "val", "test"]}
    tk = get_tok(c["model"])
    ids = {s: tk(p["a"].tolist(), p["b"].tolist(), truncation=True, max_length=c["maxlen"])["input_ids"]
           for s, p in parts.items()}
    y = {s: p[COL["label"]].values for s, p in parts.items()}

    model = AutoModelForSequenceClassification.from_pretrained(c["model"], num_labels=3).to(dev)
    cnt = np.bincount(y["train"], minlength=3)
    w = torch.tensor(len(y["train"]) / (3 * cnt), dtype=torch.float).to(dev) if c["cw"] else None
    nd = ["bias", "LayerNorm.weight"]
    groups = [{"params": [p for n, p in model.named_parameters() if not any(k in n for k in nd)],
               "weight_decay": c["wd"]},
              {"params": [p for n, p in model.named_parameters() if any(k in n for k in nd)],
               "weight_decay": 0.0}]
    opt = torch.optim.AdamW(groups, lr=c["lr"])
    steps_ep = math.ceil(math.ceil(len(y["train"]) / c["bs"]) / c["accum"])
    total = steps_ep * c["epochs"]
    sch = torch.optim.lr_scheduler.LambdaLR(opt, lr_lambda(c, total, int(c["warm"] * total)))
    use = dev == "cuda"
    scaler = torch.amp.GradScaler("cuda", enabled=use)
    hist, best, state, bad = [], -1, None, 0
    for ep in range(1, c["epochs"] + 1):
        model.train(); run, nb = 0.0, 0; opt.zero_grad()
        nbat = math.ceil(len(y["train"]) / c["bs"])
        for j, (x, m, lb) in enumerate(tf_batches(ids["train"], y["train"], c["bs"], tk, True)):
            with torch.autocast("cuda", dtype=torch.float16, enabled=use):
                lg = model(input_ids=x.to(dev), attention_mask=m.to(dev)).logits
            loss = nn.functional.cross_entropy(lg.float(), lb.to(dev), weight=w,
                                               label_smoothing=c["ls"])
            scaler.scale(loss / c["accum"]).backward()
            run += loss.item(); nb += 1
            if (j + 1) % c["accum"] == 0 or j == nbat - 1:
                scaler.unscale_(opt)
                if c["clip"] > 0: nn.utils.clip_grad_norm_(model.parameters(), c["clip"])
                scaler.step(opt); scaler.update(); sch.step(); opt.zero_grad()
        vl, vlg = eval_tf(model, ids["val"], y["val"], tk, w)
        f1 = f1_score(y["val"], vlg.argmax(-1), average="macro")
        hist.append(dict(epoch=ep, train_loss=run/nb, val_loss=vl, val_f1=f1))
        chart.line_chart(pd.DataFrame(hist).set_index("epoch"))
        log_line(status, f"seed {seed} | epoch {ep}/{c['epochs']} | train {run/nb:.3f} | val loss {vl:.3f} | val F1 {f1:.3f}")
        if f1 > best:
            best, bad = f1, 0
            state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        else:
            bad += 1
            if c["patience"] > 0 and bad >= c["patience"]:
                log_line(status, f"early stop at epoch {ep}"); break
    model.load_state_dict(state)
    _, lg = eval_tf(model, ids["test"], y["test"], tk, w)
    yp, yt = lg.argmax(-1), y["test"]
    prob = torch.softmax(torch.tensor(lg), -1).numpy()
    t = parts["test"].copy(); t["pred"] = yp; t["p_key"] = prob[:, 1]
    hit = tot = 0
    for _, gg in t.groupby(COL["article"]):
        top = gg.nlargest(3, "p_key"); hit += (top[COL["label"]] == 1).sum(); tot += len(top)
    extra = dict(binary=f1_score(yt > 0, yp > 0, average="macro"), top3=hit / max(tot, 1))
    if save:
        t.drop(columns=["a", "b", "prev", "next"]).to_csv("test_predictions.csv", index=False, encoding="utf-8-sig")
        model.save_pretrained("my_model"); tk.save_pretrained("my_model")
    return dict(f1=f1_score(yt, yp, average="macro"), best_val=best, y=yt, p=yp, extra=extra)

def baseline(csv):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    df = load_df(csv); tr = df[df[COL["split"]] == "train"]; te = df[df[COL["split"]] == "test"]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    lr = LogisticRegression(max_iter=2000, class_weight="balanced").fit(
        vec.fit_transform(tr[COL["sent"]]), tr[COL["label"]])
    return f1_score(te[COL["label"]], lr.predict(vec.transform(te[COL["sent"]])), average="macro")

# ---------------- 介面 ----------------
st.title("句子重要性訓練面板")
sb = st.sidebar
label = sb.radio("模式", ["LSTM + RoBERTa tokenizer", "LSTM 自建詞表", "DistilRoBERTa 微調"])
mode = {"LSTM + RoBERTa tokenizer": "tok", "LSTM 自建詞表": "word", "DistilRoBERTa 微調": "tf"}[label]
csv = sb.text_input("CSV 檔名", "data.csv")
c = dict(mode=mode)
sb.subheader("訓練")
if mode == "tf":
    c.update(model=sb.selectbox("模型", ["distilroberta-base", "roberta-base"]),
             epochs=sb.slider("EPOCHS", 1, 15, 4),
             bs=sb.select_slider("BATCH", [4, 8, 16, 32], 8),
             accum=sb.select_slider("梯度累積", [1, 2, 4, 8], 2),
             lr=sb.select_slider("學習率", [1e-5, 2e-5, 3e-5, 5e-5, 1e-4], 2e-5),
             wd=sb.select_slider("weight decay", [0.0, 0.01, 0.05, 0.1], 0.01),
             sched=sb.selectbox("排程", ["linear", "cosine", "constant"]),
             warm=sb.slider("warmup 比例", 0.0, 0.3, 0.1, 0.05),
             clip=sb.slider("梯度裁剪 (0=關)", 0.0, 5.0, 1.0, 0.5),
             patience=sb.slider("early stopping (0=關)", 0, 6, 0),
             ls=sb.slider("label smoothing", 0.0, 0.2, 0.0, 0.05),
             cw=sb.checkbox("類別權重", True),
             maxlen=sb.select_slider("MAXLEN", [128, 192, 256, 384], 256))
    run_base = sb.checkbox("同時跑 TF-IDF 基線", False)
else:
    c.update(epochs=sb.slider("EPOCHS", 3, 60, 25),
             bs=sb.select_slider("BATCH", [16, 32, 64, 128], 64),
             lr=sb.select_slider("學習率", [1e-4, 3e-4, 5e-4, 1e-3, 2e-3, 3e-3], 1e-3),
             wd=sb.select_slider("weight decay", [0.0, 0.001, 0.01, 0.05, 0.1], 0.01),
             sched=sb.selectbox("排程", ["cosine", "linear", "constant"]),
             clip=sb.slider("梯度裁剪 (0=關)", 0.0, 5.0, 1.0, 0.5),
             patience=sb.slider("early stopping (0=關)", 0, 15, 6),
             ls=sb.slider("label smoothing", 0.0, 0.2, 0.0, 0.05),
             cw=sb.checkbox("類別權重", True))
    sb.subheader("模型")
    c.update(maxlen=sb.select_slider("MAXLEN", [64, 120, 192, 256], 256 if mode == "tok" else 120),
             emb=sb.select_slider("詞向量維度", [64, 128, 256], 128),
             hid=sb.select_slider("LSTM 隱藏維度", [64, 128, 256, 384], 128),
             layers=sb.slider("LSTM 層數", 1, 3, 1),
             drop=sb.slider("dropout", 0.0, 0.7, 0.4, 0.05),
             pool=sb.selectbox("池化", ["max", "mean", "max+mean"], 2))
    if mode == "tok":
        c.update(pre=sb.checkbox("用 distilroberta 詞向量初始化 (768 維)", True),
                 freeze=sb.checkbox("凍結詞向量", False))
    else:
        c.update(pre=False, freeze=False, min_count=sb.slider("最低詞頻", 1, 5, 2))
n_seeds = sb.slider("重複種子數", 1, 5, 1)
seed0 = int(sb.number_input("起始 SEED", 0, 9999, 42))
st.caption(f"device: {dev}")

if st.button("開始訓練", type="primary"):
    if mode == "tok": bundle = data_tok(csv, c["maxlen"])
    elif mode == "word": bundle = data_word(csv, c["maxlen"], c["min_count"])
    if mode != "tf":
        st.write({k: len(v[1]) for k, v in bundle[0].items()}, "vocab:", bundle[2])
    if mode == "tf" and run_base:
        st.write(f"TF-IDF 基線 test macro-F1: {baseline(csv):.3f}")
    chart, status = st.empty(), st.empty()
    st.session_state["live_log"] = []
    res = []
    for k in range(n_seeds):
        s = seed0 + k
        r = train_tf(c, csv, s, chart, status, k == 0) if mode == "tf" \
            else train_lstm(c, bundle, s, chart, status, k == 0)
        res.append(r)
        st.write(f"seed {s}: val {r['best_val']:.3f} / test macro-F1 {r['f1']:.3f}")
    f1s = [r["f1"] for r in res]
    st.metric("測試 macro-F1 (平均)", f"{np.mean(f1s):.3f}", f"± {np.std(f1s):.3f}")
    r = res[0]
    st.text(classification_report(r["y"], r["p"], digits=3, target_names=NAMES))
    st.dataframe(pd.DataFrame(confusion_matrix(r["y"], r["p"]),
                 index=["真0", "真1", "真2"], columns=["預0", "預1", "預2"]))
    if mode == "tf":
        st.write(f"binary macro-F1 (重要 vs 無關): {r['extra']['binary']:.3f}　"
                 f"top-3 重點句精準度: {r['extra']['top3']:.3f}")
        st.success("已儲存 my_model/ 與 test_predictions.csv(第一個種子)")
    else:
        st.success("已儲存 lstm_best.pt(第一個種子)")
