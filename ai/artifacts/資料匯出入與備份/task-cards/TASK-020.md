# AI-Ready 任務卡

## Metadata

- 任務：TASK-020 全資料庫還原
- 上層規格：（Epic 範圍已於對話中核准，未另立 feature-spec；還原前自動備份+confirm 參數兩項安全設計已於對話中核准）
- 上層 Epic：資料匯出入與備份
- 上層 User Story：全資料庫還原
- 分軌：後端
- 前置任務（dependsOn）：TASK-001、TASK-002、TASK-019
- 狀態：就緒
- 風險等級：高（會整批覆蓋使用者現有資料，且需要在執行中的行程裡安全換掉底層 SQLite 檔案；不可逆操作類別，已在對話中與人工確認安全設計）
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供上傳備份檔還原資料庫的端點，且做到「不會因為傳錯檔案就求助無門」：還原前自動備份現有資料、上傳檔案格式錯誤時不觸碰現有資料、且需要明確的 `confirm=true` 才會真的執行。

## 情境包（Context Pack）

- 相關檔案：`backend/app/api/backup.py`（TASK-019）、`backend/app/core/db.py`（既有 `engine`，本卡需要呼叫 `engine.dispose()`）。
- 既有模式：延續 TASK-019 的備份邏輯（`sqlite3.Connection.backup()`）與 TASK-010 的檔案上傳驗證風格。
- 假設：
  - 驗證上傳檔案：檢查檔頭魔數 `b"SQLite format 3\x00"`（前 16 bytes），並用獨立的 `sqlite3.connect()`（不透過 SQLAlchemy engine）開啟該上傳內容、檢查 `sqlite_master` 是否含 `vocabulary`、`media_log` 這兩張核心資料表；任一檢查失敗回 422，且**完全不觸碰現有資料庫**。
  - 通過驗證後：先用 TASK-019 的備份邏輯把現有資料庫備份到 `backend/data/` 目錄下的 `immersion_tracker.before-restore-{timestamp}.db`（人工可事後手動救援用），再呼叫 `engine.dispose()` 釋放連線池持有的檔案控制代碼，最後用 `os.replace()` 把上傳內容原子性地寫入正式資料庫路徑（同一個檔案系統內的 rename 是原子操作，不會有「寫一半」的中間狀態）。
  - `confirm` 為必填 query 參數，只有明確傳 `confirm=true` 才會執行；缺少或非 `true` 回 422，且不處理上傳的檔案內容（避免瀏覽器預先載入、意外點擊等情況觸發真正的還原）。
  - 還原完成後，後續請求會拿到新檔案的內容（`engine` 物件本身不重建，只是連線池被清空，下次使用時會針對同一個路徑重新開啟連線，讀到的自然是新檔案內容）。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/backup.py`（新增端點，與 TASK-019 同檔案）。
- 不得觸碰：`backend/app/core/db.py`（不重寫既有的 engine 初始化或連線管理邏輯，只呼叫既有的 `engine.dispose()`）。

## 需求

- `POST /api/v1/backup/restore?confirm=true`（multipart，欄位名 `file`）：
  - `confirm` 不是 `true` → 422（「需要 confirm=true 才會執行還原，這是不可逆操作」），不處理檔案。
  - 上傳檔案非 SQLite 格式，或缺少 `vocabulary`/`media_log` 資料表 → 422（「檔案不是合法的資料庫備份檔」），不觸碰現有資料庫。
  - 驗證通過：依序執行「備份現有資料庫 → 釋放連線 → 原子性換檔」，回傳 `{"restored": true, "safety_backup_filename": "immersion_tracker.before-restore-{timestamp}.db"}`。

## 驗收標準

- 上傳一份合法的備份檔（例如用 TASK-019 產生的備份），還原後查詢資料庫內容與備份檔內容一致；且 `data/` 目錄下出現一份還原前的安全備份檔。
- 上傳格式錯誤的檔案（例如純文字檔）回 422，且事後查詢資料庫內容與還原前完全一致（未被觸碰）。
- 不帶 `confirm=true`（或帶 `confirm=false`）呼叫回 422，且資料庫與安全備份都不受影響。
- 上傳一份缺少 `vocabulary`/`media_log` 表的合法 SQLite 檔（例如空白資料庫）回 422，不執行還原。

## 實作備註

- 本卡的整合測試不透過既有 `client`/`db_session`（in-memory）fixture，因為那個 fixture 用 dependency override 指向一個跟正式 `engine` 無關的記憶體資料庫，測不到「真的把檔案換掉」這件事——改用獨立的 `TestClient(app)` 搭配對 `_sqlite_path_from_url()`／`get_settings()` 的 monkeypatch，指向 `tmp_path` 底下的真實檔案，直接驗證檔案系統層級的行為。

## 驗證契約

- 整合測試：`pytest backend/tests/test_backup_restore_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：上傳內容先驗證合法性才觸碰現有資料庫；`confirm=true` 防止意外觸發；還原前自動安全備份，降低誤操作的資料遺失風險；`os.replace()` 提供原子性換檔，避免「寫一半」造成資料庫損毀。

