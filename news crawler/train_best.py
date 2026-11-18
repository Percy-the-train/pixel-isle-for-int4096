import time
from compare_tab import CONFIGS, _Sink
from train_common import train_tf

c = CONFIGS["DistilRoBERTa 微調 (tf)"]
print("training best model (DistilRoBERTa) with save=True ...", flush=True)
t0 = time.time()
r = train_tf(c, "data_full.csv", 42, _Sink(), _Sink(), save=True)
print(f"done in {(time.time() - t0) / 60:.1f} min | test macro-F1 {r['f1']:.4f}", flush=True)
print("saved my_model/ (model + tokenizer)", flush=True)
