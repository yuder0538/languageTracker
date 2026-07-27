# Multilingual Immersion Tracker — Backend

FastAPI + SQLite 後端，個人多語言沉浸與追劇媒體追蹤系統。目標 Python 3.11+（本機開發環境若只有 3.12 可用，向下相容可直接使用）。

## 設定環境

```bash
cd backend
python -m venv venv
# Windows (PowerShell)
venv\Scripts\Activate.ps1
# Windows (Git Bash)
source venv/Scripts/activate

pip install -r requirements.txt
```

## 建立資料庫（第一次執行必做）

資料表是用 Alembic migration 建立的，`app.main` 不會自動建表。第一次設定環境、或資料庫檔案被刪除重建時，都要先跑：

```bash
alembic upgrade head
```

沒跑這步的話，`uvicorn` 可以正常啟動、`/health` 也會回應正常，但所有會碰資料庫的 API（單字庫、追劇紀錄、複習）都會回 500 錯誤，前端會顯示「讀取失敗」。

## 啟動 dev server

```bash
uvicorn app.main:app --reload
```

開 <http://127.0.0.1:8000/health> 應回傳 `{"status": "ok"}`。

## 跑測試 / lint

```bash
pytest
ruff check .
```

## 環境設定

複製 `.env.example` 為 `.env`，依需要修改內容（`.env` 不會進版控）。

## 技術決策

這個後端看起來只支撐幾個前端頁面，但實際涵蓋的技術範圍比 UI 表面看到的多。記錄在這裡是為了讓後續維護者（包含未來的自己）知道「為什麼」，不用重新猜一次。

- **SRS 排程演算法自己刻，沒有套件**（`app/services/srs.py`）。用的是簡化版 SM-2：依評分（again/hard/good/easy）調整 ease factor 與下次複習間隔，答錯（again）重置 repetitions 並記一次 lapse。自己刻是因為需要跟德文冠詞填空模式（`ReviewArtikel`）共用同一套排程狀態，且規則要能配合「連續答錯多次的卡片標記為 leech」這類專案特化行為，套現成套件（如 anki 演算法 lib）反而綁死擴充彈性。
- **雙語（en/de）資料是隔離的，不是共用一張表加語言欄位的簡單設計** — `Vocabulary`／`MediaLog` 皆以 `language` 區分且德文有專屬欄位（`de_artikel` 冠詞等），所有查詢端點強制帶語言篩選，避免英文/德文資料互相污染。
- **兩個外部字典/翻譯 API 各自獨立整合**：英文走 `services/en_dictionary.py`（dictionaryapi.dev 查音標/釋義）+ MyMemory 補中文翻譯；德文走 `services/de_translation.py`（MyMemory `de|zh-TW`）。兩邊都是「查詢失敗就回 502、成功才寫回資料庫」，不會半套資料留在 DB 裡。已知限制：MyMemory 的翻譯記憶庫比對品質不穩定（同一個字有時翻不準），這是外部服務本身的限制，不是程式邏輯問題，翻錯可用既有編輯功能手動修正。
- **SRT 字幕解析器自己寫**（`app/services/srt_parser.py`），沒有用第三方 srt parsing 套件——格式簡單（index/timing/text 三段一 block）且需要客製化錯誤訊息（`SrtParseError` 標明是哪個 block 壞掉），自己寫比拉套件依賴划算。
- **範疇是刻意控制的，不是能力做不到**：多個 User Story（例如單字庫搜尋列、單字庫管理頁面）都在任務卡的「殘留風險／後續任務」欄位明確寫下「不做進階篩選／編輯，留給後續 User Story」。這是治理流程（見根目錄 `AGENTS.md`）要求每張任務卡先寫清楚 non-goals 的結果，避免一張卡範圍無限擴大。
- **測試覆蓋量與程式碼量比例接近 2:1**（後端本體約 1,674 行 vs 測試約 3,053 行、35 個測試檔），外部 API 呼叫（字典/翻譯）皆有 mock 測項與失敗情境（逾時、非 200、格式異常）測項，不是只測 happy path。
