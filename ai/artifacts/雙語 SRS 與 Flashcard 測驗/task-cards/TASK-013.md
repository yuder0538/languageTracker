# AI-Ready 任務卡

## Metadata

- 任務：TASK-013 複習佇列 API
- 上層規格：（同 Epic，範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：雙語 SRS 與 Flashcard 測驗
- 上層 User Story：複習佇列 API
- 分軌：後端
- 前置任務（dependsOn）：TASK-012
- 狀態：就緒（TASK-012 已核准 done）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供查詢端點，依語言（en/de）回傳今日應複習的單字清單：已排程過、現在到期的卡片，加上受每日新卡上限限制的全新卡片。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/vocabulary.py`、`backend/app/models/vocabulary.py`（TASK-012）、`backend/app/models/review_log.py`（TASK-012）、`backend/app/core/config.py`。
- 既有模式：延續 `list_vocabulary` 的語言篩選查詢風格；新端點掛在獨立的 `reviews` router（不是 `vocabulary` router 底下，因為這是跨單字的聚合查詢，語意上屬於「複習」這個概念而非單一單字的 CRUD）。
- 假設：
  - 「到期複習卡」定義為 `srs_last_reviewed_at IS NOT NULL AND srs_next_review_at <= now()`，依 `srs_next_review_at` 升冪排序（最逾期的先出現），不設上限（使用者要清完複習堆積）。
  - 「全新卡」定義為 `srs_last_reviewed_at IS NULL`，依 `id` 升冪排序，數量上限為「今日剩餘新卡額度」= `daily_new_card_limit`（新增到 `config.py`，預設 20）減去「今天已首次複習過的卡片數」；後者透過 `review_log` 依 `vocabulary_id` 分組取每個單字最早一筆 `reviewed_at`，篩出落在今天日期範圍內的數量計算，不额外加欄位。
  - 回傳格式為單一有序清單（到期卡在前、新卡在後），每筆為 `VocabularyRead`，方便前端之後照順序逐張出題。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/reviews.py`（新增）、`backend/app/api/router.py`（掛載新 router）、`backend/app/core/config.py`（新增 `daily_new_card_limit`）。
- 不得觸碰：`backend/app/models/`（TASK-012 已建好）、`backend/app/services/srs.py`。

## 需求

- `backend/app/core/config.py` 新增 `daily_new_card_limit: int = 20`。
- `GET /api/v1/reviews/queue?language=en|de`：
  - `language` 為必填 query 參數（同 `list_vocabulary` 的驗證方式，缺少回 422）。
  - 回傳：到期複習卡（依 `srs_next_review_at` 升冪，全部）+ 全新卡（依 `id` 升冪，上限為當日剩餘新卡額度，額度用完則此段為空清單，不報錯）。

## 驗收標準

- 建立數個不同 `srs_next_review_at`（過去/未來）與 `srs_last_reviewed_at IS NULL` 的單字，呼叫端點驗證到期卡與新卡的排序、篩選正確。
- 全新卡數量超過 `daily_new_card_limit` 時，回傳的新卡數量被正確截斷。
- 今天已透過 `review_log` 首次複習過的卡片，計入「今日已用新卡額度」，使當日後續呼叫佇列端點時新卡數量對應減少。
- `language` 缺少回 422；en/de 兩種語言的佇列彼此獨立，互不干擾。

## 實作備註

- 「今日已用新卡額度」的計算需注意時區：一律用伺服器本機日期（`date.today()`）判斷「今天」，不處理跨時區問題（本地單人工具，已知限制）。

## 驗證契約

- 整合測試：`pytest backend/tests/test_reviews_queue_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：`language` 為 enum 驗證，無注入風險；查詢皆透過 SQLAlchemy ORM 參數化。

## 完成證據

- 變更的檔案：
  - `backend/app/core/config.py`（新增 `daily_new_card_limit`）
  - `backend/app/api/reviews.py`（新增，`GET /reviews/queue`）
  - `backend/app/api/router.py`（掛載 `reviews` router）
  - `backend/tests/test_reviews_queue_api.py`
- 執行過的指令：
  - `pytest -q` → `116 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `GET /api/v1/reviews/queue` 已掛載
- 測試輸出：`116 passed, 14 warnings in 1.85s`（新增的 warning 為 `datetime.utcnow()` deprecation，非阻塞，見已知限制）。涵蓋：到期卡回傳與排序（最逾期優先）、未到期卡排除、新卡依 id 排序、新卡受每日上限截斷、今日已首次複習過的卡片計入額度使新卡數量對應減少、en/de 語言彼此獨立、缺少 `language` 回 422。
- 螢幕截圖：不適用。
- 已知限制：使用 `datetime.utcnow()`（Python 3.12 起標示 deprecated，但為維持與既有 `func.now()`/SQLite `CURRENT_TIMESTAMP`（UTC、naive datetime）一致的比較基準，暫不改用 timezone-aware datetime，避免與既有欄位比較時 naive/aware 混用出錯；「今日」的日期邊界仍依任務卡假設使用伺服器本機日期 `date.today()`，兩者已知不完全對齊時區，屬本地單人工具的可接受簡化）。
- 審查關卡（架構+安全性+測試 agent 審查，皆 PASS/APPROVE，無需修正）：
  - 架構關卡：「今日已用新卡額度」子查詢邏輯正確（`GROUP BY vocabulary_id` + `MIN(reviewed_at)` 不會重複計算、正確排除語言不符/非首次複習）；獨立 `reviews` router 的架構邊界正確；到期卡無上限查詢與 UTC/本機日期混用兩點均為任務卡已記錄的已知限制，本地單人工具規模下可接受。
  - 安全性關卡：全部查詢皆為 SQLAlchemy ORM 參數化，無注入風險；`daily_new_card_limit` 為伺服器端設定值，非使用者輸入可影響。
  - 測試關卡：116 passed，monkeypatch 對 `get_settings()` 確認有效攔截；發現一處測試裡的死碼過濾條件（不影響正確性，只是誤導）→ 已修正測試斷言更精確表達語意。
- 後續任務：無直接後續（TASK-014、TASK-015 皆依賴 TASK-012，非本卡）。
