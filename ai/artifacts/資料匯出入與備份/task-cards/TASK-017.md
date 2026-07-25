# AI-Ready 任務卡

## Metadata

- 任務：TASK-017 單字資料匯入（CSV）
- 上層規格：（Epic 範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：資料匯出入與備份
- 上層 User Story：單字資料匯入（CSV）
- 分軌：後端
- 前置任務（dependsOn）：TASK-001、TASK-002、TASK-003（「專案設置」Epic 全部卡片，依 project-kickoff 強制規則；本卡是這個 Epic 最先建立的卡片）、TASK-006（Vocabulary CRUD API，本卡匯入邏輯依賴既有的驗證規則）
- 狀態：就緒
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供 CSV 檔案上傳端點，批次新增單字，不需一筆一筆手動輸入；單一列格式錯誤不影響其他列的匯入。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/vocabulary.py`（既有 `VocabularyCreate`、`validate_language_specific_fields`、`_validate_media_log_language`）。
- 既有模式：延續 TASK-010 檔案上傳（`UploadFile`、2MB 上限、界限讀取避免記憶體耗盡）的做法；每列驗證邏輯直接複用 `create_vocabulary` 既有的驗證函式，不重造。
- 假設：
  - CSV 需含表頭列，欄位對應 `VocabularyCreate`：`language,headword,part_of_speech,translation_zh,example_sentence,media_log_id,ipa,de_artikel,de_plural,de_conjugation,notes`；欄位順序不拘（用 `csv.DictReader`），缺的非必填欄位留空即可。
  - 採「部分成功」策略：單一列驗證失敗（缺必填欄位、語言特化欄位規則違反、`media_log_id` 對應的語言不符）只記錄該列錯誤並跳過，不中斷整批匯入；全部驗證通過的列一次性 commit。
  - 檔案大小上限 5MB（CSV 通常遠小於此，防止異常大檔案耗盡記憶體，做法比照 TASK-010）。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/vocabulary.py`（新增端點）、`backend/app/schemas/vocabulary.py`（新增 `VocabularyImportResult`）。
- 不得觸碰：`backend/app/models/`、既有的 CRUD/enrich 端點邏輯。

## 需求

- `POST /api/v1/vocabulary/import-csv`（multipart，欄位名 `file`）：
  - 非 `.csv` 副檔名 → 422。
  - 檔案超過 5MB → 422。
  - 逐列驗證並新增：驗證失敗的列記錄 `{"row": 列號, "message": "..."}`，繼續處理下一列。
  - 回傳 `VocabularyImportResult`：`{"created": N, "skipped": N, "errors": [...]}`。

## 驗收標準

- 上傳含 5 筆合法資料的 CSV，`created == 5`，資料庫確實新增 5 筆。
- 上傳含 1 筆合法 + 1 筆違反語言特化欄位規則（例如 en 卻填 de_artikel）的 CSV，`created == 1`、`skipped == 1`，`errors` 內容指出是第幾列、原因為何。
- `media_log_id` 指向不存在或語言不符的媒體紀錄 → 該列跳過並記錄錯誤，不中斷整批。
- 非 `.csv` 副檔名回 422；超過 5MB 回 422。

## 實作備註

- 逐列驗證直接呼叫既有的 `validate_language_specific_fields()`／`_validate_media_log_language()`，用 `try/except ValueError`／`HTTPException` 包起來轉成錯誤列表項目，不重複實作規則。

## 驗證契約

- 整合測試：`pytest backend/tests/test_vocabulary_import_csv_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：檔案大小上限比照 TASK-010 用界限讀取；CSV 內容只做結構化欄位解析與 ORM 參數化寫入，不執行任何動態程式碼。

## 完成證據

- 變更的檔案：
  - `backend/app/schemas/vocabulary.py`（新增 `VocabularyImportRowError`、`VocabularyImportResult`）
  - `backend/app/api/vocabulary.py`（新增 `POST /import-csv`）
  - `backend/tests/test_vocabulary_import_csv_api.py`
- 執行過的指令：
  - `pytest -q` → `142 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `POST /api/v1/vocabulary/import-csv` 已掛載
- 測試輸出：`143 passed, 58 warnings in 2.36s`（審查後補測試與修正，原始 142 passed；既有 `datetime.utcnow()` deprecation，非阻塞）。涵蓋：全部合法列匯入成功（含 DE 列的 `de_artikel` 正確持久化，用查 DB 而非只信任回應數字驗證）、混合合法/違反語言特化欄位規則的部分成功（含正確列號、且查 DB 確認只真的新增 1 筆）、`media_log_id` 不存在時該列跳過（含錯誤訊息內容檢查、查 DB 確認 0 筆）、欄位數多於表頭的列被優雅跳過而非讓整批 500、非 `.csv` 副檔名回 422、超過 5MB 回 422。
- 螢幕截圖：不適用。
- 已知限制：驗證完全在 `db.add()` 之前完成（先建構 `VocabularyCreate` 並檢查 `media_log_id`），確保單列失敗不需要 rollback、也不會波及同批次已驗證通過的其他列；全部通過驗證的列在迴圈結束後一次性 `commit()`。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用）：
  - 安全性關卡與架構關卡**各自獨立**發現同一個真實 bug：CSV 某列若欄位數多於表頭，`csv.DictReader` 會把多餘欄位塞進 key 為 `None` 的 restkey，導致 `VocabularyCreate(**cleaned)` 拋出 `TypeError`（不在原本的 `except` 清單內），使整批上傳直接 500、違反「單列失敗不影響其他列」的設計初衷 → 已修正為偵測 restkey 並將該列記錄為錯誤、優雅跳過，並補上對應測試。
  - 架構關卡額外提醒（記錄供後續任務參考，非本卡問題）：Starlette 對 `/{vocabulary_id}` 是用字串正則匹配、之後才做 int 型別驗證失敗回 422（不會 fallback 試下一條路由）；未來若要在 `/vocabulary` 底下加同深度的靜態路徑（例如假設性的 `GET /vocabulary/export-csv`），須注意路由註冊順序或改用更深一層路徑（TASK-018 的 `/export/anki` 已經是後者，不受影響）。
  - 測試關卡（CONCERNS→已補）：多筆測試只信任回應內容的 `created`/`skipped` 數字、未實際查 DB 驗證持久化狀態 → 已補上查 DB 的斷言（含 DE 列內容、部分成功後的實際筆數、media_log_id 錯誤訊息內容）。
- 後續任務：無。
