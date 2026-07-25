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
