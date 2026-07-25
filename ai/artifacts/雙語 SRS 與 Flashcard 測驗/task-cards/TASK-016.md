# AI-Ready 任務卡

## Metadata

- 任務：TASK-016 德文冠詞（der/die/das）填空卡片
- 上層規格：（同 Epic，範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：雙語 SRS 與 Flashcard 測驗
- 上層 User Story：德文冠詞（der/die/das）填空卡片
- 分軌：後端
- 前置任務（dependsOn）：TASK-012、TASK-013、TASK-014
- 狀態：就緒
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

支援「德文冠詞填空」這種客觀評分的特化複習模式：使用者對已標好 `de_artikel` 的德文名詞猜 der/die/das，答對答錯由系統自動判定（不需使用者自評 again/hard/good/easy），並複用既有的 SRS 排程邏輯。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/reviews.py`（TASK-013）、`backend/app/api/vocabulary.py`（TASK-014 的 `submit_review`）、`backend/app/models/vocabulary.py`（`de_artikel` 欄位已在 Epic 1 建好，本卡不新增欄位）。
- 既有模式：複用 TASK-014 的排程更新邏輯（讀 `SrsState` → `schedule_next_review()` → 寫回六個 `srs_*` 欄位與 `review_log`），避免重複實作演算法呼叫邏輯——把這段共用邏輯抽成一個內部函式，供 `submit_review`（既有）與本卡新端點共同呼叫。
- 假設：
  - 答對 → 內部視為 `grade=good`；答錯 → 內部視為 `grade=again`。不提供 hard/easy 這種主觀強度，因為冠詞題本質是「對/錯」二元判定。
  - 只有德文名詞（`language='de'` 且 `de_artikel` 不為 null）適用；動詞/形容詞等沒有冠詞的德文單字不適用。
  - 複習佇列（TASK-013 的 `GET /reviews/queue`）新增可選 `card_type` 參數，預設 `standard`（行為完全不變）；`card_type=artikel` 時只回傳德文名詞（`de_artikel IS NOT NULL`）。`language=en` 搭配 `card_type=artikel` 沒有意義（英文沒有冠詞），回 422。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/reviews.py`（`card_type` 參數）、`backend/app/api/vocabulary.py`（新增端點、抽出共用排程更新函式）、`backend/app/schemas/review.py`（新增 `ArtikelQuizSubmit`、`ArtikelQuizResult`）。
- 不得觸碰：`backend/app/models/`（`de_artikel` 已存在，不新增欄位）、`backend/app/services/srs.py`（演算法純函式不變，本卡只是多一個呼叫方）。

## 需求

- `backend/app/schemas/review.py` 新增：
  - `class ArtikelQuizSubmit(BaseModel): answer: DeArtikel`
  - `class ArtikelQuizResult(BaseModel): correct: bool; correct_answer: DeArtikel`
- `GET /api/v1/reviews/queue` 新增可選 query 參數 `card_type: Literal["standard", "artikel"] = "standard"`：
  - `card_type="artikel"` 時，到期卡與新卡查詢都額外加上 `Vocabulary.de_artikel.is_not(None)` 篩選。
  - `card_type="artikel"` 且 `language="en"` → 422（「英文沒有冠詞，不適用冠詞填空模式」）。
- `POST /api/v1/vocabulary/{id}/review/artikel-quiz`：
  - 單字不存在 → 404。
  - `vocabulary.language != 'de'` 或 `vocabulary.de_artikel is None` → 422（「此單字不適用冠詞填空（非德文名詞或未標註冠詞）」）。
  - 答案正確 → 內部以 `grade=good` 呼叫共用排程更新函式；錯誤 → 以 `grade=again`。
  - 回傳 `ArtikelQuizResult`（`correct`、`correct_answer`），不曝露 `VocabularyRead`（與 TASK-014 的範圍決定一致）。
- 重構：把 TASK-014 `submit_review` 裡「讀狀態 → 呼叫演算法 → 寫回六個欄位 → 寫 review_log → commit/refresh」的邏輯抽成 `_apply_review_grade(db, vocabulary, grade) -> Vocabulary` 內部函式，`submit_review` 與新的 `submit_artikel_quiz` 都呼叫它，避免邏輯重複（並延續 TASK-014 修過的 `MAX_SRS_INTERVAL_DAYS` 截斷保護）。

