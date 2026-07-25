# AI-Ready 任務卡

## Metadata

- 任務：TASK-021 影集/追劇紀錄匯出入（CSV）
- 上層規格：（Epic 範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：資料匯出入與備份
- 上層 User Story：影集/追劇紀錄匯出入（CSV）
- 分軌：後端
- 前置任務（dependsOn）：TASK-005
- 狀態：就緒
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

`media_log`（追劇/影集紀錄）的 CSV 匯出與匯入，補齊資料匯出入範圍（不只單字資料）。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/media_log.py`（既有 `MediaLogCreate`）。
- 既有模式：延續 TASK-017（單字 CSV 匯入）的「表頭列 + `csv.DictReader` + 部分成功」策略，以及 TASK-018 的匯出風格（純函式組列 + `text/csv` 回應）。
- 假設：
  - CSV 欄位對應 `MediaLogCreate`：`language,title,media_type,watched_date,duration_minutes,notes`。
  - 匯入採部分成功策略（同 TASK-017），單列失敗記錄錯誤、不中斷整批。
  - 匯出依 `language` 篩選（同既有 `list_media_logs` 慣例），欄位與匯入格式一致，方便使用者「先匯出、改一改、再匯入」的往返編輯流程。
  - 檔案大小上限 5MB（同 TASK-017）。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/media_log.py`（新增兩個端點）、`backend/app/schemas/media_log.py`（新增 `MediaLogImportResult`）。
- 不得觸碰：`backend/app/models/`、既有 CRUD 端點邏輯。

## 需求

- `POST /api/v1/media-logs/import-csv`（multipart，欄位名 `file`）：
  - 非 `.csv` 或超過 5MB → 422。
  - 逐列驗證新增，回傳 `MediaLogImportResult`：`{"created": N, "skipped": N, "errors": [...]}`。
- `GET /api/v1/media-logs/export-csv?language=en|de`：
  - 回傳 `text/csv`，`Content-Disposition: attachment; filename="media_logs_export_{language}.csv"`。
  - 欄位與匯入格式一致（含表頭列）。

## 驗收標準

- 匯出後直接把同一份檔案匯入回一個乾淨的資料庫，驗證資料列數與內容一致（往返一致性）。
- 匯入含 1 筆合法 + 1 筆缺必填欄位（例如缺 `title`）的 CSV，`created == 1`、`skipped == 1`，錯誤訊息指出列號與原因。
- 非 CSV 副檔名或超過 5MB 回 422。
- `language` 缺少時匯出端點回 422（同既有慣例）。

## 實作備註

- 匯出/匯入的欄位順序一致，這樣「匯出、編輯、匯入」的往返流程對使用者才直覺。

## 驗證契約

- 整合測試：`pytest backend/tests/test_media_log_csv_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：檔案大小上限比照 TASK-017/010；CSV 內容只做結構化解析與 ORM 參數化寫入。

## 完成證據

- 變更的檔案：
  - `backend/app/schemas/media_log.py`（新增 `MediaLogImportRowError`、`MediaLogImportResult`）
  - `backend/app/api/media_log.py`（新增 `POST /import-csv`、`GET /export-csv`，兩者皆放在 `/{media_log_id}` 之前避免被遮蔽，`export-csv` 尤其重要因為與 `/{media_log_id}` 深度相同）
  - `backend/tests/test_media_log_csv_api.py`
- 執行過的指令：
  - `pytest -q` → `175 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `POST /api/v1/media-logs/import-csv`、`GET /api/v1/media-logs/export-csv` 皆已掛載且未被 `/{media_log_id}` 遮蔽
- 測試輸出：`175 passed, 58 warnings in 2.85s`（既有 `datetime.utcnow()` deprecation，非阻塞）。涵蓋：全部合法列匯入成功、混合合法/違反必填欄位規則的部分成功（含正確列號）、非 `.csv` 副檔名回 422、超過 5MB 回 422、匯出回應 Content-Type/Content-Disposition 正確且欄位與匯入格式一致、`language` 缺少回 422、**匯出後直接匯入回去的往返一致性測試**（驗證匯出格式與匯入格式相容）。
- 螢幕截圖：不適用。
- 已知限制：沿用 TASK-017 已修正過的「欄位數多於表頭」防護（`row.pop(None, None)` 偵測 restkey，優雅跳過而非讓整批 500），現已補上專屬測試覆蓋此路徑。CSV 匯出對可能被試算表軟體解讀為公式的欄位（`title`/`media_type`/`notes` 開頭為 `= + - @` 或 tab/CR）加上前置單引號防護；若該欄位原始內容本身就以單引號開頭的公式觸發字元開頭，往返匯入後會多一個字元，屬已知、可接受的權衡。
- 後續任務：無（本卡為本 Epic 最後一張）。

## 審查關卡紀錄（2026-07-25）

- architect agent：APPROVE，附一項要求修正 — `_format_import_row_error` 型別註記與 except 元組不一致（漏了 TypeError 分支，若觸發會讓整批 500，破壞 TASK-017 保護的不變量）。已修正，比照 vocabulary.py 補上 TypeError 分支。路由順序（import-csv/export-csv 皆在 `/{media_log_id}` 之前）確認正確。
- security-reviewer agent：CONCERNS — 匯出端點對使用者可控欄位（title/media_type/notes）未過濾公式前綴，屬 CSV 公式注入風險（本任務新增的攻擊面）。已修正：新增 `_csv_safe()` 對以 `= + - @`/tab/CR 開頭的欄位加前置單引號，並補上專屬測試 `test_export_escapes_formula_like_fields`。錯誤訊息回顯 pydantic msg 一項，判定風險可接受（本機工具、非敏感資料），知悉不修。
- test-engineer agent：要求修改 — 已修正：(1) 部分成功測試補上錯誤訊息內容斷言、(2) round-trip 測試改為逐欄比對內容而非只比數量、(3) 補上 restkey（欄位數多於表頭）專屬測試、(4) 額外補上空檔案與超大檔案未寫入 DB 的邊界測試。修正後 `pytest tests/test_media_log_csv_api.py -v` 10 passed，`pytest -q` 178 passed，`ruff check .` All checks passed。
- 三個審查關卡皆已通過，核准轉 done。
