# AI-Ready 任務卡

## Metadata

- 任務：TASK-006 Vocabulary CRUD API（含語言隔離與德文特化欄位）
- 上層規格：（同 Epic，範圍單純未另立 feature-spec）
- 上層 Epic：多語言資料庫與後端 API
- 上層 User Story：Vocabulary CRUD API（含語言隔離與德文特化欄位）
- 分軌：後端
- 前置任務（dependsOn）：TASK-004
- 狀態：草稿（待 TASK-004 完成後轉就緒）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供 `vocabulary` 資料表的完整 CRUD API，強制語言隔離查詢，並在 API 層驗證德文／英文各自的特化欄位只在對應語言下才允許填寫。

## 情境包（Context Pack）

- 相關檔案：`backend/app/models/vocabulary.py`（TASK-003）、`backend/app/api/router.py`（TASK-004）。
- 既有模式：延續 TASK-005 的 CRUD 端點寫法（同 Epic 內風格一致）。
- 假設：本卡只做後端 API 與 API 層驗證，不整合任何外部字典/LLM API（那是 Phase 2 範圍）；`de_conjugation` 這階段先接受任意 JSON 字串，不做結構化 schema 驗證。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/vocabulary.py`（新增）、`backend/app/schemas/vocabulary.py`（新增）、`backend/app/api/router.py`（掛載新 router）。
- 不得觸碰：`backend/app/models/`（欄位已在 TASK-003 定案）。

## 需求

- `POST /api/v1/vocabulary`：新增一筆單字，body 驗證：
  - `language`（`en`/`de`，必填）。
  - `language='en'` 時：允許填 `ipa`；若填了 `de_artikel`／`de_plural`／`de_conjugation` 任一欄位，回 422。
  - `language='de'` 時：允許填 `de_artikel`（限 `der`/`die`/`das`）、`de_plural`、`de_conjugation`；若填了 `ipa`，回 422。
  - `headword` 必填；`media_log_id` 選填，若提供須確認對應紀錄的 `language` 與本筆單字的 `language` 一致，否則回 422（避免英文劇集紀錄底下掛德文單字）。
- `GET /api/v1/vocabulary?language=en|de`：列表查詢，`language` 為必填 query 參數；支援依 `headword`（模糊比對）、`media_log_id` 做選填篩選。
- `GET /api/v1/vocabulary/{id}`：取得單筆，找不到回 404。
- `PATCH /api/v1/vocabulary/{id}`：部分更新，`language` 不可修改（理由同 TASK-005 的 Media Log），且更新後仍要符合上述語言特化欄位驗證規則。
- `DELETE /api/v1/vocabulary/{id}`：刪除。
- Pydantic schema：`VocabularyCreate`、`VocabularyUpdate`、`VocabularyRead`，含上述跨欄位驗證邏輯（用 Pydantic 的 `model_validator`）。

## 驗收標準

- `language='en'` 且同時填 `de_artikel` 的建立請求回 422，錯誤訊息清楚指出哪個欄位不合法。
- `language='de'` 且填 `de_artikel='der'` 的請求成功建立，`GET` 回傳的資料包含該欄位。
- `media_log_id` 指向語言不相符的 `media_log` 時回 422。
- `GET /api/v1/vocabulary?language=de` 只回傳德文單字，`?language=en` 只回傳英文單字，兩者複習進度／單字量完全獨立可驗證（本卡先驗證資料層級隔離，複習進度演算法屬於 Phase 3）。
- 所有端點皆有對應的 `pytest` 測試，涵蓋正常路徑與上述例外路徑。

## 實作備註

- 跨欄位驗證（語言與特化欄位是否匹配）集中寫在 Pydantic schema 的 `model_validator`，不要分散在 router 裡手動 if/else，方便未來 Phase 2 擴充欄位時好維護。

## 驗證契約

- 單元測試：`pytest backend/tests/test_vocabulary_schemas.py`（涵蓋跨欄位驗證規則）
- 整合測試：`pytest backend/tests/test_vocabulary_api.py`（透過 FastAPI `TestClient` 實際打 API）
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：所有輸入皆經 Pydantic 驗證；SQL 一律透過 SQLAlchemy ORM 組出；`de_conjugation` 接受的 JSON 字串需限制長度（例如 2000 字元）避免異常大 payload。

## 完成證據

- 變更的檔案：
  - `backend/app/schemas/vocabulary.py`（`VocabularyCreate`/`VocabularyUpdate`/`VocabularyRead`，共用的 `validate_language_specific_fields()`）
  - `backend/app/api/vocabulary.py`（5 個端點 + `media_log_id` 語言比對）
  - `backend/app/api/router.py`（掛載 vocabulary router）
  - `backend/tests/test_vocabulary_schemas.py`、`backend/tests/test_vocabulary_api.py`
- 執行過的指令：
  - `pytest -q` → `39 passed`
  - `ruff check .` → `All checks passed!`
  - 實際啟動 server 手動測：建立 `de` 單字（含 `de_artikel`/`de_plural`）→ 201；建立 `en` 單字同時帶 `de_artikel` → 422；`GET ?language=de` 只回傳德文單字
- 測試輸出：`39 passed, 1 warning in 0.70s`（同前幾卡的 httpx deprecation 警告，非本卡範圍）。
- 螢幕截圖：不適用。
- 已知限制：
  - PATCH 的跨欄位驗證（語言與特化欄位是否匹配）刻意放在 router 層而非 schema 層：`VocabularyUpdate` 本身不知道記錄現有的 `language`，用「先算合併後的有效值再驗證、驗證通過才真的 `setattr`」的順序，避免驗證失敗時 in-memory ORM 物件留下未提交的髒狀態（測試共用同一個 session，若先 `setattr` 再驗證失敗，未 commit 的物件仍會污染同一 session 內後續查詢）。
  - `media_log_id` 對應的紀錄不存在，或語言不相符，兩種情況都回 422（沒有另外區分 404），因為它是 request body 裡的欄位而非 URL 路徑，視為輸入驗證錯誤較一致。
- 後續任務：Phase 2 字典/SRT 整合會自動填入 `ipa`／`de_artikel`／`de_plural`／`de_conjugation`／`example_sentence`；Phase 3 SRS 會新增複習週期欄位（另立 migration）。
