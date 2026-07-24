# AI-Ready 任務卡

## Metadata

- 任務：TASK-011 例句對齊（Enrich Example Sentence）
- 上層規格：（同 Epic，範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：雙語字典與 SRT 字幕對齊
- 上層 User Story：SRT 字幕解析與例句對齊
- 分軌：後端
- 前置任務（dependsOn）：TASK-010
- 狀態：就緒（TASK-010 已核准 done）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供手動觸發端點，在單字所屬 `media_log` 的字幕中尋找該單字出現的對話行，回填 `example_sentence`。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/vocabulary.py`、`backend/app/models/subtitle_line.py`。
- 既有模式：延續 TASK-008/009 的 enrich 端點風格（`POST /vocabulary/{id}/enrich/...`）。
- 假設：比對方式為大小寫不敏感的子字串比對（`subtitle_line.text ILIKE '%headword%'`），找到第一筆符合的行即可，不做進階的斷詞/字形變化比對（例如德文變格、英文動詞變位不會特別處理，屬於已知限制）。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/vocabulary.py`（新增端點）。
- 不得觸碰：`backend/app/models/`、`backend/app/services/srt_parser.py`。

## 需求

- `POST /api/v1/vocabulary/{id}/enrich/example-sentence`：
  - 單字不存在 → 404。
  - 單字沒有關聯 `media_log_id`（`media_log_id is None`）→ 422（「此單字未關聯劇集紀錄，無法對齊例句」）。
  - 關聯的 `media_log` 底下沒有任何 `subtitle_line`（尚未上傳字幕）→ 422（「該劇集尚未上傳字幕」）。
  - 在該 `media_log_id` 底下的 `subtitle_line` 用大小寫不敏感子字串比對 `headword`，找不到 → 404（「字幕中找不到此單字」）。
  - 找到則取該行 `text` 存入 `example_sentence`，回傳更新後的 `VocabularyRead`。

## 驗收標準

- 單字關聯的 `media_log` 已上傳含該單字的字幕，呼叫端點後 `example_sentence` 被正確回填為該行文字。
- 單字無 `media_log_id`、有 `media_log_id` 但無字幕、字幕中查無該單字，三種情況分別回對應的 422/422/404，訊息可分辨。

## 實作備註

- 這是本 Epic 最後一張卡，完成後回頭確認 TASK-007~011 合起來是否覆蓋原始規格書的「英文抓音標與解釋、德文抓翻譯、SRT 對齊例句」，做一次 MECE 收尾檢查。

## 驗證契約

- 單元測試：不適用（邏輯簡單，直接用整合測試涵蓋即可）。
- 整合測試：`pytest backend/tests/test_vocabulary_enrich_example_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：`ILIKE` 查詢的 `headword` 來自資料庫既有欄位（非使用者直接輸入的自由文字），且透過 SQLAlchemy ORM 參數化查詢組出，無 SQL 注入風險。

## 完成證據

- 變更的檔案：
  - `backend/app/api/vocabulary.py`（新增 `POST /{vocabulary_id}/enrich/example-sentence`）
  - `backend/tests/test_vocabulary_enrich_example_api.py`
- 執行過的指令：
  - `pytest -q` → `94 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認端點已掛載
- 測試輸出：`94 passed, 1 warning in 1.12s`。涵蓋：成功回填 `example_sentence`、大小寫不敏感比對、無 `media_log_id` 回 422（訊息「未關聯劇集紀錄」）、有 `media_log_id` 但未上傳字幕回 422（訊息「尚未上傳字幕」）、字幕中查無單字回 404（訊息「找不到此單字」）、vocabulary 不存在回 404，三種 422/404 訊息互相可分辨。
- 螢幕截圖：不適用。
- 已知限制：僅做大小寫不敏感子字串比對（`ILIKE`），不做斷詞或字形變化比對（德文變格、英文動詞變位等不處理），符合任務卡預期的已知限制。
- MECE 收尾檢查（本 Epic 最後一卡）：TASK-007 建立共用基礎（`en_definition`/`subtitle_line`/`http_client`）；TASK-008 英文查詢（ipa/definition/part_of_speech）；TASK-009 德文翻譯（translation_zh）；TASK-010 SRT 上傳與整批取代（`subtitle_line`）；TASK-011 例句對齊（example_sentence）。原始規格「英文抓音標與解釋、德文抓翻譯、SRT 對齊例句」三項需求皆已覆蓋，無遺漏。
- 審查關卡（架構+安全性+測試 agent 審查，皆 PASS，無需修正）：
  - 架構關卡：兩次查詢（存在性檢查+比對查詢）是必要設計，用來區分 422（未上傳字幕）與 404（查無單字）兩種不同語意，非多餘。`ilike` 用法與既有 `list_vocabulary` 的 headword 篩選一致，非新增風險。記錄一個既有慣例的已知限制：headword 若含 `%`/`_` 會被當作 LIKE 萬用字元（`list_vocabulary` 也有此行為，非本卡新增，不修正）。
  - 安全性關卡：`ilike()` 為 SQLAlchemy 參數化查詢，非字串拼接原生 SQL，無注入風險；本端點無外部網路呼叫、無新增依賴。
  - 測試關卡：94 passed，六項驗收標準逐一對應到測試，兩個 404（vocabulary 不存在 vs 字幕查無單字）確認以 `detail` 訊息內容區分而非僅靠 status code。
- 後續任務：Epic「雙語 SRS 與 Flashcard 測驗」（Phase 3）。
