# AI-Ready 任務卡

## Metadata

- 任務：TASK-009 德文→繁中翻譯
- 上層規格：（同 Epic，範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：雙語字典與 SRT 字幕對齊
- 上層 User Story：德文→繁中翻譯
- 分軌：後端
- 前置任務（dependsOn）：TASK-007
- 狀態：就緒（TASK-007 已核准 done）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供手動觸發端點，對指定的德文單字呼叫 MyMemory Translation API，回填 `translation_zh`。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/vocabulary.py`、`backend/app/services/http_client.py`（TASK-007）。
- 既有模式：延續 TASK-008 的 enrich 端點與 service 封裝風格（一個 `services/de_translation.py` 對應一個 `services/en_dictionary.py`）。
- 假設：MyMemory API 端點為 `GET https://api.mymemory.translated.net/get?q={word}&langpair=de|zh`，回應 `responseData.translatedText` 即翻譯結果；免金鑰但每日約 5000 字元額度，超額時 API 會在回應內容而非 HTTP status 標示錯誤（`responseStatus` 欄位非 200），需要額外檢查這個欄位，不能只看 HTTP status code。
- 未知事項：MyMemory 回傳的可能是簡體或籠統的 `zh`，翻譯品質是已知限制，不在本卡處理範圍內（已與人工溝通，之後可換供應商）。
- 允許變更的檔案：`backend/app/api/vocabulary.py`（新增端點）、`backend/app/services/de_translation.py`（新增）、`backend/app/core/config.py`（若需要新增翻譯 API base URL 設定項）。
- 不得觸碰：`backend/app/models/`、既有的英文查詢端點（TASK-008）。

## 需求

- `backend/app/core/config.py` 新增 `de_translation_api_base_url: str = "https://api.mymemory.translated.net/get"`。
- `POST /api/v1/vocabulary/{id}/enrich/de-translation`：
  - 找不到單字 → 404。
  - `language != 'de'` → 422。
  - 呼叫 `services/de_translation.py` 的 `fetch_de_to_zh_translation(headword)`；MyMemory 回應內容的 `responseStatus` 非 200，或 `ExternalApiError`（逾時／連線失敗）→ 502。
  - 成功則更新 `translation_zh`，回傳更新後的 `VocabularyRead`。

## 驗收標準

- 對已存在的 `language='de'` 單字呼叫端點，用假的 HTTP transport 模擬 MyMemory 回應，驗證 `translation_zh` 被正確回填。
- 對 `language='en'` 的單字呼叫端點回 422。
- MyMemory 回應 `responseStatus` 非 200（例如額度用盡）與外部連線逾時，兩種情況分別回 502。

## 實作備註

- 測試同 TASK-008，不打真實外部網路。

## 驗證契約

- 單元測試：`pytest backend/tests/test_de_translation_service.py`
- 整合測試：`pytest backend/tests/test_vocabulary_enrich_de_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：`de_translation_api_base_url` 走 HTTPS；`headword` 進 URL 前做 URL-safe encoding。

## 完成證據

- 變更的檔案：
  - `backend/app/core/config.py`（新增 `de_translation_api_base_url`）
  - `backend/app/services/de_translation.py`（新增，`fetch_de_to_zh_translation()`、`TranslationApiError`）
  - `backend/app/api/vocabulary.py`（新增 `POST /{vocabulary_id}/enrich/de-translation`）
  - `backend/tests/test_de_translation_service.py`、`backend/tests/test_vocabulary_enrich_de_api.py`
- 執行過的指令：
  - `pytest -q` → `68 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `POST /api/v1/vocabulary/{vocabulary_id}/enrich/de-translation` 已正確掛載
- 測試輸出：`70 passed, 1 warning in 0.76s`（審查後修正+補測試，原始為 68 passed）。涵蓋：成功回填 `translation_zh`（含 `responseStatus` 為整數與字串兩種情況）、回應格式異常缺 `translatedText`、language='en' 回 422、vocabulary 不存在回 404、MyMemory `responseStatus` 非 200 回 502（訊息含「翻譯服務回應異常」）、外部連線逾時回 502（訊息含「暫時無法連線」，與前者可分辨）。
- 螢幕截圖：不適用。
- 已知限制：MyMemory 免金鑰額度約每日 5000 字元，超額時以 `responseStatus` 非 200 表示（非 HTTP status），已在 `fetch_de_to_zh_translation` 中檢查該欄位而非只看 HTTP status；翻譯品質（可能為簡體或籠統翻譯）為已知限制，不在本卡處理範圍。headword 透過 `params` 傳遞（非拼入 URL path），交由 `httpx` 做 query string 編碼。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用）：
  - 架構關卡發現：MyMemory 有時將 `responseStatus` 回傳為字串 `"200"` 而非整數，原本 `!= 200`（int）比對會把正常翻譯誤判為失敗、回 502 → 已修正為 `str(response_status) != "200"`，並補上對應測試。
  - 安全性關卡建議：`data["responseData"]["translatedText"]` 直接 subscript，若外部回應格式異常會拋未捕捉的 `KeyError`（500 而非 502）→ 已改用 `.get()` 防護，缺欄位時拋 `TranslationApiError`（502），並補測試。
  - 架構關卡記錄（不強制修正）：`translation_zh` 無條件覆蓋（與 TASK-008 的 `ipa`/`en_definition` 語意一致）——沿用 Niko 對 TASK-008 已確認的「重新查一次即覆蓋」判斷，維持現狀不改。
  - 測試/安全性關卡皆 PASS，其餘為低嚴重度、不阻擋的觀察（如 502 訊息回傳外部 URL，本地單人工具可接受）。
- 後續任務：無（本卡為葉節點功能）。
