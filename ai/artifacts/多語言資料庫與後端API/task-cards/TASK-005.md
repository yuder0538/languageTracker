# AI-Ready 任務卡

## Metadata

- 任務：TASK-005 Media Log CRUD API（含語言篩選）
- 上層規格：（同 Epic，範圍單純未另立 feature-spec）
- 上層 Epic：多語言資料庫與後端 API
- 上層 User Story：Media Log CRUD API（含語言篩選）
- 分軌：後端
- 前置任務（dependsOn）：TASK-004
- 狀態：草稿（待 TASK-004 完成後轉就緒）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供 `media_log` 資料表的完整 CRUD API，並支援依 `language` 篩選，讓前端（Phase 4）能各自取得英文／德文視角的追劇紀錄。

## 情境包（Context Pack）

- 相關檔案：`backend/app/models/media_log.py`（TASK-003）、`backend/app/api/router.py`（TASK-004）。
- 既有模式：延續 TASK-004 的 router／依賴注入慣例。
- 假設：本卡只做後端 API，不含任何前端。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/media_log.py`（新增）、`backend/app/schemas/media_log.py`（新增）、`backend/app/api/router.py`（掛載新 router）。
- 不得觸碰：`backend/app/models/`（欄位已在 TASK-003 定案）。

## 需求

- `POST /api/v1/media-logs`：新增一筆紀錄，body 驗證 `language`（`en`/`de`）、`title`、`media_type`、`watched_date`、`duration_minutes`（>=0）。
- `GET /api/v1/media-logs?language=en|de`：列表查詢，`language` 為必填 query 參數（強制語言隔離，不提供「全部語言混查」的預設行為），支援依 `watched_date` 範圍與 `media_type` 做選填篩選。
- `GET /api/v1/media-logs/{id}`：取得單筆，找不到回 404。
- `PATCH /api/v1/media-logs/{id}`：部分更新，不可修改 `language`（語言隔離的紀錄不應該事後換語言，若真的填錯語言，需求是刪除重建）。
- `DELETE /api/v1/media-logs/{id}`：刪除，關聯的 `vocabulary.media_log_id` 依 TASK-003 的 `ON DELETE SET NULL` 自動處理。
- Pydantic schema：`MediaLogCreate`、`MediaLogUpdate`、`MediaLogRead`，與 TASK-003 的欄位對齊。

## 驗收標準

- 對 `language='en'` 與 `language='de'` 各自新增資料後，`GET /api/v1/media-logs?language=en` 只回傳英文資料、`?language=de` 只回傳德文資料，兩者互不混雜。
- 缺少 `language` query 參數時，`GET /api/v1/media-logs` 回 422（強制要求指定語言視角）。
- `PATCH` 嘗試修改 `language` 欄位時被忽略或回 422（實作時二選一並在測試中明確驗證）。
- `duration_minutes` 傳負數時回 422。
- 所有端點皆有對應的 `pytest` 測試（含正常路徑與例外路徑）。

## 實作備註

- 累積時數統計（Phase 4 儀表板要用）可先用 `SUM(duration_minutes)` 的查詢邏輯思考欄位是否足夠，但本卡不需要另外做統計端點（那屬於 Phase 4 或後續任務卡範圍），除非之後發現有共用需求。

## 驗證契約

- 單元測試：`pytest backend/tests/test_media_log_schemas.py`
- 整合測試：`pytest backend/tests/test_media_log_api.py`（透過 FastAPI `TestClient` 實際打 API）
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：所有輸入皆經 Pydantic 驗證；SQL 一律透過 SQLAlchemy ORM 組出，不手寫字串拼接 SQL，避免注入風險。

## 完成證據

- 變更的檔案：
  - `backend/app/schemas/media_log.py`（`MediaLogCreate`/`MediaLogUpdate`/`MediaLogRead`）
  - `backend/app/api/media_log.py`（5 個端點）
  - `backend/app/api/router.py`（掛載 media_log router）
  - `backend/tests/conftest.py`（新增：`db_session`/`client` fixture，用 `StaticPool` 的 in-memory SQLite 隔離每個測試，不再寫進真實 dev DB）
  - `backend/tests/test_api_scaffold.py`（改用新的 `client` fixture，取代原本打真實 dev DB 的寫法）
  - `backend/tests/test_media_log_schemas.py`、`backend/tests/test_media_log_api.py`
- 執行過的指令：
  - `pytest -q` → `23 passed`
  - `ruff check .` → `All checks passed!`
  - 實際啟動 server：`POST /api/v1/media-logs`（建立 de 語言紀錄）→ 201；`GET /api/v1/media-logs?language=de` → 只回傳該筆；`GET /api/v1/media-logs`（不帶 language）→ 422
- 測試輸出：`23 passed, 1 warning in 0.45s`（同前幾卡的 httpx deprecation 警告，非本卡範圍）。
- 螢幕截圖：不適用。
- 已知限制：
  - `PATCH` 對 `language` 欄位採「忽略」策略（`MediaLogUpdate` schema 沒有 `language` 欄位，pydantic 預設 `extra="ignore"` 會直接丟掉該欄位），已在 `test_patch_updates_fields_but_ignores_language` 明確驗證。
  - 過程中發現 in-memory SQLite 若不指定 `StaticPool`，每次連線會拿到獨立的空白資料庫（測試中 `INSERT` 後找不到剛建立的表），已修正並回頭把 TASK-004 遺留的 `test_api_scaffold.py`（原本直接打真實 dev DB）一併改用同一套隔離 fixture。
- 後續任務：Phase 2 字典/SRT 整合會回填 `vocabulary.example_sentence`；Phase 4 UI 會消費本端點做時數統計。
