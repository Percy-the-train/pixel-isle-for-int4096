import json, os, re, time, pathlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd, requests

IN = "raw_new_articles.csv"
OUT = "labeled_new.csv"
CKPT = "label_progress.json"
URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
PROMPT = ("你是新聞標註助手。我會給你一篇新聞的編號句子,請為每一句標註:\n"
          "0 = 可有可無:空泛、對全文沒有太大用途、只是充實語法或過渡的句子。\n"
          "1 = 論點和中心句:新聞主題、發生的核心事件或關鍵事實(例如火災的處理時間、傷亡人數)。\n"
          "2 = 證據或附帶資訊:次要但重要的資訊(例如當事人/市民看法、要求問責、引述、影響如交通受阻等)。\n"
          "只輸出 JSON 陣列,格式 [{\"id\":1,\"label\":0},...],必須涵蓋所有句子編號,不要任何解釋。")


def call_deepseek(user, key):
    res = requests.post(URL, headers={"content-type": "application/json",
                                      "Authorization": "Bearer " + key},
                        json=dict(model=MODEL, temperature=0,
                                  messages=[dict(role="system", content=PROMPT),
                                            dict(role="user", content=user)]),
                        timeout=300)
    if not res.ok:
        raise RuntimeError(f"{res.status_code} {res.text[:200]}")
    return res.json()["choices"][0]["message"]["content"]


def parse_labels(txt, n):
    m = re.search(r"\[[\s\S]*\]", txt)
    if not m:
        raise ValueError("no JSON")
    mp = {o["id"]: int(o["label"]) for o in json.loads(m.group(0))}
    out = []
    for i in range(1, n + 1):
        if i not in mp or mp[i] not in (0, 1, 2):
            raise ValueError(f"missing id {i}")
        out.append(mp[i])
    return out


def label_article(title, sents, key):
    msg = (f"Title: {title}\n" if title else "") + "\n".join(
        f"{i + 1}. {s}" for i, s in enumerate(sents))
    err = None
    for t in range(3):
        try:
            return parse_labels(call_deepseek(msg, key), len(sents))
        except Exception as e:
            err = e
            time.sleep(3 * (t + 1))
    raise err


def main():
    key = os.environ.get("DEEPSEEK_API_KEY")
    kf = pathlib.Path("deepseek_key.txt")
    if not key and kf.exists():
        key = kf.read_text(encoding="utf-8").strip()
    if not key:
        raise SystemExit("set DEEPSEEK_API_KEY env var or create deepseek_key.txt with the key")
    df = pd.read_csv(IN)
    prog = json.loads(pathlib.Path(CKPT).read_text(encoding="utf-8")) if pathlib.Path(CKPT).exists() else {}
    all_ids = [int(a) for a in df.article_id.unique()]
    todo = [a for a in all_ids if str(a) not in prog]
    print(f"{len(all_ids)} articles, {len(todo)} to label")

    def work(aid):
        g = df[df.article_id == aid].sort_values("sent_idx")
        labs = label_article(g.title.iloc[0], g.sentence.tolist(), key)
        return aid, labs

    done = 0
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {ex.submit(work, a): a for a in todo}
        for fut in as_completed(futs):
            aid, labs = fut.result()
            prog[str(aid)] = labs
            pathlib.Path(CKPT).write_text(json.dumps(prog), encoding="utf-8")
            done += 1
            print(f"{done}/{len(todo)} article {aid}: "
                  f"{labs.count(0)}x0 {labs.count(1)}x1 {labs.count(2)}x2", flush=True)

    df["sentence_label"] = [prog[str(a)][int(i) - 1] for a, i in
                            zip(df.article_id, df.sent_idx)]
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print("saved", OUT, df.sentence_label.value_counts().sort_index().to_dict())


if __name__ == "__main__":
    main()
