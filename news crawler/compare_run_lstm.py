import json, time
import pandas as pd
from compare_tab import CONFIGS, compute_result

names = ["LSTM 自建詞表 (word)", "LSTM + RoBERTa tokenizer (tok)"]
results = []
for name in names:
    print(f"\n===== {name} =====", flush=True)
    t0 = time.time()
    m = compute_result(name, CONFIGS[name], "data_full.csv")
    results.append(m)
    print(json.dumps(m, default=str), flush=True)
    print(f"elapsed: {(time.time() - t0) / 60:.1f} min", flush=True)

pd.DataFrame(results).to_csv("compare_lstm.csv", index=False, encoding="utf-8-sig")
print("\nsaved compare_lstm.csv", flush=True)
