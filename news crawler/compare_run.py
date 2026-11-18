import sys, json, time
import pandas as pd
from compare_tab import (CONFIGS, compute_result, load_df, data_tok, data_word,
                         train_lstm, train_tf, Net, _Sink, COL, SEED, _top3)
from sklearn.metrics import f1_score, confusion_matrix
from transformers import AutoModelForSequenceClassification


def run_one_full(name, c, csv):
    """Same as compare_tab.compute_result but also returns test y/p for confusion matrices."""
    import time as _t
    t0 = _t.perf_counter()
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
    secs = _t.perf_counter() - t0
    y, p = r["y"], r["p"]
    per = f1_score(y, p, average=None, labels=[0, 1, 2])
    m = dict(name=name,
             macro_f1=round(float(f1_score(y, p, average="macro")), 4),
             f1_0=round(float(per[0]), 4), f1_1=round(float(per[1]), 4),
             f1_2=round(float(per[2]), 4),
             binary=round(float(f1_score(y > 0, p > 0, average="macro")), 4),
             top3=round(float(_top3(te, r["prob"])), 4),
             best_val=round(float(r["best_val"]), 4),
             time_min=round(secs / 60, 1), params=int(params))
    return m, y, p


csv = sys.argv[1] if len(sys.argv) > 1 else "data_full.csv"
print(f"compare run on {csv}", flush=True)
results = []
for name, c in CONFIGS.items():
    print(f"\n===== {name} =====", flush=True)
    t0 = time.time()
    try:
        m, y, p = run_one_full(name, c, csv)
        results.append(m)
        pd.DataFrame(dict(true=y, pred=p)).to_csv(
            f"preds_{c['mode']}.csv", index=False, encoding="utf-8-sig")
        cm = confusion_matrix(y, p, labels=[0, 1, 2])
        pd.DataFrame(cm, index=["filler", "key", "evidence"],
                     columns=["filler", "key", "evidence"]).to_csv(
            f"cm_{c['mode']}.csv", encoding="utf-8-sig")
        print(json.dumps(m, default=str), flush=True)
        print(f"saved preds_{c['mode']}.csv + cm_{c['mode']}.csv", flush=True)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"{name} FAILED: {e!r}", flush=True)
    print(f"elapsed so far: {(time.time() - t0) / 60:.1f} min", flush=True)

if results:
    pd.DataFrame(results).to_csv("compare_results.csv", index=False,
                                 encoding="utf-8-sig")
    print("\nsaved compare_results.csv", flush=True)
    print(pd.DataFrame(results).to_string(index=False), flush=True)
