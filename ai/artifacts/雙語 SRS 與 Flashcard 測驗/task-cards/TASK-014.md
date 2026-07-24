# AI-Ready 任務卡

## Metadata

- 任務：TASK-014 複習作答評分 API
- 上層規格：（同 Epic，範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：雙語 SRS 與 Flashcard 測驗
- 上層 User Story：複習作答評分 API
- 分軌：後端
- 前置任務（dependsOn）：TASK-012
- 狀態：就緒（TASK-012 已核准 done）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供端點，讓使用者對單字複習作答評分（again/hard/good/easy），依 SM-2 演算法更新該單字的排程狀態，並寫入複習歷史紀錄。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/vocabulary.py`、`backend/app/services/srs.py`（TASK-012）、`backend/app/models/review_log.py`（TASK-012）。
- 既有模式：延續 TASK-008/009/011 的 `POST /vocabulary/{id}/enrich/...`／動作型端點風格，本端點命名為 `POST /vocabulary/{id}/review`（不是 enrich，因為這是複習流程的核心動作而非資料回填，但錯誤處理與回傳 `VocabularyRead` 的模式一致）。
- 假設：
  - `srs_next_review_at` 由 `now() + timedelta(days=schedule_next_review() 算出的 interval_days)` 計算，時間運算在 API 層做（`srs.py` 純函式只算天數，不碰日期時鐘，方便單元測試）。
  - 每次評分都寫入一筆 `review_log`（不論 grade 為何），`interval_days_after` 存演算法算出的新間隔。
  - 評分事件本身不回傳 `review_log` 內容，只回傳更新後的 `VocabularyRead`（前端如需複習歷史，屬於之後的功能，不在本卡範圍）。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/vocabulary.py`（新增端點）、`backend/app/schemas/review.py`（新增，`ReviewSubmit` 請求 schema）。
- 不得觸碰：`backend/app/models/`、`backend/app/services/srs.py`（純函式邏輯已在 TASK-012 定案，本卡只呼叫它）。

## 需求

- `backend/app/schemas/review.py`：`class ReviewSubmit(BaseModel): grade: ReviewGrade`（複用 TASK-012 的 `ReviewGrade` enum）。
- `POST /api/v1/vocabulary/{id}/review`：
  - 單字不存在 → 404。
  - `grade` 不是合法列舉值 → 422（FastAPI/Pydantic 自動處理）。
  - 成功：讀出目前 `SrsState`（`srs_interval_days`/`srs_ease_factor`/`srs_repetitions`/`srs_lapses`）→ 呼叫 `schedule_next_review()` → 依新 `interval_days` 算出 `srs_next_review_at` → 更新 `vocabulary` 六個 SRS 欄位（含 `srs_last_reviewed_at = now()`）→ 新增一筆 `review_log` → 回傳更新後的 `VocabularyRead`。

## 驗收標準

- 對全新單字（`srs_last_reviewed_at IS NULL`）評分 `good`，驗證排程欄位被正確初始化與更新，且產生一筆 `review_log`。
- 對已有排程的單字評分 `again`，驗證間隔被重置、`srs_lapses` 遞增。
- 單字不存在回 404；`grade` 傳入非法字串回 422。
- 每次呼叫都新增剛好一筆 `review_log`，`interval_days_after` 與回應中的 `srs_interval_days`-equivalent 更新一致（`VocabularyRead` 目前不曝露 SRS 欄位，驗證方式為直接查 DB 或後續 TASK-015 統計端點間接驗證，見驗證契約）。

## 實作備註

- `VocabularyRead` 目前不包含 SRS 欄位（`srs_*`），本卡不新增曝露（不在需求範圍內，避免 schema 膨脹；如後續 Epic 需要前端顯示排程狀態，屆時再拆卡新增）。測試改為直接查詢 DB session 驗證欄位值。

## 驗證契約

- 整合測試：`pytest backend/tests/test_vocabulary_review_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：`grade` 為 enum 驗證（Pydantic），無注入風險；無外部呼叫。

## 完成證據

- 變更的檔案：
  - `backend/app/schemas/review.py`（新增，`ReviewSubmit`）
  - `backend/app/api/vocabulary.py`（新增 `POST /{vocabulary_id}/review`）
  - `backend/tests/test_vocabulary_review_api.py`
- 執行過的指令：
  - `pytest -q` → `120 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `POST /api/v1/vocabulary/{vocabulary_id}/review` 已掛載
- 測試輸出：`121 passed, 48 warnings in 2.49s`（審查後補測試；warning 為 `datetime.utcnow()` deprecation，與 TASK-013 一致，非阻塞）。涵蓋：全新單字評分後排程正確初始化（含 `srs_ease_factor` 與 `srs_next_review_at`/`srs_interval_days` 關係的驗證）並產生一筆 `review_log`；連續評分後再評 `again` 會重置間隔並使 `srs_lapses` 遞增；連續 30 次 `easy` 評分不會觸發 `OverflowError`；單字不存在回 404；`grade` 非法值回 422（Pydantic enum 驗證）。
- 螢幕截圖：不適用。
- 已知限制：`VocabularyRead` 目前不曝露 `srs_*` 欄位（依任務卡範圍決定，避免 schema 膨脹），測試改為直接查 DB session 驗證；`datetime.utcnow()` 與 TASK-013 一致，維持與既有 `func.now()` 的 naive UTC 比較基準；`srs_interval_days` 上限鎖定 100 年（`MAX_SRS_INTERVAL_DAYS`），超過此值會被截斷但不影響排程正確性（100 年遠超任何實際複習需求）。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用）：
  - 安全性關卡發現真實可觸發 bug：`srs_ease_factor` 無上限，連續約 11 次 `easy` 評分後 `interval_days` 指數成長會超過 `datetime` 年份上限（9999），觸發未捕捉的 `OverflowError` → 500 → 已在 API 層加上 `MAX_SRS_INTERVAL_DAYS = 365*100` 上限截斷，並補上「連續 30 次 easy 評分不會 500」的回歸測試。
  - 架構關卡（APPROVE）：日期運算放在 API 層、純函式只算天數的邊界正確；回應不反映剛更新的 SRS 狀態記錄為已知的刻意範圍決定，非阻擋項。
  - 測試關卡（PASS，有 polish 建議）：補上 `srs_ease_factor` 與 `srs_next_review_at`/`srs_interval_days` 一致性的斷言，強化對日期運算 wiring 錯誤的偵測能力。
- 後續任務：無直接後續。
