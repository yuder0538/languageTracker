# AI-Ready 任務卡

## Metadata

- 任務：TASK-041 複習佇列到期卡改為隨機排序
- 上層規格：無（既有複習佇列 API 的行為調整，非新功能）
- 上層 Epic：雙語 SRS 與 Flashcard 測驗
- 上層 User Story：複習佇列 API
- 分軌：後端
- 前置任務（dependsOn）：TASK-013
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：（純後端行為調整，2026-07-27 與 Niko 討論「設定與偏好」Epic 範圍時一併確認需求，待 Niko 本機驗證後轉 done）

## 目標

Niko 回饋：他加入單字庫的字沒有官方難易度分級（都是追劇時第一次碰到的字，主觀上都重要），現有到期複習卡佇列固定依「最久沒複習」排序，每次複習體感順序都一樣。Niko 要求到期卡改成隨機排序（間歇性複習），新卡則沿用既有邏輯排在到期卡後面。

## 情境包（Context Pack）

- 相關檔案：
  - `backend/app/api/reviews.py`（`get_review_queue`，`due_cards` 原本 `order_by(Vocabulary.srs_next_review_at.asc())`）
  - `backend/tests/test_reviews_queue_api.py`
- 既有模式：`due_cards` 與 `new_cards` 是兩段分開查詢後相加回傳（`due_cards + new_cards`），只改 `due_cards` 的排序方式，`new_cards` 排序（`Vocabulary.id.asc()`）與每日新卡上限邏輯不變。
- 假設：隨機排序套用在「所有到期卡」，不分是否曾標記困難／連續答錯（leech），因為 Niko 明確表示他的單字沒有難易度之分。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/reviews.py`、`backend/tests/test_reviews_queue_api.py`。
- 不得觸碰：`new_cards` 查詢邏輯、每日新卡上限計算、其他複習端點（`/reviews/stats`、`/reviews/history`）。

## 需求

- `GET /reviews/queue` 回傳的到期卡（`due_cards`）改為隨機排序，不再固定依 `srs_next_review_at` 由舊到新排。
- 新卡（`new_cards`）排序與每日新卡上限邏輯維持不變，仍接在到期卡之後回傳。
- `card_type=artikel` 冠詞複習模式套用相同的隨機排序規則。

## 驗收標準

- 多次呼叫 `/reviews/queue`（有多張到期卡時），回傳的到期卡集合正確（不多不少），但順序不保證固定。
- 新卡部分行為不變：依 `id` 升冪排序、受每日新卡上限限制。
- `cd backend && pytest -q` 全數通過。
- `ruff check .` 全數通過。

## 實作備註

- `due_query.all()` 取得結果後用 `random.shuffle()` 原地打亂，不影響 SQL 查詢本身。
- 測試：新增 `test_queue_due_cards_are_shuffled`，用 `monkeypatch` 把 `app.api.reviews.random.shuffle` 換成確定性行為（reverse）驗證排序確實套用了 shuffle 呼叫；原本斷言固定順序的 `test_queue_due_cards_ordered_most_overdue_first` 改為只驗證回傳集合正確，不驗證順序。

## 驗證契約

- 單元測試：無新增（邏輯簡單，涵蓋於下方整合測試）。
- 整合測試：`backend/tests/test_reviews_queue_api.py` 新增/調整 2 個測試（見實作備註）。
- E2E 測試：無。
- 型別檢查：不適用（純 Python 後端）。
- Lint：`ruff check .`。
- Build：不適用。
- 螢幕截圖：不適用（無 UI 變更）。
- 安全性檢查：不適用（低風險、無新增輸入、無資料寫入邏輯變更）。

## 完成證據

- 變更的檔案：
  - `backend/app/api/reviews.py`（`get_review_queue` 的 `due_cards` 改用 `random.shuffle`，移除 `order_by(srs_next_review_at.asc())`）
  - `backend/tests/test_reviews_queue_api.py`（新增 `test_queue_due_cards_are_shuffled`，原順序斷言測試改為集合比對）
- 執行過的指令：
  - `pytest -q`（backend，193 passed）
  - `ruff check .`（backend，全數通過）
- 測試輸出：193 passed，ruff 全數通過。
- 螢幕截圖：不適用（純後端行為調整，無 UI 變更）。
- 已知限制：無。
- 後續任務：無。
