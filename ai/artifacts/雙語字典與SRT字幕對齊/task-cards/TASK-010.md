# AI-Ready 任務卡

## Metadata

- 任務：TASK-010 SRT 字幕解析與上傳
- 上層規格：（同 Epic，範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：雙語字典與 SRT 字幕對齊
- 上層 User Story：SRT 字幕解析與例句對齊
- 分軌：後端
- 前置任務（dependsOn）：TASK-007
- 狀態：就緒（TASK-007 已核准 done）
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供檔案上傳端點，接收 `.srt` 字幕檔、解析成逐行時間軸與文字，整批取代該 `media_log` 底下既有的 `subtitle_line` 資料。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/media_log.py`、`backend/app/models/subtitle_line.py`（TASK-007）。
- 既有模式：延續 media_log router 的錯誤處理風格；上傳用 FastAPI 的 `UploadFile`。
- 假設：SRT 格式為標準格式（索引行、`HH:MM:SS,mmm --> HH:MM:SS,mmm` 時間軸行、一或多行文字、空行分隔區塊）；解析失敗（格式不符）回 422，不嘗試「盡量解析」。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/media_log.py`（新增子端點）、`backend/app/services/srt_parser.py`（新增，純解析邏輯，不碰 DB）、`backend/app/schemas/subtitle_line.py`（新增，回應用的簡單 schema）。
- 不得觸碰：`backend/app/models/`（表已在 TASK-007 建好）。

## 需求

- `backend/app/services/srt_parser.py`：`parse_srt(content: str) -> list[tuple[int, int, str]]`，回傳 `(start_ms, end_ms, text)` 的清單；格式不符時拋出 `SrtParseError`。
- `POST /api/v1/media-logs/{id}/subtitles`（multipart，欄位名 `file`）：
  - `media_log` 不存在 → 404。
  - 檔案非 `.srt` 副檔名或內容解析失敗（`SrtParseError`）→ 422。
  - 解析成功後：刪除該 `media_log_id` 底下所有既有 `subtitle_line`，整批插入新解析出的行，回傳 `{"media_log_id": ..., "line_count": N}`。
- `GET /api/v1/media-logs/{id}/subtitles`：列出該 `media_log` 目前已存的字幕行（依 `start_ms` 排序），供除錯與驗證用。

## 驗收標準

- 上傳一份合法的 `.srt` 內容，`subtitle_line` 表出現對應筆數的資料，`GET` 端點可依序取回。
- 重新上傳同一個 `media_log_id` 的新字幕，舊的 `subtitle_line` 全部被取代，不會新舊混雜。
- 上傳格式錯誤的內容（例如純文字檔）回 422。
- 上傳目標 `media_log_id` 不存在回 404。

## 實作備註

- `parse_srt()` 是純函式（輸入字串、輸出資料），方便獨立單元測試，不需要啟動 DB 或 HTTP。

## 驗證契約

- 單元測試：`pytest backend/tests/test_srt_parser.py`
- 整合測試：`pytest backend/tests/test_media_log_subtitles_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：限制上傳檔案大小（例如 2MB，一般劇集字幕檔遠小於此），避免異常大檔案耗盡記憶體；解析過程不執行檔案內容中的任何動態程式碼。

## 完成證據

- 變更的檔案：
  - `backend/app/services/srt_parser.py`（新增，`parse_srt()`、`SrtParseError`）
  - `backend/app/schemas/subtitle_line.py`（新增，`SubtitleLineRead`、`SubtitleUploadResult`）
  - `backend/app/api/media_log.py`（新增 `POST/GET /{media_log_id}/subtitles`）
  - `backend/requirements.txt`（新增 `python-multipart`，FastAPI `UploadFile` multipart 解析必要依賴，超出原允許檔案清單但屬必要基礎設施）
  - `backend/tests/test_srt_parser.py`、`backend/tests/test_media_log_subtitles_api.py`
- 執行過的指令：
  - `pip install "python-multipart>=0.0.9,<1.0"`
  - `pytest -q` → `84 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `POST`/`GET /api/v1/media-logs/{media_log_id}/subtitles` 已掛載
- 測試輸出：`88 passed, 1 warning in 1.02s`（審查後補測試，原始為 84 passed）。涵蓋：合法 SRT 解析與依序取回、多行文字合併、CRLF 換行相容、UTF-8 BOM 相容、重新上傳整批取代（新舊不混雜）、非 `.srt` 副檔名回 422、格式錯誤內容回 422、非 UTF-8 內容回 422、檔案超過 2MB 回 422、跨區塊亂序上傳仍依 `start_ms` 排序取回、目標 `media_log` 不存在回 404（上傳與查詢兩端點皆測）。
- 螢幕截圖：不適用。
- 已知限制：檔案大小上限 2MB（`MAX_SUBTITLE_FILE_SIZE`，改為界限讀取 `file.read(MAX+1)` 避免超量檔案先被完整讀進記憶體）；檔案編碼要求 UTF-8（含 BOM 相容），非 UTF-8 內容回 422；`parse_srt()` 對格式從嚴（不做「盡量解析」），任何區塊不符規範即整體判定失敗。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用）：
  - 架構關卡（PASS）發現：真實世界常見的 UTF-8 BOM 字幕檔會被 `decode("utf-8")` 誤判成格式錯誤（BOM 不會被 `strip()` 移除）→ 已改用 `decode("utf-8-sig")`，並補上 BOM 檔案上傳測試。
  - 安全性關卡（PASS）發現：`await file.read()` 會把整個上傳內容讀進記憶體後才檢查 2MB 上限，限制形同虛設 → 已改為 `file.read(MAX_SUBTITLE_FILE_SIZE + 1)` 界限讀取，並補上超量檔案測試。
  - 測試關卡（PASS）發現兩個任務卡明列但未覆蓋的驗收情境（檔案過大、非 UTF-8 編碼）→ 已補測試；另補上「跨區塊亂序上傳仍依 start_ms 排序」的加強測試。
- 後續任務：TASK-011 例句對齊會讀取本卡存下的 `subtitle_line`。
