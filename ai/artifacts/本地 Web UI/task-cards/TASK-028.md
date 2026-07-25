# AI-Ready 任務卡

## Metadata

- 任務：TASK-028 複習歷史聚合 API
- 上層規格：（無獨立 feature-spec；由 Dashboard screen-spec 的資料需求反推，見 `ai/artifacts/專案設置/screen-spec-dashboard.md`）
- 上層 Epic：本地 Web UI
- 上層 User Story：Dashboard 頁面實作
- 分軌：後端
- 前置任務（dependsOn）：TASK-027
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：（實作階段，純後端 API 擴充，非高風險工作，不需額外審查關卡；已通過完整測試與 lint）

## 目標

補上 Dashboard 需要、但既有後端完全沒有的資料：過去 N 天每日複習張數與正確題數，讓「複習日曆熱力圖」與「7 日正確率」能用真實資料而非造假數字。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/reviews.py`、`backend/app/schemas/review.py`、`backend/tests/test_reviews_history_api.py`。
- 既有模式：`get_review_stats`（同檔案）已有「用 `func.date(ReviewLog.reviewed_at)` 依語言分組算連續複習天數」的邏輯，本卡的每日聚合查詢沿用同一種 SQLite 日期分組寫法（`func.date()` 回傳字串、用 `.isoformat()` 比對），維持風格一致。
- 假設：`ReviewLog` 表本身欄位已足夠（`reviewed_at`、`grade`），不需要 schema/migration 變更；`days` 參數上限訂 90 天，避免無界查詢（本機單人工具沒有效能疑慮，這只是防禦性上限，非效能考量）。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/reviews.py`、`backend/app/schemas/review.py`、`backend/tests/`。
- 不得觸碰：`frontend/`（本卡不改前端；串接見 TASK-029）。

## 需求

- 新增 `GET /api/v1/reviews/history?language=en|de&days=35`（`days` 預設 35，涵蓋熱力圖的 5 週；同一個端點也供「7 日正確率」取用最後 7 筆，避免為兩個視覺化各開一支 API）。
- 回傳依日期由舊到新排序的陣列，每筆含 `date`／`reviewed_count`／`correct_count`，**含零複習的日期**（熱力圖需要完整 35 天的格子，不能只回有資料的天）。
- `days` 超出 1-90 範圍回 422。
- 依語言隔離（沿用既有 `Vocabulary.language` 篩選慣例）。

## 驗收標準

- `GET /reviews/history?language=en` 預設回傳 35 筆，最舊一筆日期為「今天 - 34 天」，最新一筆為今天。
- 某天有複習就正確計入 `reviewed_count`／`correct_count`（`AGAIN` 以外的評分視為答對，沿用 `get_review_stats` 的既有定義）；沒複習的天 `reviewed_count`/`correct_count` 皆為 0，不會在陣列裡缺席。
- `days` 不在 1-90 範圍內回 422。
- 未帶 `language` 回 422（沿用既有 query 驗證慣例）。
- 不同語言的資料互相隔離。

## 實作備註

- SQL：`ReviewLog` join `Vocabulary`（取得 `language`），依 `func.date(reviewed_at)` group by，用 `func.sum(case((grade != 'again', 1), else_=0))` 算正確題數。
- 查到的聚合結果存進 `dict[str, tuple[int,int]]`（key 是 ISO 日期字串），再用一個從 `start_date` 到 `end_date` 的迴圈補齊所有日期（含零複習日），確保回傳陣列長度固定等於 `days`。
- 沒有新增/修改資料表欄位，不需要 Alembic migration。

## 驗證契約

- 單元測試：`backend/tests/test_reviews_history_api.py` 新增 7 個測試（預設 35 天含零複習日、`days` 參數生效、日期由舊到新排到今天、單日 reviewed/correct 計數正確、語言隔離、缺 `language` 422、`days` 超出範圍 422）。
- 整合測試：以上測試透過 FastAPI `TestClient` 走完整 HTTP 層，等同輕量整合測試。
- E2E 測試：不適用。
- 型別檢查：不適用（Python 專案無獨立型別檢查步驟，ruff 涵蓋 lint）。
- Lint：`ruff check .` 已執行，全數通過。
- Build：不適用（Python，無 build 步驟）。
- 螢幕截圖：不適用（純 API）。
- 安全性檢查：不適用（唯讀查詢、無使用者輸入寫入資料庫、無新外部網路存取）。

## 完成證據

- 變更的檔案：
  - `backend/app/schemas/review.py`（新增 `ReviewHistoryDay`）
  - `backend/app/api/reviews.py`（新增 `GET /history` 端點）
  - `backend/tests/test_reviews_history_api.py`（新增，7 個測試）
- 執行過的指令：
  - `pytest -q` → 185 passed（178 既有 + 7 新增），0 failed
  - `ruff check .` → All checks passed
- 測試輸出：見上，185/185 通過，無新增警告（既有的 `datetime.utcnow()` deprecation warning 是既有程式碼的既有問題，非本卡引入）。
- 螢幕截圖：不適用。
- 已知限制：無。
- 後續任務：TASK-029（Dashboard 頁面串接本端點）。
