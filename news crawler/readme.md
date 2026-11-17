# 新聞句子重要性 — 資料管線 + 三模型比較

## 1. 環境
```
py -m venv venv
venv\Scripts\activate
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
pip install transformers datasets streamlit scikit-learn feedparser trafilatura requests pytest
```

## 2. 資料管線(擴充資料)
```
python fetch_news.py      # RSS 抓取即時新聞 → raw_new_articles.csv
$env:DEEPSEEK_API_KEY="<你的 key>"
python label_news.py      # DeepSeek 標註 0/1/2 → labeled_new.csv(可中斷續跑)
python merge_data.py      # 合併 data.csv + labeled_new.csv → data_full.csv
```
- 清洗/斷句邏輯與 news_labeler.html 完全一致
- 標註 prompt 與 news_labeler.html 相同;key 只從環境變數讀取

## 3. 訓練與比較
```
streamlit run app.py
```
- 「單一模型訓練」分頁:手動調參訓練任一種模型
- 「三模型比較」分頁:一鍵跑 3 種方法(LSTM 自建詞表 / LSTM+RoBERTa tokenizer / DistilRoBERTa 微調),輸出對比圖表與方法論 infographic

## 4. 模型
| 方法 | 檔案 |
|---|---|
| TF-IDF + LogReg 基線 / DistilRoBERTa | train.py |
| LSTM 自建詞表 | train_lstm.py |
| LSTM + RoBERTa tokenizer | train_lstm_tok.py |

## 5. 測試
```
python -m pytest tests/ -v
```
