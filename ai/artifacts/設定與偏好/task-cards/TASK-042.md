# AI-Ready 任務卡

## Metadata

- 任務：TASK-042 每日新卡引入上限設定 API（後端）
- 上層規格：`ai/artifacts/設定與偏好/feature-spec.md`
- 上層 Epic：設定與偏好
- 上層 User Story：每日新卡引入上限設定
- 分軌：後端
- 前置任務（dependsOn）：TASK-001、TASK-002、TASK-003、TASK-022、TASK-023、TASK-024、TASK-025、TASK-026（本卡是「設定與偏好」Epic 底下第一張任務卡，依 `ai/skills/implementation-plan.md` 規則強制依賴「專案設置」Epic 全部卡片）
- 狀態：就緒
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-27（feature-spec／screen-spec／mockup-decision 皆已核准，見 `ai/artifacts/設定與偏好/`）

## 目標

新增 `GET /settings`、`PATCH /settings` 端點，把「每日新卡引入上限」從 `backend/app/core/config.py` 寫死的常數，改成可透過 API 調整並持久化到資料庫的值；`GET /reviews/queue` 改為讀取這個持久化值，而非讀取寫死常數。

## 情境包（Context Pack）

- 相關檔案：
  - `backend/app/models/`（新增 `app_settings.py`）
  - `backend/alembic/versions/`（新增 migration，建表並種入預設值 15）
  - `backend/app/schemas/`（新增 `settings.py`：`AppSettingsRead`／`AppSettingsUpdate`）
  - `backend/app/services/app_settings.py`（新增，`get_app_settings(db)` get-or-create helper，供 `api/settings.py` 與 `api/reviews.py` 共用）
  - `backend/app/api/settings.py`（新增路由）
  - `backend/app/api/router.py`（掛載新路由）
  - `backend/app/api/reviews.py`（`get_review_queue` 改讀 `get_app_settings(db).daily_new_card_limit`，取代 `get_settings().daily_new_card_limit`）
  - `backend/app/core/config.py`（`daily_new_card_limit` 常數保留但改為僅供 migration 種子值使用，數值從 20 改成 15，並加註解說明它不再是執行期讀取來源）
  - `backend/tests/test_settings_api.py`（新增）
  - `backend/tests/test_reviews_queue_api.py`（既有兩個依賴 `daily_new_card_limit` 的測試，monkeypatch 對象從 `get_settings` 改成直接寫入 `app_settings` 資料列）
- 既有模式：
  - 資料表定義沿用 `backend/app/models/media_log.py` 等既有 model 的寫法（`Base` 繼承、`__tablename__`）。
  - API router 掛載方式比照 `backend/app/api/router.py` 既有其他路由（`backup.py`、`media_log.py` 等）的 `include_router` 寫法。
  - Alembic migration 比照 `backend/alembic/versions/d2f0916462fe_add_en_definition_and_subtitle_line.py` 的結構（`upgrade`/`downgrade`），本次額外需要在 `upgrade()` 用 `op.bulk_insert` 或原生 SQL 種入一列預設值（`daily_new_card_limit=15`）。
  - 驗證規則比照 `backend/app/schemas/vocabulary.py` 等既有 schema 用 pydantic `Field(ge=1, le=500)` 做範圍驗證，非法值由 FastAPI 自動回 422，不需手動 raise HTTPException。
- 假設：
  - `app_settings` 資料表固定只有一列（單機單一使用者，不需要多筆設定檔），用 `id=1` 固定主鍵，`get_app_settings(db)` 找不到就自動建立一列（種子值來自 `config.py` 的 `daily_new_card_limit`），確保 migration 沒跑種子資料時仍不會炸。
  - 不做身分驗證／權限（沿用專案現況，單機本地無登入機制）。
- 未知事項：無。
- 允許變更的檔案：見上方「相關檔案」清單。
- 不得觸碰：`app/api/vocabulary.py`、`app/api/media_log.py`、`app/api/backup.py` 等其他既有端點；`get_review_queue` 除了新卡上限來源，不變更其他邏輯（含 TASK-041 剛完成的到期卡隨機排序，維持不動）。

