# AI-Ready 任務卡

## Metadata

- 任務：TASK-019 全資料庫備份
- 上層規格：（Epic 範圍已於對話中核准，未另立 feature-spec）
- 上層 Epic：資料匯出入與備份
- 上層 User Story：全資料庫備份
- 分軌：後端
- 前置任務（dependsOn）：TASK-001、TASK-002
- 狀態：就緒
- 風險等級：中（直接操作底層 SQLite 檔案，屬於基礎設施類別，雖是唯讀備份但仍需仔細處理併發安全）
- Agent owner：claude
- 人工核准者：Niko

## 目標

提供下載整個 SQLite 資料庫備份檔的端點，避免單機資料遺失後求助無門。

## 情境包（Context Pack）

- 相關檔案：`backend/app/core/config.py`（`database_url`）、`backend/app/core/db.py`（既有 `engine`）。
- 既有模式：新建 `backend/app/api/backup.py` 獨立 router（與 `reviews.py` 一樣，這是跨資源的系統層級操作，不屬於任何單一 CRUD 資源）。
- 假設：
  - 用 Python 標準庫 `sqlite3` 的 `Connection.backup()` API 做「熱拷貝」到暫存檔，而不是直接讀取資料庫檔案的位元組——直接複製檔案位元組可能在寫入進行到一半時拷貝到不一致的狀態，`backup()` API 是 SQLite 官方建議的線上備份方式。
  - 備份檔透過 `FileResponse` 回傳後，用 `BackgroundTask` 清掉暫存檔，避免暫存目錄累積垃圾檔案。
  - 資料庫路徑從 `settings.database_url`（`sqlite:///relative/path` 格式）解析出實際檔案路徑，純函式 `_sqlite_path_from_url()` 供本卡與 TASK-020 共用。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/backup.py`（新增）、`backend/app/api/router.py`（掛載）。
- 不得觸碰：`backend/app/core/db.py`（本卡只讀取 `settings.database_url` 解析路徑，不動既有的 engine 初始化邏輯）。

## 需求

- `GET /api/v1/backup/export`：
  - 回傳 `application/octet-stream`，`Content-Disposition: attachment; filename="immersion_tracker_backup_{YYYYMMDD_HHMMSS}.db"`。
  - 內容為透過 `sqlite3.Connection.backup()` 產生的完整資料庫快照。

## 驗收標準

- 呼叫端點下載備份檔，用 `sqlite3` 開啟該備份檔，驗證裡面的資料表與資料列數與原資料庫一致。
- 備份過程中對資料庫進行寫入（模擬併發），驗證備份檔仍是結構完整、可正常開啟的 SQLite 檔案（不會拷貝到損毀的中間狀態）。
- 回應下載完成後，暫存檔案確實被清除（不留垃圾檔案）。

## 實作備註

- 這是 TASK-020（還原）的前置：還原功能會重用本卡的備份邏輯（在還原前先對現有資料庫做一次內部安全備份）。

## 驗證契約

- 整合測試：`pytest backend/tests/test_backup_export_api.py`
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：唯讀操作，不修改任何資料；暫存檔存放於系統暫存目錄，回應後立即清除，不長期留存使用者資料副本。

## 完成證據

- 變更的檔案：
  - `backend/app/api/backup.py`（新增，`sqlite_path_from_url()`、`create_backup_file()`、`GET /export`）
  - `backend/app/api/router.py`（掛載 `backup` router）
  - `backend/tests/test_backup_export_api.py`
- 執行過的指令：
  - `pytest -q` → `158 passed`
  - `ruff check .` → `All checks passed!`
  - 以 `TestClient` 讀取 `/openapi.json` 確認 `GET /api/v1/backup/export` 已掛載
- 測試輸出：`160 passed, 58 warnings in 2.44s`（審查後補測試與修正，原始 158 passed；既有 `datetime.utcnow()` deprecation，非阻塞）。涵蓋：下載的備份檔用 `sqlite3` 開啟驗證資料表與資料列數與來源一致、Content-Type/Content-Disposition 正確；備份過程中對來源資料庫進行寫入（透過 `backup()` 的 `progress` callback 模擬併發寫入時機），驗證備份檔仍是結構完整（**真的 fetch `PRAGMA integrity_check` 的結果並斷言為 `"ok"`**，而非只是執行指令不看結果）、可正常開啟的 SQLite 檔案；回應完成後暫存檔確實被清除；備份過程失敗時暫存檔也會被清除（不洩漏）；來源資料庫檔案不存在時回 404（而非安靜地產生一份空備份）。
- 螢幕截圖：不適用。
- 已知限制：測試不透過既有 `client`/`db_session`（in-memory）fixture，因為那個 fixture 跟正式 `engine` 的檔案路徑無關；改用獨立 `TestClient(app)` 搭配對 `app.api.backup.get_settings` 的 monkeypatch，指向 `tmp_path` 底下的真實 SQLite 檔案，直接驗證檔案系統層級的行為（與任務卡「實作備註」一致）。併發寫入測試中，若備份的讀鎖與模擬寫入短暫衝突，寫入端設定 `timeout=0.1` 快速失敗而非重試 5 秒（避免測試因 SQLite 預設鎖重試機制而變慢或看似卡住）。不曾對外開放（僅本地單人工具），未加身分驗證；已記錄為未來若要對外開放/加認證時必須先處理的已知風險。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用）：
  - 架構關卡與安全性關卡**各自獨立**發現同一個真實 bug：`create_backup_file()` 若在建立暫存檔之後、`FileResponse` 建構之前拋出例外（例如來源鎖住超過 timeout、磁碟已滿），暫存檔的 `BackgroundTask` 清除邏輯永遠不會被掛上，暫存檔會直接洩漏在系統暫存目錄，違反任務卡自己承諾的「不長期留存使用者資料副本」→ 已用 `try/except BaseException: os.remove(tmp_path); raise` 包起來，並補上模擬備份失敗的回歸測試。
  - 架構關卡額外發現（記錄並修正）：來源資料庫檔案不存在時，`sqlite3.connect()` 會安靜建立一個空檔案當作「備份」，讓使用者誤以為備份成功但其實是空的 → 已加上 `os.path.exists()` 檢查，不存在時回 404，並補測試。
  - 安全性關卡（CONCERNS，記錄不需修正）：本端點無身分驗證即可下載整個資料庫，比起其他回傳篩選後 JSON 子集的端點是更大的曝露面；在目前「本地單人工具、全站無身分驗證」的既定模型下可接受，但記錄為未來對外開放前必須處理的已知風險。
  - 測試關卡（CONCERNS→已修）發現真實 bug：併發測試裡 `verify_conn.execute("PRAGMA integrity_check")` 沒有 `fetch` 結果，等於完全沒在檢查——就算備份檔案結構損毀，這個測試也會通過 → 已修正為 `fetchone()[0] == "ok"`。
- 後續任務：TASK-020 全資料庫還原會重用本卡的 `create_backup_file()`。
