import json, os, re, sys, time, pathlib, datetime
import requests, feedparser, trafilatura
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from fetch_news import clean_text, split_sentences

BBC_RSS = "http://feeds.bbci.co.uk/news/rss.xml"
URL = "https://api.deepseek.com/chat/completions"
LLM = "deepseek-chat"
MODEL_DIR = "my_model"
TOP_K = 8
ALLOWED = ["Dead body", "Papers (rug)", "Picture", "Chair", "Bookshelf", "Night window"]
N_QUESTIONS = 5
dev = "cuda" if torch.cuda.is_available() else "cpu"

SYSTEM = """你是像素偵探遊戲 Pixel Isle 的編劇。我會給你一篇真實新聞的關鍵句子,你要把它們改寫成一宗遊戲內的謀殺謎案。

規則:
1. 虛構一位住在 Pixel Isle 的受害者(絕對不要用新聞中的真實人物)。新聞只提供「事實與主題」(事件、地點、成因、數字)。
2. 寫一篇約 10 句的遊戲內報紙文章,報導這宗虛構命案;新聞的真實事實要自然地織入(例如新聞講洪水,受害者的死就與洪水有關)。文章要像真的會發生在 Pixel Isle 的事,線索彼此連貫、不能跳脫。
3. 出 5 條四選一選擇題,每條綁定一個遊戲物件,物件只能從下列清單選,每個只用一次:
   "Dead body", "Picture", "Chair", "Bookshelf", "Night window"
   題目要配合物件性質(Dead body=死因, Picture=人物/地點, Chair=現場發現的東西, Bookshelf=文件/書, Night window=夜間看到的事)。
4. 所有題目都必須能從文章中找到答案。每題 4 個選項,只有一個正確,其餘要合理但錯誤。
5. solution:2-3 句解釋受害者為什麼死,必須能由文章推論。
6. key_terms:6-8 個短關鍵詞(供答案評分用)。

只輸出嚴格的 JSON(不要 markdown、不要解釋),格式:
{"title":"...","article":{"headline":"...","text":"..."},"questions":[{"object":"Dead body","question":"...","options":["...","...","...","..."],"answer":0}],"solution":"...","key_terms":["...","..."]}"""


def get_key():
    k = os.environ.get("DEEPSEEK_API_KEY")
    f = pathlib.Path("deepseek_key.txt")
    if not k and f.exists():
        k = f.read_text(encoding="utf-8").strip()
    if not k or k.startswith("PASTE"):
        raise SystemExit("set DEEPSEEK_API_KEY or deepseek_key.txt with a real key")
    return k


def fetch_latest_bbc():
    d = feedparser.parse(BBC_RSS)
    if not d.entries:
        raise RuntimeError("BBC RSS empty")
    e = d.entries[0]
    title = re.sub(r"\s+", " ", e.get("title") or "").strip()
    link = e.get("link") or ""
    text = trafilatura.extract(requests.get(link, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) news-collector/1.0"}, timeout=20).text) \
        or (e.get("summary") or "")
    text = clean_text(text)
    sents = [s for s in split_sentences(text) if len(s) >= 15]
    if len(sents) < 6:
        raise RuntimeError("article too short")
    return dict(title=title, url=link, sents=sents)


def load_model():
    tk = AutoTokenizer.from_pretrained(MODEL_DIR)
    mdl = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR).to(dev).eval()
    return tk, mdl


def score_sentences(tk, mdl, title, sents):
    n = len(sents)
    texts = []
    for i, s in enumerate(sents):
        prev = sents[i - 1] if i > 0 else ""
        nxt = sents[i + 1] if i < n - 1 else ""
        texts.append(f"{title} pos{1 + i} of{n} {prev} SEP {s} {nxt}")
    probs = []
    with torch.no_grad():
        for i in range(0, len(texts), 16):
            e = tk(texts[i:i + 16], truncation=True, max_length=256,
                   padding="max_length", return_tensors="pt")
            with torch.autocast("cuda", dtype=torch.float16, enabled=dev == "cuda"):
                lg = mdl(input_ids=e["input_ids"].to(dev),
                         attention_mask=e["attention_mask"].to(dev)).logits.float().cpu()
            probs.append(torch.softmax(lg, -1)[:, 1])
    p = torch.cat(probs).numpy()
    top = sorted(range(len(sents)), key=lambda i: -p[i])[:TOP_K]
    top = sorted(top)
    return [sents[i] for i in top], [round(float(p[i]), 3) for i in top]


def call_llm(prompt, key):
    res = requests.post(URL, headers={"content-type": "application/json",
                                      "Authorization": "Bearer " + key},
                        json=dict(model=LLM, temperature=0.3,
                                  messages=[dict(role="system", content=SYSTEM),
                                            dict(role="user", content=prompt)]),
                        timeout=300)
    if not res.ok:
        raise RuntimeError(f"{res.status_code} {res.text[:200]}")
    return res.json()["choices"][0]["message"]["content"]


def parse_case(txt):
    m = re.search(r"\{[\s\S]*\}", txt)
    if not m:
        raise ValueError("no JSON object in LLM output")
    case = json.loads(m.group(0))
    for k in ("title", "solution", "key_terms"):
        if k not in case:
            raise ValueError(f"missing {k}")
    if "article" not in case or not case["article"].get("headline") or not case["article"].get("text"):
        raise ValueError("bad article")
    qs = case["questions"]
    if len(qs) != N_QUESTIONS:
        raise ValueError(f"need {N_QUESTIONS} questions, got {len(qs)}")
    used = set()
    for q in qs:
        obj = q.get("object")
        if obj not in ALLOWED or obj in used:
            raise ValueError(f"bad object {obj!r}")
        used.add(obj)
        if not isinstance(q.get("options"), list) or len(q["options"]) != 4 \
                or not isinstance(q.get("answer"), int) or not (0 <= q["answer"] <= 3):
            raise ValueError("bad question")
        q["answer"] = int(q["answer"])
    return case


def main(out="../case_data.js"):
    key = get_key()
    print("fetching latest BBC story ...", flush=True)
    news = fetch_latest_bbc()
    print(f"article: {news['title'][:90]} | {len(news['sents'])} sentences | {news['url']}", flush=True)
    tk, mdl = load_model()
    top, scores = score_sentences(tk, mdl, news["title"], news["sents"])
    print("top key sentences:")
    for s, sc in zip(top, scores):
        print(f"  [{sc:.2f}] {s[:110]}", flush=True)
    prompt = ("News title: " + news["title"] + "\n\nKey sentences:\n" +
              "\n".join(f"{i + 1}. {s}" for i, s in enumerate(top)))
    case = None
    for attempt in range(3):
        try:
            raw = call_llm(prompt, key)
            case = parse_case(raw)
            break
        except Exception as e:
            print(f"attempt {attempt + 1} failed: {e}", flush=True)
            time.sleep(5)
    if case is None:
        raise SystemExit("LLM generation failed after 3 attempts")
    case["source"] = dict(url=news["url"], headline=news["title"],
                          generated=datetime.date.today().isoformat(),
                          key_sentences=top, key_scores=scores)
    js = "window.CASE = " + json.dumps(case, ensure_ascii=False, indent=2) + ";\n"
    pathlib.Path(out).write_text(js, encoding="utf-8")
    pathlib.Path("case_log.json").write_text(
        json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {out} and case_log.json", flush=True)
    print("questions:", [q["object"] for q in case["questions"]], flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "../case_data.js")
