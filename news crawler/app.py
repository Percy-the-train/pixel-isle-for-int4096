import numpy as np, pandas as pd, streamlit as st
from sklearn.metrics import f1_score, classification_report, confusion_matrix
from train_common import (COL, START, NAMES, dev, load_df, data_tok, data_word,
                          train_lstm, train_tf, baseline)

st.set_page_config(page_title="Sentence Trainer", layout="wide")

# ---------------- 介面 ----------------
tab_train, tab_compare = st.tabs(["單一模型訓練", "三模型比較"])

with tab_train:
    st.title("句子重要性訓練面板")
    sb = st.sidebar
    label = sb.radio("模式", ["LSTM + RoBERTa tokenizer", "LSTM 自建詞表", "DistilRoBERTa 微調"])
    mode = {"LSTM + RoBERTa tokenizer": "tok", "LSTM 自建詞表": "word", "DistilRoBERTa 微調": "tf"}[label]
    csv = sb.text_input("CSV 檔名", "data_full.csv")
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

with tab_compare:
    from compare_tab import render_compare
    render_compare(csv)