## 完成證據

- 變更的檔案：
  - `backend/app/schemas/backup.py`（新增，`RestoreResult`）
  - `backend/app/api/backup.py`（新增 `_validate_restore_upload()`、`POST /restore`）
  - `backend/tests/test_backup_restore_api.py`
- 執行過的指令：
  - `pytest -q` → `166 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `POST /api/v1/backup/restore` 已掛載
- 測試輸出：`168 passed, 58 warnings in 2.80s`（審查後補測試與修正，原始 166 passed；既有 `datetime.utcnow()` deprecation，非阻塞）。涵蓋：合法備份檔還原後，查詢新資料庫內容確認已更新、且同目錄下產生的安全備份檔內容為還原前的舊資料且通過 `PRAGMA integrity_check`；非 SQLite 檔案／缺少必要資料表／`confirm` 缺少或為 `false`／超過 50MB，皆回 422 且用 **SHA-256 雜湊比對**確認現有資料庫檔案逐位元組完全未受影響（而非只查單一欄位值）；`confirm` 未通過時完全不讀取上傳檔案內容（spy 監控 `UploadFile.read()` 呼叫次數為 0）；**安全備份步驟本身失敗時**，現有資料庫保持逐位元組不變、且 `engine.dispose()` 從未被呼叫（證明還原的「不可逆點」確實只在檔案真正被換掉的那一刻，之前任何步驟失敗都是安全中止）。
- 螢幕截圖：不適用。
- 已知限制：安全備份邏輯無條件呼叫 `create_backup_file()`（不因應用程式初次啟動、live DB 檔案尚未建立而略過）——若目標檔案不存在，`sqlite3.connect()` 會視為建立一份空資料庫來源，產生一份空的「安全備份」，這在正式環境中幾乎不會發生（本專案任何一次請求都會先觸發 DB 連線、建立資料庫檔案），視為可接受的邊界情況。`engine.dispose()` 到 `os.replace()` 之間有極短的併發時間窗，若剛好有其他請求在這期間重新開啟連線，Windows 上 `os.replace()` 可能因檔案被佔用而失敗——但這會安全地中止（現有資料庫不受影響、暫存檔會被清除、回 500），不會造成資料損毀，記錄為本地單人工具下可接受的已知風險。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用，本卡為高風險，審查特別嚴格）：
  - 架構關卡（APPROVE）：逐步追蹤確認「不可逆點」精準落在 `os.replace()` 那一行，之前任何步驟失敗都不會讓現有資料庫進入部分毀損狀態；`engine.dispose()` 在寫入前呼叫、之後若寫入失敗，引擎只是連線池被清空、下次請求會對「完全沒變」的原始檔案重新連線，不會有問題。額外建議：驗證只檢查資料表名稱、沒檢查 schema 版本相容性 → 已加入 `alembic_version` 表存在檢查（非完整版本比對，但能擋掉明顯不相容的舊/怪檔案）。
  - 安全性關卡（PASS，兩個低嚴重度提醒）：確認最嚴重的「透過檔名做任意路徑寫入」完全不存在（檔名從未被用來組路徑）；`confirm=true` 檢查確實在讀取檔案內容之前。提醒安全備份檔案預設權限 0644（世界可讀）→ 已改用 `os.open(..., O_CREAT|O_EXCL, 0o600)` 預先建立限制權限的檔案，再讓 sqlite3 連線寫入。
  - 測試關卡（CONCERNS→已修，本卡唯一的阻擋等級發現）：完全沒有測試驗證「安全備份步驟本身失敗時，現有資料庫保持不變、`engine.dispose()` 沒被呼叫」這個最關鍵的安全性質 → 已補上 `test_restore_aborts_and_stays_contained_when_safety_backup_fails`。另補：`confirm` 未通過時驗證 `UploadFile.read()` 從未被呼叫；所有「應該沒被觸碰」的斷言從只查單一欄位值改為 SHA-256 雜湊比對整個檔案。
- 後續任務：無。
