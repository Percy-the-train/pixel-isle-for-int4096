import sys, json, time
import pandas as pd
from compare_tab import CONFIGS, compute_result

csv = sys.argv[1] if len(sys.argv) > 1 else "data_full.csv"
print(f"compare run on {csv}", flush=True)
results = []
for name, c in CONFIGS.items():
    print(f"\n===== {name} =====", flush=True)
    t0 = time.time()
    try:
        m = compute_result(name, c, csv)
        results.append(m)
        print(json.dumps(m, default=str), flush=True)
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
