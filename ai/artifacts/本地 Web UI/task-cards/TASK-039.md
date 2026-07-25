# AI-Ready 任務卡

## Metadata

- 任務：TASK-039 修正英文單字自動查詢缺少中文翻譯的問題
- 上層規格：無（既有功能的缺口修正，非新畫面）
- 上層 Epic：本地 Web UI
- 上層 User Story：英文單字自動查詢補上中文翻譯
- 分軌：後端為主（前端只改一行說明文字）
- 前置任務（dependsOn）：TASK-031
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko（2026-07-25，本機驗證通過）

## 目標

Niko 回報：英文視角點單字列表的「自動查詢」，即使是簡單的字（例如 cookie）翻譯欄位也是空的。要讓英文模式跟德文模式一樣，點一次自動查詢就能同時拿到音標、英文解釋、中文翻譯。

## 情境包（Context Pack）

- 相關檔案：`backend/app/services/de_translation.py`、`backend/app/api/vocabulary.py`、`backend/tests/test_vocabulary_enrich_en_api.py`、`backend/tests/test_en_translation_service.py`（新增）、`frontend/src/pages/Vocabulary.tsx`（僅改說明文字）。
- 根因（已用真實請求驗證，非猜測）：
  - `POST /vocabulary/{id}/enrich/en-dictionary`（`backend/app/api/vocabulary.py:199-218`）從實作之初就只呼叫 `fetch_en_dictionary_data`（dictionaryapi.dev），只寫入 `ipa`／`en_definition`／`part_of_speech`，從未呼叫任何翻譯服務、也從未寫入 `translation_zh`。
  - 直接對真實 dictionaryapi.dev 發請求查 `cookie`，回應正常（有音標、有英文解釋），證實外部字典服務本身沒有故障，是我們的端點本來就沒有做「翻譯」這一步。
  - 對照組：德文模式 `POST /vocabulary/{id}/enrich/de-translation` 有呼叫 `fetch_de_to_zh_translation`（MyMemory，langpair=de|zh-TW），所以德文模式一直都有翻譯，英文模式沒有——這是原始設計時遺漏的不對稱，不是這次改動造成的迴歸。
- 既有模式：沿用 TASK-038 剛建立的 MyMemory 翻譯服務模式，把 `de_translation.py` 內的請求邏輯抽成共用的 `_fetch_zh_translation(headword, langpair)`，`fetch_de_to_zh_translation` 與新增的 `fetch_en_to_zh_translation` 都呼叫它，只是 `langpair` 不同（`de|zh-TW` vs `en|zh-TW`）。檔名沿用 `de_translation.py`（原本只服務德文，現在是雙語共用的 MyMemory 翻譯模組），沒有重新命名檔案，避免不必要的大範圍改動。
- 假設：`de_translation_api_base_url` 設定值其實是通用的 MyMemory 端點（`https://api.mymemory.translated.net/get`），並非德文專用，可以直接讓英文共用同一個設定值。
- 未知事項：MyMemory 對於常見英文字（尤其多義詞）的翻譯品質不穩定——已用真實請求測試 `cookie`，`responseData.translatedText` 回傳的是「Cookie, Cookie」（品質分數 0 的舊詞條），而不是更常見的「餅乾」；MyMemory 內部其實有品質分數 74 的「餅乾」候選，但不是它排在最前面的結果。這是 MyMemory 翻譯記憶庫比對機制本身的限制（跟 TASK-031/038 已記錄的德文翻譯品質問題同一類），修不了，只能靠既有的編輯功能（TASK-033）手動修正。
- 允許變更的檔案：`backend/app/services/de_translation.py`、`backend/app/api/vocabulary.py`、`backend/tests/`、`frontend/src/pages/Vocabulary.tsx`（僅說明文字）。
- 不得觸碰：其他前端頁面、資料庫 schema（`translation_zh` 欄位已存在，不需要 migration）。

## 需求

- 英文單字點「自動查詢」時，同一次請求要同時：
  1. 呼叫既有字典 API 拿音標/英文解釋（不變）。
  2. 新增呼叫 MyMemory 翻譯 API（langpair=en|zh-TW）拿中文翻譯，寫入 `translation_zh`。
- 兩個外部呼叫都成功才寫入資料庫並回傳 200；任一個失敗都回傳 502（沿用德文模式的錯誤處理風格，不做部分寫入）。
- 前端說明文字更新，不再說英文只回填音標/解釋、德文才有翻譯（因為現在兩者都有）。

## 驗收標準

