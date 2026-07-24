# AI-Ready 任務卡

## Metadata

- 任務：TASK-001 技術骨架初始化
- 上層規格：（無，Epic 0 直接由 project-kickoff 產出，不需要 feature-spec）
- 上層 Epic：專案設置
- 上層 User Story：技術骨架初始化
- 分軌：後端
- 前置任務（dependsOn）：無
- 狀態：就緒
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

建立 Multilingual Immersion Tracker 後端專案的目錄結構、Python 3.11 虛擬環境慣例、`requirements.txt`，以及可執行的 lint/test 指令與一個最小可跑的 FastAPI 健康檢查端點，讓後續任務卡有地方長出程式碼。

## 情境包（Context Pack）

- 相關檔案：目前專案根目錄只有 Monstrare 治理骨架（`ai/`、`tools/`、`scripts/`），尚無任何應用程式碼。
- 既有模式：無既有後端程式碼可參考，直接依 FastAPI 官方慣例（`app/` 套件、`app/main.py` 進入點）建立。
- 假設：Python 3.11、pip + venv（不用 Poetry/uv）、SQLite 為資料庫、無需容器化部署。
- 未知事項：無。
- 允許變更的檔案：新增 `backend/` 目錄底下所有檔案、根目錄 `.gitignore` 若需要補充 Python 相關規則可一併調整。
- 不得觸碰：`ai/`、`tools/`、`scripts/`、既有的 `.github/`、`.codex/` 等治理骨架檔案。

## 需求

- 在專案根目錄建立 `backend/` 目錄，內含：
  - `app/` 套件（`__init__.py`、`main.py`、`api/`、`models/`、`schemas/`、`core/` 子套件，先建空殼即可，供後續任務卡填充）。
  - `tests/` 目錄（含 `__init__.py`）。
  - `requirements.txt`：至少包含 `fastapi`、`uvicorn[standard]`、`sqlalchemy`、`pydantic-settings`、`pytest`、`httpx`（測試用 TestClient 需要）、`ruff`（lint）。
  - `pyproject.toml` 或 `pytest.ini`：設定 `tests/` 為測試根目錄。
  - `README.md`（`backend/README.md`）：如何建立 venv、安裝套件、啟動 dev server、跑測試/lint 的指令。
- `app/main.py` 建立 FastAPI app 實例，並提供 `GET /health` 回傳 `{"status": "ok"}`。
- 確認 `uvicorn app.main:app --reload` 可在 `backend/` 目錄下啟動。
- 確認 `pytest` 可執行（至少一個針對 `/health` 的測試）。
- 確認 `ruff check .` 可執行且無錯誤。

## 驗收標準

- `backend/requirements.txt` 存在且套件版本可正常安裝（`pip install -r requirements.txt` 成功）。
- 執行 `uvicorn app.main:app` 後，`GET /health` 回傳 200 與 `{"status": "ok"}`。
- `pytest` 全數通過。
- `ruff check .` 無錯誤。
- 目錄結構符合上述需求，供 TASK-002／TASK-003 直接擴充，不需要重建骨架。

## 實作備註

- `app/core/` 預留給 TASK-002 的設定（settings）模組使用。
- `app/models/`、`app/schemas/` 預留給 TASK-003 的 SQLAlchemy 模型與 pydantic schema。
- 不要在這張卡實作資料庫連線或任何業務邏輯，只做骨架與健康檢查。

## 驗證契約

- 單元測試：`pytest backend/tests/test_health.py`
- 整合測試：不適用（本卡無外部整合）。
- E2E 測試：不適用。
- 型別檢查：不強制（先以 ruff 為主，型別檢查可在後續卡片視需要加入 mypy）。
- Lint：`ruff check backend/`
- Build：`pip install -r backend/requirements.txt` 成功視為 build 通過。
- 螢幕截圖：不適用（無 UI）。
- 安全性檢查：確認 `requirements.txt` 套件皆為知名套件、無明顯供應鏈風險；`.gitignore` 排除 `venv/`、`__pycache__/`、`*.db`。

## 完成證據

- 變更的檔案：
  - `backend/requirements.txt`
  - `backend/pyproject.toml`
  - `backend/README.md`
  - `backend/app/__init__.py`、`app/main.py`
  - `backend/app/api/__init__.py`、`app/models/__init__.py`、`app/schemas/__init__.py`、`app/core/__init__.py`
  - `backend/tests/__init__.py`、`tests/test_health.py`
  - `.gitignore`（新增 Python/venv/SQLite 相關排除規則，並修正 `.env.*` 會誤擋 `.env.example` 的既有問題）
- 執行過的指令：
  - `python -m venv venv`
  - `python -m pip install -r requirements.txt`
  - `pytest -q` → `1 passed`
  - `ruff check .` → `All checks passed!`
  - `uvicorn app.main:app --port 8123` 啟動後 `curl http://127.0.0.1:8123/health` → `{"status":"ok"}`（HTTP 200）
- 測試輸出：`1 passed, 1 warning in 1.66s`（警告為 `starlette.testclient` 對 httpx 的 deprecation 提示，不影響功能，非本卡範圍）。
- 螢幕截圖：不適用。
- 已知限制：
  - 本機只有 Python 3.12（無 3.11），已改用 3.12 建立 venv；程式碼未使用任何 3.12-only 語法，對 3.11 環境相容。
  - `starlette.testclient` 出現 httpx deprecation 警告，暫不處理，待該套件生態穩定或後續卡片需要時再評估。
- 後續任務：TASK-002 環境變數與金鑰設定、TASK-003 核心資料模型基礎。
