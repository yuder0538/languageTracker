# AI-Ready 任務卡

## Metadata

- 任務：TASK-002 環境變數與金鑰設定
- 上層規格：（無，Epic 0 直接由 project-kickoff 產出）
- 上層 Epic：專案設置
- 上層 User Story：環境變數與金鑰設定
- 分軌：後端
- 前置任務（dependsOn）：TASK-001
- 狀態：草稿（待 TASK-001 完成後轉就緒）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

建立集中式設定管理（`pydantic-settings`），涵蓋 SQLite 資料庫檔案路徑與未來字典/LLM API 金鑰的存放慣例，並提供 `.env.example` 讓使用者知道要填哪些變數，密鑰絕不進版控。

## 情境包（Context Pack）

- 相關檔案：`backend/app/core/`（TASK-001 建立的空殼）。
- 既有模式：延續 TASK-001 的 FastAPI 專案結構。
- 假設：目前德文字典先用免費開放 API（不需金鑰），但要預留未來可能加入 LLM API 金鑰（如 Anthropic/OpenAI）的欄位，即使暫時用不到也要建好慣例。
- 未知事項：實際會用哪個免費德文字典 API 尚未在本卡決定（留給 Phase 2 的字典整合任務卡），本卡只需要預留設定欄位。
- 允許變更的檔案：`backend/app/core/config.py`（新增）、`backend/.env.example`（新增）、`backend/.gitignore`（若需要新增 `.env` 排除規則）、`backend/README.md`（補充設定說明）。
- 不得觸碰：`ai/`、`tools/`、`scripts/`。

## 需求

- 新增 `backend/app/core/config.py`，用 `pydantic-settings` 的 `BaseSettings` 定義：
  - `database_url`（預設值指向本地 SQLite 檔案，例如 `sqlite:///./data/immersion_tracker.db`）。
  - `en_dictionary_api_base_url`（預設 Free Dictionary API 的 base URL）。
  - `de_dictionary_api_base_url`（先留空字串預設，Phase 2 決定實際供應商後再填）。
  - `llm_api_key`（`str | None`，預設 `None`，供未來 LLM 翻譯/例句功能使用）。
  - 支援從 `.env` 檔案讀取（`model_config = SettingsConfigDict(env_file=".env")`）。
- 新增 `backend/.env.example`，列出上述所有變數與說明註解，值皆為佔位符或安全預設值，不含任何真實金鑰。
- 確認 `backend/.gitignore`（或根目錄 `.gitignore`）已排除 `.env`、`*.db`、`data/`。
- `backend/README.md` 補充一段「環境設定」：複製 `.env.example` 為 `.env` 並依需要修改。

## 驗收標準

- `from app.core.config import get_settings` 可在應用程式任何地方取得單例設定物件（建議用 `functools.lru_cache` 包裝 `get_settings()`）。
- 未設定 `.env` 時，應用程式仍可用預設值啟動（SQLite 路徑、Free Dictionary API URL 皆有合理預設）。
- `.env` 或任何含真實金鑰的檔案不會出現在 `git status` 的追蹤清單中。
- `backend/.env.example` 不含任何真實金鑰或敏感值。

## 實作備註

- 這張卡只建立設定讀取機制，不建立資料庫連線或 ORM engine（那是 TASK-003 的範圍）。
- `database_url` 的值會被 TASK-003 的 SQLAlchemy engine 直接使用，命名需與 TASK-003 對齊。

## 驗證契約

- 單元測試：`pytest backend/tests/test_config.py`（驗證預設值與 `.env` 覆寫行為）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`pip install -r backend/requirements.txt` 成功（若新增 `pydantic-settings` 需同步更新 `requirements.txt`）。
- 螢幕截圖：不適用。
- 安全性檢查：確認 `.env` 已被 `.gitignore` 排除；`.env.example` 內無真實金鑰；`llm_api_key` 等敏感欄位不會被 log 出來（避免在任何 `print`/`logging` 語句中直接輸出 settings 物件全貌）。

## 完成證據

- 變更的檔案：
  - `backend/app/core/config.py`（`Settings` + `get_settings()`）
  - `backend/.env.example`
  - `backend/tests/test_config.py`
- 執行過的指令：
  - `pytest -q` → `4 passed`（含 TASK-001 的 `/health` 測試）
  - `ruff check .` → `All checks passed!`
  - `git check-ignore -v backend/.env.example` → 未被忽略（可正常進版控）
  - `git check-ignore -v backend/.env`（暫建空檔測試後刪除）→ 被 `.gitignore:1:.env` 排除
- 測試輸出：`4 passed, 1 warning in 0.42s`（同 TASK-001 的 httpx deprecation 警告，非本卡範圍）。
- 螢幕截圖：不適用。
- 已知限制：`de_dictionary_api_base_url` 目前預設空字串，實際供應商留給 Phase 2 決定。
- 後續任務：TASK-003 核心資料模型基礎（`database_url` 命名已對齊，供 TASK-003 的 SQLAlchemy engine 直接使用）。
