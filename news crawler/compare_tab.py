import time
import numpy as np, pandas as pd, streamlit as st
from sklearn.metrics import f1_score
from transformers import AutoModelForSequenceClassification

from train_common import (COL, load_df, data_tok, data_word, train_lstm, train_tf,
                          Net, dev)

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


def _top3(te, prob):
    t = te.copy()
    t["p_key"] = prob[:, 1]
    hit = tot = 0
    for _, g in t.groupby(COL["article"]):
        top = g.nlargest(3, "p_key")
        hit += (top[COL["label"]] == 1).sum()
        tot += len(top)
    return hit / max(tot, 1)


def compute_result(name, c, csv):
    t0 = time.perf_counter()
    df = load_df(csv)
    te = df[df[COL["split"]] == "test"]
    if c["mode"] == "tf":
        r = train_tf(c, csv, SEED, _Sink(), _Sink(), save=False)
        mdl = AutoModelForSequenceClassification.from_pretrained(c["model"], num_labels=3)
        params = mdl.num_parameters()
    else:
        bundle = data_tok(csv, c["maxlen"]) if c["mode"] == "tok" \
            else data_word(csv, c["maxlen"], c["min_count"])
        r = train_lstm(c, bundle, SEED, _Sink(), _Sink(), save=False)
        params = sum(p.numel() for p in Net(bundle[2], bundle[1], c["emb"], c["hid"],
                                            c["layers"], c["drop"], c["pool"]).parameters())
    secs = time.perf_counter() - t0
    y, p, prob = r["y"], r["p"], r["prob"]
    per = f1_score(y, p, average=None, labels=[0, 1, 2])
    m = dict(name=name,
             macro_f1=round(float(f1_score(y, p, average="macro")), 4),
             f1_0=round(float(per[0]), 4), f1_1=round(float(per[1]), 4),
             f1_2=round(float(per[2]), 4),
             binary=round(float(f1_score(y > 0, p > 0, average="macro")), 4),
             top3=round(float(_top3(te, prob)), 4),
             best_val=round(float(r["best_val"]), 4),
             time_min=round(secs / 60, 1), params=int(params))
    return m


def run_one(name, c, csv):
    st.write(f"**{name}** 開始訓練 (seed {SEED}) …")
    m = compute_result(name, c, csv)
    st.write(f"{name}: test macro-F1 **{m['macro_f1']:.3f}** (val {m['best_val']:.3f}, {m['time_min']} min, {m['params']:,} params)")
    return m


def _charts(res):
    st.markdown("### 結果圖表")
    d = res.rename(columns=dict(macro_f1="macro-F1", f1_0="F1 0 filler",
                                f1_1="F1 1 key", f1_2="F1 2 evidence",
                                binary="binary F1", time_min="訓練時間(分)",
                                best_val="val macro-F1", top3="top-3 精準度",
                                params="參數量"))
    st.markdown("**test macro-F1(越高越好)**")
    st.bar_chart(d[["macro-F1"]])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**各類別 F1**")
        st.bar_chart(d[["F1 0 filler", "F1 1 key", "F1 2 evidence"]])
    with c2:
        st.markdown("**訓練時間(分鐘,越低越好)**")
        st.bar_chart(d[["訓練時間(分)"]])
    st.markdown("**完整指標表**")
    st.dataframe(d[["macro-F1", "F1 0 filler", "F1 1 key", "F1 2 evidence",
                    "binary F1", "top-3 精準度", "val macro-F1", "訓練時間(分)", "參數量"]],
                 width="stretch")


def _infographic(res):
    win = res.macro_f1.idxmax()
    second = res.macro_f1.nlargest(2).iloc[-1]
    margin = res.loc[win, "macro_f1"] - second
    st.markdown("### 方法論解讀 (infographic)")
    st.markdown(f"""
<div style="padding:12px 18px;border-radius:10px;background:#e8f5e9;border:2px solid #2e7d32;margin:8px 0">
<b>贏家:{win}</b><br>
test macro-F1 <b>{res.loc[win, 'macro_f1']:.3f}</b>(領先第二名 <b>{margin:+.3f}</b>);
val macro-F1 {res.loc[win, 'best_val']:.3f};參數 {res.loc[win, 'params']:,};
訓練 {res.loc[win, 'time_min']} 分鐘</div>""", unsafe_allow_html=True)
    cards = [
        ("LSTM 自建詞表", "📚",
         "**從零開始學語言**:詞彙表由語料本身統計得出,詞向量隨機初始化,BiLSTM 由前向後、由後向前掃過句子。沒有外部世界知識,一切只靠這幾萬句。優點:輕量、快;缺點:生字只能當 UNK,語法語義先驗完全沒有。"),
        ("LSTM + RoBERTa tokenizer", "🧩",
         "**借用切詞知識**:用 RoBERTa 的子詞(BPE)分詞器切開文字——罕見字、詞尾變化、拼字變體都能共用子詞,UNK 幾乎消失,詞表覆蓋率高得多。但句子仍靠 BiLSTM 逐字掃描,上下文是線性累積的。"),
        ("DistilRoBERTa 微調", "🧠",
         "**直接請教預訓練大腦**:6700 萬參數、在超大語料上預訓練過;多頭注意力讓每個字同時看到整句所有字的上下文,再在我們的資料上微調最後分類層。語言先驗最強,但也最大、最慢、最吃資源。"),
    ]
    cols = st.columns(3)
    for col, (t, icon, txt) in zip(cols, cards):
        with col:
            st.markdown(f"""<div style="border:1px solid #ccc;border-radius:10px;
padding:12px;height:100%;background:#fafafa">
<div style="font-size:26px">{icon}</div><b>{t}</b><hr>
<div style="font-size:13px;line-height:1.55">{txt}</div></div>""",
                        unsafe_allow_html=True)
    st.markdown(f"""
**根本差異一句話:** 三者的差別在於「外部語言知識注入的層級」——
<b>詞表層</b>(方法1:完全沒有)→ <b>切詞層</b>(方法2:子詞分詞)→ <b>模型層</b>(方法3:整顆預訓練大腦)。
資料越少,預訓練先驗越值錢;資料越多,三者差距通常會縮小——這正好是這次擴充資料集後可以驗證的假設。
""")


def render_compare(csv):
    st.subheader("三模型比較")
    st.caption(f"固定超參數、同一個資料集({csv})、同一 seed {SEED} — 公平對比。左側側欄設定不影響本頁。")
    st.write("method 1: LSTM 自建詞表 | method 2: LSTM + RoBERTa tokenizer | method 3: DistilRoBERTa 微調")
    if st.button("開始比較三模型", type="primary"):
        results = []
        for name, c in CONFIGS.items():
            with st.spinner(f"訓練中: {name}"):
                try:
                    results.append(run_one(name, c, csv))
                except Exception as e:
                    st.error(f"{name} 失敗: {e!r}")
        if len(results) >= 2:
            res = pd.DataFrame(results).set_index("name")
            st.session_state["cmp"] = res
            pd.DataFrame(results).to_csv("compare_results.csv", index=False,
                                         encoding="utf-8-sig")
            st.success("已儲存 compare_results.csv")
    if "cmp" not in st.session_state:
        try:
            saved = pd.read_csv("compare_results.csv")
            if not saved.empty:
                st.session_state["cmp"] = saved.set_index("name")
                st.caption("圖表與 infographic 來自已儲存的 compare_results.csv;按鈕可重新訓練。")
        except Exception:
            pass
    if "cmp" in st.session_state:
        _charts(st.session_state["cmp"])
        _infographic(st.session_state["cmp"])