- 英文視角點「自動查詢」後，該筆單字的翻譯欄位不再顯示「—」，會顯示 MyMemory 回傳的中文翻譯（品質可能不完美，但至少有內容可看/可編輯）。
- 翻譯服務失敗（例如 API 逾時）時，畫面顯示查詢失敗的錯誤訊息，跟原本字典查詢失敗的錯誤處理体驗一致。
- 既有的音標/英文解釋/詞性回填行為不受影響。
- `pytest -q` 全數通過、`ruff check .` 全數通過。

## 實作備註

- `backend/app/services/de_translation.py`：抽出 `_fetch_zh_translation(headword, langpair)` 私有函式，`fetch_de_to_zh_translation`／`fetch_en_to_zh_translation` 都是它的薄封裝，避免重複 MyMemory 請求/解析邏輯。
- `backend/app/api/vocabulary.py` 的 `enrich_en_dictionary`：新增第二個 try/except 呼叫 `fetch_en_to_zh_translation`，錯誤訊息比照 `enrich_de_translation`（`翻譯服務回應異常`／`外部翻譯服務暫時無法連線`）。兩個外部呼叫都在 `db.commit()` 之前完成，任一失敗都不會寫入部分資料。
- 沒有新增或修改 `TranslationApiError`／`ExternalApiError` 的例外型別，沿用既有的例外階層。
- 前端 `dashboard-api.ts` 的 `enrichEnDictionary` 函式簽章完全沒變（呼叫同一個端點），前端唯一需要改的是 `Vocabulary.tsx` 裡描述「自動查詢」行為的說明文字。

## 驗證契約

- 單元測試：`backend/tests/test_en_translation_service.py`（新增，4 個測試：成功回傳、回應格式異常、非 200 狀態、外部服務逾時），比照 `test_de_translation_service.py` 的結構。
- 整合測試：`backend/tests/test_vocabulary_enrich_en_api.py` 更新既有 3 個測試補上翻譯 stub，新增 1 個「翻譯服務失敗回 502」的測試；原本 2 個字典失敗案例（查無此字/外部服務逾時）在字典呼叫階段就失敗，不受影響、維持原樣。
- E2E 測試：不適用。
- 型別檢查：待人工在本機執行 `npm run build` 確認（僅改一行 JSX 字串，風險極低）；此執行環境無 Node.js，未能跑。
- Lint：後端 `ruff check .` 已執行，全數通過；Niko 本機執行 `npm run lint` 通過。
- Build：Niko 本機執行 `npm run build` 通過。
- 螢幕截圖：不適用，Niko 以實機操作（點自動查詢確認翻譯欄位有內容）驗證功能，未另外提供截圖。
- 安全性檢查：不適用（呼叫既有外部翻譯服務，複用既有的 headword 輸入，無新輸入處理邏輯）。

## 完成證據

- 變更的檔案：
  - `backend/app/services/de_translation.py`（抽出 `_fetch_zh_translation`，新增 `fetch_en_to_zh_translation`）
  - `backend/app/api/vocabulary.py`（`enrich_en_dictionary` 新增翻譯呼叫與 `translation_zh` 寫入）
  - `backend/tests/test_en_translation_service.py`（新增）
  - `backend/tests/test_vocabulary_enrich_en_api.py`（更新既有測試、新增翻譯失敗測試）
  - `frontend/src/pages/Vocabulary.tsx`（更新自動查詢說明文字）
  - `tools/kanban/epics.json`（新增「英文單字自動查詢補上中文翻譯」User Story）
- 執行過的指令：
  - `curl "https://api.dictionaryapi.dev/api/v2/entries/en/cookie"` → 確認英文字典服務正常，查得到 cookie 的音標與定義
  - `curl "https://api.mymemory.translated.net/get?q=cookie&langpair=en%7Czh-TW"` → 確認 MyMemory 支援 en→zh-TW，但發現此字的最佳匹配翻譯品質不理想（見已知限制）
  - `pytest -q` → 190 passed
  - `ruff check .` → All checks passed
- 測試輸出：見上，全數通過。Niko 本機驗證英文視角自動查詢已能填入翻譯內容，build/lint 皆通過，效能無異狀。
- 螢幕截圖：不適用，Niko 以實機操作驗證。
- 已知限制：
  1. MyMemory 對常見英文字的「最佳匹配」翻譯品質不穩定（例如 cookie 可能翻成「Cookie, Cookie」而非「餅乾」），這是外部翻譯記憶庫服務本身的限制，非本卡程式邏輯錯誤，可用既有編輯功能手動修正。
  2. 跟德文模式一樣，翻譯永遠會覆蓋既有值（不像 `part_of_speech` 有「已有值就不覆蓋」的保護），維持與德文模式一致的行為。
- 後續任務：無。
