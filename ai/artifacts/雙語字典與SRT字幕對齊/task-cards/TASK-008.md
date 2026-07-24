# AI-Ready 任務卡

## Metadata

- 任務：TASK-008 英文單字自動查詢（音標+解釋）
- 上層規格：（同 Epic，範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：雙語字典與 SRT 字幕對齊
- 上層 User Story：英文單字自動查詢（音標+解釋）
- 分軌：後端
- 前置任務（dependsOn）：TASK-007
- 狀態：就緒（TASK-007 已核准 done）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供手動觸發端點，對指定的英文單字呼叫 Free Dictionary API，回填 `ipa` 與 `en_definition`。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/vocabulary.py`、`backend/app/services/http_client.py`（TASK-007）、`backend/app/core/config.py` 的 `en_dictionary_api_base_url`。
- 既有模式：延續現有 vocabulary router 的錯誤處理風格（404/422）。
- 假設：Free Dictionary API 回應格式為陣列，取第一筆 entry 的 `phonetic`（若缺，退而找 `phonetics[]` 第一個有 `text` 的項目）與第一個 `meanings[0].definitions[0].definition`；一併把 `meanings[0].partOfSpeech` 寫入 `part_of_speech`（若原本為空才覆蓋，避免覆蓋使用者手動填寫的值）。
- 未知事項：Free Dictionary API 對特定單字可能回 404（查無此字），此時回傳清楚的錯誤訊息而非整包轉發外部原始回應。
- 允許變更的檔案：`backend/app/api/vocabulary.py`（新增端點）、`backend/app/services/en_dictionary.py`（新增，封裝呼叫與解析邏輯）。
- 不得觸碰：`backend/app/models/`、`backend/app/schemas/vocabulary.py` 的既有欄位定義（`en_definition` 已在 TASK-007 加好，這裡只是使用）。

## 需求

- `POST /api/v1/vocabulary/{id}/enrich/en-dictionary`：
  - 找不到單字（404 vocabulary）→ 404。
  - 單字 `language != 'en'` → 422（「僅適用英文單字」）。
  - 呼叫 `services/en_dictionary.py` 的 `fetch_en_dictionary_data(headword)`，內部用 TASK-007 的 `get_json()`；外部 API 查無此字（404）或逾時／連線失敗（`ExternalApiError`）→ 502，訊息清楚區分「字典查無此字」與「外部服務暫時無法連線」兩種情況。
  - 成功則更新 `ipa`、`en_definition`（若原本為空的 `part_of_speech` 也一併補上），回傳更新後的 `VocabularyRead`。

## 驗收標準

- 對已存在的 `language='en'` 單字呼叫端點，用 mock/假的 HTTP transport 模擬 Free Dictionary API 回應，驗證 `ipa`/`en_definition` 被正確回填。
- 對 `language='de'` 的單字呼叫端點回 422。
- 外部 API 回 404（查無此字）與外部 API 逾時，兩種情況分別回 502，且錯誤訊息不同、可分辨。
- 已有 `en_definition`／`ipa` 的單字重新呼叫，會被最新查詢結果覆蓋（enrich 端點語意上就是「重新查一次」，不是唯一寫入一次）。

## 實作備註

- 測試不打真實外部網路，用 `httpx` 的 `MockTransport` 或替換 `get_json` 為可注入的假實作，確保測試穩定、不依賴網路。

## 驗證契約

- 單元測試：`pytest backend/tests/test_en_dictionary_service.py`
- 整合測試：`pytest backend/tests/test_vocabulary_enrich_en_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：`headword` 直接放進 URL path 前先做 URL-safe encoding（`httpx` 預設會處理，但需確認特殊字元不會破壞請求）；外部回應內容只做結構化欄位讀取，不執行任何動態程式碼。

## 完成證據

- 變更的檔案：
  - `backend/app/services/en_dictionary.py`（新增，`fetch_en_dictionary_data()`、`DictionaryLookupError`、`EnDictionaryData`）
  - `backend/app/api/vocabulary.py`（新增 `POST /{vocabulary_id}/enrich/en-dictionary`）
  - `backend/app/schemas/vocabulary.py`（`VocabularyRead` 新增 `en_definition` 欄位，補齊 TASK-007 遺留的 schema gap）
  - `backend/tests/test_en_dictionary_service.py`、`backend/tests/test_vocabulary_enrich_en_api.py`
- 執行過的指令：
  - `pytest -q` → `60 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `POST /api/v1/vocabulary/{vocabulary_id}/enrich/en-dictionary` 已正確掛載
- 測試輸出：`60 passed, 1 warning in 0.89s`。涵蓋：成功回填 ipa/definition/part_of_speech、part_of_speech 非空時不覆蓋、ipa/en_definition 一律被覆蓋、language='de' 回 422、vocabulary 不存在回 404、字典查無此字回 502（訊息含「查無此字」）、外部服務逾時/連線失敗回 502（訊息含「暫時無法連線」，與查無此字訊息可分辨）。
- 螢幕截圖：不適用。
- 已知限制：headword 已用 `urllib.parse.quote(headword, safe="")` 做 URL-safe encoding 後才組進請求路徑（依 TASK-007 安全性審查建議）；`fetch_en_dictionary_data` 透過檢查 `ExternalApiError.__cause__` 是否為 `httpx.HTTPStatusError` 且 status 404 來判斷「查無此字」，未修改 TASK-007 的 `http_client.py`。
- 審查關卡發現（架構+安全性+測試 agent 審查）：
  - 架構關卡（APPROVE，non-blocking）：(1) `en_dictionary.py` 用 `exc.__cause__` 判斷外部 404，隱性依賴 `http_client.py` 的例外串接方式，屬可接受的耦合，已記錄；(2) 外部查到字但缺音標/解釋時，`ipa`/`en_definition` 會被無條件覆蓋成 `None`（清空使用者原本填寫的值），與 `part_of_speech` 的「僅在原本為空時才覆蓋」邏輯不對稱 → **人工確認後維持現狀**：任務卡驗收標準明確要求「重新查一次即覆蓋最新結果」，此為既有規格的預期行為，不修改；(3) `schemas/vocabulary.py` 的修改嚴格說超出任務卡原列的允許檔案清單，但為補齊 TASK-007 遺留的必要欄位、justified。
  - 安全性關卡（PASS）：headword 的 URL-safe encoding 足以防止 path/query injection；502 錯誤訊息會回傳外部 API 的完整 URL，對本地單人工具可接受，不阻擋關卡。
  - 測試關卡（PASS）：60 passed、ruff 乾淨，驗收標準逐項對應到測試，無 regression。
- 後續任務：無（本卡為葉節點功能）。