## 需求

- `GET /settings`：回傳 `{ "daily_new_card_limit": int }`，讀不到資料列時自動建立種子列（值 15）再回傳。
- `PATCH /settings`：body `{ "daily_new_card_limit": int }`，驗證 1～500 之間整數，通過則更新該列並回傳更新後的值；驗證失敗回 422（FastAPI 自動處理，不需自訂錯誤訊息邏輯）。
- `GET /reviews/queue` 的新卡數量計算，改讀 `get_app_settings(db).daily_new_card_limit`，行為（依語言各自計算今日已引入新卡數、超過上限則不再回傳新卡）維持不變，只換資料來源。

## 驗收標準

- `GET /settings` 首次呼叫（資料庫尚無資料列）回傳 `daily_new_card_limit: 15`。
- `PATCH /settings` 送出合法值（例如 20）後，再呼叫 `GET /settings` 回傳新值 20。
- `PATCH /settings` 送出非法值（0、-1、501、"abc"）回 422，且資料庫裡的值不變。
- 呼叫 `PATCH /settings` 把上限改成 2 後，`GET /reviews/queue`（該語言有 5 個從未複習的新單字）只回傳 2 張新卡，行為與原本讀 `config.py` 常數時一致，只是來源換成資料庫。
- `alembic upgrade head` 在全新資料庫上執行成功，且執行後 `app_settings` 表已有一列 `daily_new_card_limit=15`。
- `cd backend && pytest -q` 全數通過。
- `ruff check .` 全數通過。

## 實作備註

- `AppSettings` model 建議欄位：`id`（固定 1 的主鍵）、`daily_new_card_limit`（`Integer`, `nullable=False`）。
- `get_app_settings(db: Session) -> AppSettings`：`db.get(AppSettings, 1)`，找不到就用 `config.py` 的 `daily_new_card_limit` 當種子值建立、`commit`、回傳。`PATCH` 端點沿用同一個 helper 取得（或建立）該列後修改欄位並 commit。
- Migration 的 `upgrade()` 建表後，直接 `op.execute()` 插入一列種子資料（`id=1, daily_new_card_limit=15`），確保跑過 migration 的環境不需要額外呼叫 API 就有預設值；`get_app_settings` 的 get-or-create 邏輯是保險，不是取代 migration 種子資料。
- `test_reviews_queue_api.py` 既有的 `test_new_cards_capped_by_daily_limit`／`test_new_cards_already_introduced_today_count_against_limit` 兩個測試，把 `monkeypatch.setattr("app.api.reviews.get_settings", ...)` 改成直接對 `db_session` 寫入/更新 `AppSettings` 資料列（例如呼叫 `get_app_settings(db_session)` 後設定 `daily_new_card_limit` 並 commit）。

## 驗證契約

- 單元測試：`AppSettingsUpdate` schema 驗證測試（合法值／超出範圍／非數字）。
- 整合測試：`backend/tests/test_settings_api.py`（`GET`／`PATCH /settings` 端到端）；`backend/tests/test_reviews_queue_api.py` 既有測試改用新資料來源後仍全數通過。
- E2E 測試：無（沿用專案慣例，無 E2E 套件）。
- 型別檢查：不適用（純 Python 後端）。
- Lint：`ruff check .`。
- Build：不適用。
- 螢幕截圖：不適用（無 UI）。
- 安全性檢查：不適用（低風險，無新增身分驗證面、輸入僅為受範圍限制的整數）。

## 完成證據

- 變更的檔案：（實作後填寫）
- 執行過的指令：（實作後填寫）
- 測試輸出：（實作後填寫）
- 螢幕截圖：不適用
- 已知限制：（實作後填寫）
- 後續任務：TASK-043（前端 `/settings` 頁面）依賴本卡完成。
