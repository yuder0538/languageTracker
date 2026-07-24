# AI-Ready 任務卡

## Metadata

- 任務：TASK-015 複習統計與進度追蹤
- 上層規格：（同 Epic，範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：雙語 SRS 與 Flashcard 測驗
- 上層 User Story：複習統計與進度追蹤
- 分軌：後端
- 前置任務（dependsOn）：TASK-012
- 狀態：就緒（TASK-012 已核准 done）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供查詢端點，回傳依語言區分的複習統計：今日已複習張數、正確率、連續複習天數（streak），供之後 Phase 4 Dashboard 使用。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/reviews.py`（TASK-013 建立的 router，本卡加一個端點進去）、`backend/app/models/review_log.py`（TASK-012）。
- 既有模式：延續 TASK-013 的 `reviews` router 與語言篩選查詢風格。
- 假設：
  - 「正確」定義為 `grade != 'again'`（`hard`/`good`/`easy` 皆視為正確，只有 `again` 視為忘記/不正確），與 TASK-012 的演算法假設一致（只有 `again` 會重置間隔）。
  - 「今日已複習張數」與「正確率」統計範圍為 `review_log.reviewed_at` 落在今天（伺服器本機日期）、且對應 `vocabulary.language` 符合查詢參數的紀錄。
  - 「連續複習天數」（streak）：從今天往回算，每天至少有一筆該語言的 `review_log` 就算一天，中斷（某天完全没複習）則 streak 停止累加；今天若還沒複習過，streak 從「昨天」開始算（不因為「今天還沒複習」就把 streak 歸零），這是常見 SRS 應用的慣例（給使用者當天還有機會維持連續紀錄）。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/reviews.py`（新增端點，同 TASK-013 建立的檔案）。
- 不得觸碰：`backend/app/models/`、`backend/app/services/srs.py`。

## 需求

- `GET /api/v1/reviews/stats?language=en|de`：
  - `language` 為必填 query 參數，缺少回 422。
  - 回傳 `{"reviewed_today": N, "accuracy_today": 0.0~1.0 或 null（今日無複習時）, "streak_days": N}`。

## 驗收標準

- 今日對某語言複習 N 次（含至少一次 `again`），驗證 `reviewed_today` 與 `accuracy_today` 計算正確（正確率 = 非 again 次數 / 總次數）。
- 今日尚無複習紀錄時，`reviewed_today == 0` 且 `accuracy_today` 為 `null`（避免除以零）。
- 連續複習天數：模擬跨日的 `review_log` 紀錄（今天、昨天、前天皆有，大前天中斷），驗證 `streak_days == 3`；今天尚未複習但昨天有複習時，streak 不歸零。
- en/de 兩種語言的統計彼此獨立。

## 實作備註

- 測試需要造出不同 `reviewed_at` 日期的 `review_log` 資料（直接寫入 DB session，不透過 API，因為 TASK-014 的評分端點只會產生「現在」時間的紀錄）。

## 驗證契約

- 整合測試：`pytest backend/tests/test_reviews_stats_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：`language` 為 enum 驗證，查詢皆透過 SQLAlchemy ORM 參數化，無注入風險。

## 完成證據

- 變更的檔案：
  - `backend/app/schemas/review.py`（新增 `ReviewStats`）
  - `backend/app/api/reviews.py`（新增 `GET /reviews/stats`）
  - `backend/tests/test_reviews_stats_api.py`
- 執行過的指令：
  - `pytest -q` → `127 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `GET /api/v1/reviews/stats` 已掛載
- 測試輸出：`127 passed, 52 warnings in 2.27s`（新增 warning 為 `datetime.utcnow()` deprecation，與 TASK-013/014 一致，非阻塞）。涵蓋：今日複習張數與正確率計算（含 again 視為不正確）、今日無複習時正確率為 null、連續複習天數計算（含中斷情境）、今日尚未複習時 streak 不歸零（從昨天開始算）、en/de 語言彼此獨立、缺少 `language` 回 422。
- 螢幕截圖：不適用。
- 已知限制：連續天數判斷使用 `func.date()` 依伺服器本機日期分組，與 TASK-013 相同的時區簡化假設；正確率定義為「非 again 皆算正確」，與 TASK-012 演算法假設一致。
- 審查關卡（架構+安全性+測試 agent 審查，皆 PASS/APPROVE，無需修正）：
  - 架構關卡：`func.date()` 對 naive UTC datetime 的日期萃取正確；streak 迴圈有界（`reviewed_days` 為有限集合、cursor 單調遞減），streak=0 情境驗證會立即終止不會往回走；`accuracy_today` 定義與 TASK-012 演算法假設一致。**Epic 收尾檢查**：TASK-012~015 四個 User Story 各自對應一張卡、職責無重疊無缺口（TASK-012 模型+演算法、TASK-013 讀佇列、TASK-014 寫入評分、TASK-015 讀統計）；延後的「德文冠詞 der/die/das 填空卡片」已正確記錄在 `epics.json` 的 `backlogNotes`，非遺漏。
  - 安全性關卡：兩個查詢皆為 SQLAlchemy ORM 參數化，回應只含聚合數字（比 TASK-013 的 `/queue` 曝露更少），streak 迴圈受真實歷史資料筆數限制，非攻擊者可控。
  - 測試關卡：127 passed，六項驗收標準逐一對應到測試（含 streak 中斷與今日未複習不歸零兩個關鍵情境皆有明確測試而非僅靠推論）。
- 後續任務：無（本卡為本輪 Epic 最後一張）。