## 驗收標準

- `card_type=artikel` 的佇列只回傳有 `de_artikel` 的德文名詞；`card_type=standard`（或不傳）行為與 TASK-013 完全一致，不受影響。
- `card_type=artikel` 搭配 `language=en` 回 422。
- 答對冠詞：`correct=true`，且該單字排程被更新（等同 `grade=good` 的效果，透過直接查 DB 驗證）。
- 答錯冠詞：`correct=false`，`correct_answer` 為正確答案，且該單字排程被重置（等同 `grade=again` 的效果，`srs_lapses` 遞增）。
- 對非德文單字或 `de_artikel` 為 null 的德文單字呼叫此端點回 422；單字不存在回 404。
- 既有的 `submit_review`（TASK-014）與 `/reviews/queue` 標準模式（TASK-013）行為不受重構影響，既有測試全數通過。

## 實作備註

- 重構 `_apply_review_grade` 時，`submit_review` 的行為（含回傳的 `VocabularyRead`）必須維持完全一致，這是既有已核准端點，不能因為重構而改變外部行為。

## 驗證契約

- 整合測試：`pytest backend/tests/test_reviews_artikel_queue_api.py`、`pytest backend/tests/test_vocabulary_artikel_quiz_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：`answer`／`card_type` 皆為 enum/Literal 驗證，無注入風險；重構不得引入迴歸，需先跑過既有 TASK-013/014 測試全綠再送審。

## 完成證據

- 變更的檔案：
  - `backend/app/api/vocabulary.py`（抽出 `_apply_review_grade()` 共用函式；新增 `POST /{vocabulary_id}/review/artikel-quiz`）
  - `backend/app/api/reviews.py`（`GET /queue` 新增 `card_type` 參數）
  - `backend/app/schemas/review.py`（新增 `ArtikelQuizSubmit`、`ArtikelQuizResult`）
  - `backend/tests/test_reviews_artikel_queue_api.py`、`backend/tests/test_vocabulary_artikel_quiz_api.py`
- 執行過的指令：
  - `pytest -q` → `136 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `POST /api/v1/vocabulary/{vocabulary_id}/review/artikel-quiz` 已掛載
- 測試輸出：`137 passed, 58 warnings in 2.34s`（審查後補測試，原始 136 passed；warning 為既有的 `datetime.utcnow()` deprecation，非阻塞）。涵蓋：`card_type=artikel` 對「到期卡」與「新卡」兩條查詢分支都只回傳有冠詞的德文名詞、`card_type=standard`（預設）行為與 TASK-013 完全一致不受影響、`card_type=artikel`+`language=en` 回 422、答對/答錯冠詞分別正確判定並更新排程（答對等同 good、答錯等同 again 且 `srs_lapses` 遞增）、非德文或無冠詞單字回 422、單字不存在回 404、非法冠詞值回 422。
- 螢幕截圖：不適用。
- 已知限制：無新增（沿用 TASK-013/014 已記錄的 `datetime.utcnow()`/本機日期簡化假設）。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用）：
  - 架構關卡（APPROVE）：逐行比對確認 `_apply_review_grade()` 重構與原 `submit_review` 邏輯完全一致（含 `MAX_SRS_INTERVAL_DAYS` 截斷保護），`submit_review` 外部行為零改變。
  - 安全性關卡（PASS）：確認重構後 TASK-014 修過的 OverflowError 防護仍完整存在於 `_apply_review_grade()` 內，且集中到單一函式反而降低未來分歧風險。
  - 測試關卡（CONCERNS→已補）：`card_type=artikel` 篩選在到期卡與新卡查詢各寫一次，原本只測到新卡分支 → 已補 `test_artikel_queue_filters_due_cards_too` 涵蓋到期卡分支。
- 後續任務：無（本卡補齊「雙語 SRS 與 Flashcard 測驗」Epic 的最後一個 User Story）。
