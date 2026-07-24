# AI-Ready 任務卡

## Metadata

- 任務：TASK-004 API 服務骨架
- 上層規格：（Epic 範圍直接由 project-kickoff 定義，未另立 feature-spec；範圍單純故未套用 spec-interrogation）
- 上層 Epic：多語言資料庫與後端 API
- 上層 User Story：API 服務骨架
- 分軌：後端
- 前置任務（dependsOn）：TASK-001、TASK-002、TASK-003（「專案設置」Epic 全部卡片，依 project-kickoff 強制規則）
- 狀態：草稿（待「專案設置」Epic 全部完成後轉就緒）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

建立本 Epic 底下所有 CRUD 端點共用的基礎設施：FastAPI router 註冊方式、DB session 依賴注入、共用的錯誤/回應格式，以及 `language` 查詢參數的共用驗證邏輯，避免 TASK-005／TASK-006 各自重造一套。

## 情境包（Context Pack）

- 相關檔案：`backend/app/main.py`（TASK-001）、`backend/app/core/db.py`（TASK-003）、`backend/app/models/enums.py`（TASK-003 的 `Language` enum）。
- 既有模式：延續 TASK-001 建立的 `app/api/` 子套件放 router。
- 假設：本 Epic 所有端點掛在 `/api/v1` 前綴下；`language` 查詢參數統一用 `Language` enum 驗證（FastAPI 會自動回 422 若傳入不合法值，如 `fr`）。
- 未知事項：分頁機制細節（page/limit 或 cursor）留給實際端點卡（TASK-005/006）依資料量需求決定，本卡只需預留可擴充的共用 response envelope。
- 允許變更的檔案：`backend/app/api/__init__.py`、`backend/app/api/deps.py`（新增，共用依賴）、`backend/app/schemas/common.py`（新增，共用錯誤/回應 schema）、`backend/app/main.py`（掛載 router）。
- 不得觸碰：`ai/`、`tools/`、`scripts/`、`backend/app/models/`（模型定義已在 TASK-003 定案，本卡不改欄位）。

## 需求

- `backend/app/api/deps.py`：re-export 或包裝 `get_db`，供路由層 `Depends()` 使用。
- `backend/app/schemas/common.py`：定義共用的錯誤回應 schema（例如 `{"detail": str}`，沿用 FastAPI 預設即可，若需要分頁包裝則定義 `PaginatedResponse[T]`）。
- 建立 `backend/app/api/router.py` 作為所有子路由的彙總點，`main.py` 只需 `include_router` 一次。
- 統一的 422／404／500 錯誤回應格式（沿用 FastAPI 內建行為即可，不需自訂 exception handler，除非後續卡片發現有共用需求）。

## 驗收標準

- `GET /health` 仍正常運作（本卡不應破壞既有端點）。
- 新增一個暫時的 `GET /api/v1/ping` 測試端點，確認 router 掛載機制與 DB 依賴注入可用（可在 TASK-005 開始實作時移除或保留視情況）。
- `pytest` 涵蓋 router 掛載與 DB 依賴注入的基本測試皆通過。

## 實作備註

- 保持這張卡的範圍是「基礎設施」，不要提前實作 Media Log 或 Vocabulary 的實際業務邏輯。

## 驗證契約

- 單元測試：`pytest backend/tests/test_api_scaffold.py`
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 可正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：確認尚未對外開放任何寫入端點時沒有輸入驗證缺口（本卡僅骨架，無實際業務端點）。

## 完成證據

- 變更的檔案：
  - `backend/app/api/deps.py`（re-export `get_db`）
  - `backend/app/api/router.py`（`api_router`，`/api/v1` 前綴，含暫時的 `GET /api/v1/ping`）
  - `backend/app/main.py`（掛載 `api_router`）
  - `backend/tests/test_api_scaffold.py`
- 執行過的指令：
  - `pytest -q` → `13 passed`
  - `ruff check .` → `All checks passed!`
  - `uvicorn app.main:app --port 8124` 啟動後 `curl /health` 與 `curl /api/v1/ping` 皆回 200 `{"status":"ok"}`
- 測試輸出：`13 passed, 1 warning in 1.08s`（同前幾卡的 httpx deprecation 警告，非本卡範圍）。
- 螢幕截圖：不適用。
- 已知限制：`backend/app/schemas/common.py`（共用錯誤/分頁 schema）本卡未建立——目前沒有具體需求（FastAPI 內建 422/404 已足夠，TASK-005/006 的需求裡也未要求分頁），依「不做投機性抽象」原則先不做；若 TASK-005/006 實作時真的需要共用 schema，再回來補。
- 後續任務：TASK-005 Media Log CRUD API、TASK-006 Vocabulary CRUD API。
