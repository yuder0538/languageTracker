# AI-Ready 任務卡

## Metadata

- 任務：TASK-018 Anki 匯出格式
- 上層規格：（Epic 範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：資料匯出入與備份
- 上層 User Story：Anki 匯出格式
- 分軌：後端
- 前置任務（dependsOn）：TASK-006
- 狀態：就緒（TASK-017 已核准 done，本卡不依賴它但沿用同樣的檔案上傳/路由慣例）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

把單字庫匯出成 Anki 可直接匯入的純文字格式，供想搭配 Anki 複習的使用者使用。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/vocabulary.py`。
- 既有模式：延續 `list_vocabulary` 的語言篩選查詢風格。
- 假設：
  - 匯出純文字 TSV（Tab 分隔，Front/Back 兩欄），這是 Anki「記事庫（Basic）」筆記類型可直接匯入的通用格式；**不產生 `.apkg` 二進位封裝檔**（那是完整的 Anki SQLite collection 格式，對這個範圍而言過度複雜，純文字匯入是 Anki 官方支援且足夠的做法）。
  - 英文：Front = headword（若有 ipa，加註 `[ipa]`）；Back = en_definition（若空則退而用 translation_zh）+ 換行後接 example_sentence（若有）。
  - 德文：Front = `{de_artikel} {headword}`（若無 de_artikel 則只有 headword）；Back = translation_zh + 換行後接 example_sentence（若有）。
  - 欄位內容裡若含真正的換行字元，取代為 `<br>`（Anki 純文字匯入以每行一筆卡片為單位，欄位內部換行需另外編碼，用 HTML `<br>` 是 Anki 支援的慣例）；欄位內容裡的 Tab 字元取代為空白，避免破壞欄位分隔。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/vocabulary.py`（新增端點）。
- 不得觸碰：`backend/app/models/`、`backend/app/schemas/vocabulary.py`。

## 需求

- `GET /api/v1/vocabulary/export/anki?language=en|de`：
  - 回傳 `text/tab-separated-values`，`Content-Disposition: attachment; filename="anki_export_{language}.txt"`。
  - 每個符合語言篩選的單字輸出一行 `Front\tBack`。
  - 該語言下沒有任何單字時，回傳空檔案（200，不報錯）。

## 驗收標準

- 匯出英文單字：驗證 Front 含 headword 與 ipa（若有），Back 含 en_definition/translation_zh 與 example_sentence。
- 匯出德文單字：驗證 Front 含 `de_artikel + headword`，Back 含 translation_zh。
- 欄位內容含換行字元時，輸出檔案裡該筆卡片仍只佔一行（換行已被替換為 `<br>`）。
- `language` 缺少回 422（同既有 enum 驗證慣例）。

## 實作備註

- 純函式方式組字串（例如 `_build_anki_line(vocab: Vocabulary) -> str`），方便獨立單元測試，不需要啟動 HTTP。

## 驗證契約

- 單元測試：`pytest backend/tests/test_anki_export_service.py`
- 整合測試：`pytest backend/tests/test_vocabulary_export_anki_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：純字串組裝與 ORM 查詢，無注入風險；輸出內容為使用者自己輸入的資料，不涉及第三方內容。

## 完成證據

- 變更的檔案：
  - `backend/app/services/anki_export.py`（新增，`build_anki_line()` 純函式）
  - `backend/app/api/vocabulary.py`（新增 `GET /export/anki`，路由放在 `/{vocabulary_id}` 之前但因深度不同本來就不會衝突）
  - `backend/tests/test_anki_export_service.py`、`backend/tests/test_vocabulary_export_anki_api.py`
- 執行過的指令：
  - `pytest -q` → `152 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `GET /api/v1/vocabulary/export/anki` 已掛載，且 `/{vocabulary_id}` 與 `/import-csv`（TASK-017）等既有路由未被遮蔽
- 測試輸出：`155 passed, 58 warnings in 2.56s`（審查後補測試與修正，原始 152 passed；既有 `datetime.utcnow()` deprecation，非阻塞）。涵蓋：英文卡片 Front 含 ipa、Back 優先用 en_definition 缺則退而用 translation_zh；德文卡片 Front 含冠詞前綴（無冠詞則省略，**且透過真正的 API 端點驗證，非只信任子字串比對**）；欄位內部換行（含單獨 `\r`）與 Tab 字元皆正確轉換（各自獨立測試，不再共用同一個未含 Tab 的測資）；端點回應正確的 Content-Type/Content-Disposition；該語言無單字時回空檔案（200）；en/de 語言彼此獨立；`language` 缺少回 422。
- 螢幕截圖：不適用。
- 已知限制：只產生純文字 TSV，不產生 `.apkg` 二進位封裝檔（依任務卡假設，Anki 的純文字匯入已足夠且官方支援）。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用）：
  - 架構關卡（APPROVE）確認 `/export/anki`（2 段路徑）與 `/{vocabulary_id}`（1 段路徑）深度不同，不論註冊順序都不會被遮蔽（與 TASK-017 提醒的「未來假設性單段路徑」風險不同類）；順手採納兩個非阻塞建議：`_clean_field()` 補上單獨 `\r`（非 `\r\n`）的處理、端點加上 `response_class=Response` 讓 OpenAPI 正確描述回應型別（非 JSON）。
  - 安全性關卡（PASS）：唯讀重新匯出使用者自己的資料，無新增攻擊面；`Content-Disposition` 檔名只由 enum 驗證過的 `language.value` 組成，無標頭注入風險。
  - 測試關卡（CONCERNS→已補）發現兩個缺口：(1) 命名為「測試換行與 Tab 逸出」的測試實際上沒放任何 Tab 字元，Tab 替換邏輯完全沒被測到 → 拆成獨立的換行測試與 Tab 測試；(2) 德文冠詞+翻譯的組合只在純函式層級測過，整合測試只用子字串比對、且測試的是「無冠詞」分支 → 已補上透過真正 API 端點、對完整輸出行內容斷言的德文冠詞測試。
- 後續任務：無。
