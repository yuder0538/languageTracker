# AI-Ready 任務卡

## Metadata

- 任務：TASK-007 Epic 架構基礎
- 上層規格：（Epic 範圍由 project-kickoff + 人工核准的架構規劃定義，未另立 feature-spec）
- 上層 Epic：雙語字典與 SRT 字幕對齊
- 上層 User Story：Epic 架構基礎
- 分軌：後端
- 前置任務（dependsOn）：TASK-001、TASK-002、TASK-003、TASK-004、TASK-005、TASK-006（「專案設置」Epic 全部卡片，依 project-kickoff 強制規則；另加上前一個 Epic 的全部卡片，因為本卡要在既有的 `vocabulary`/`media_log` 模型與 API 結構上擴充）
- 狀態：就緒
- 風險等級：中（資料庫 schema 變更／新增資料表，屬於高風險類別；欄位與表設計已在對話中經人工核准）
- Agent owner：claude
- 人工核准者：Niko

## 目標

為本 Epic 底下的查詢/翻譯/例句對齊功能建立共用基礎：`vocabulary` 表新增 `en_definition` 欄位、新增 `subtitle_line` 表存放解析後的字幕行，並封裝一個共用的外部 API client（timeout、統一錯誤處理），供 TASK-008~011 使用。

## 情境包（Context Pack）

- 相關檔案：`backend/app/models/vocabulary.py`、`backend/app/models/media_log.py`、`backend/alembic/versions/`。
- 既有模式：延續 TASK-003 的 SQLAlchemy 2.x 宣告式模型與 Alembic autogenerate 流程；延續 TASK-004 的 `app/api/router.py` 掛載慣例。
- 假設：
  - 字幕行的刪除策略採「整批取代」：TASK-010 重新上傳同一個 `media_log_id` 的字幕時，先刪除該 `media_log_id` 底下所有既有 `subtitle_line`，再整批插入新的，避免新舊字幕混雜。
  - `subtitle_line.media_log_id` 用 `ON DELETE CASCADE`（與 `vocabulary.media_log_id` 的 `SET NULL` 不同）：字幕行離開所屬劇集紀錄就沒有意義，媒體紀錄被刪除時字幕應一併清除；單字則要獨立保留。
  - 外部 API client 封裝用 `httpx`（`requirements.txt` 已有，供 TestClient 使用，這次拿來做真正的 outbound 呼叫）。
- 未知事項：無（範圍已在對話中核准）。
- 允許變更的檔案：`backend/app/models/subtitle_line.py`（新增）、`backend/app/models/vocabulary.py`（加欄位）、`backend/app/models/__init__.py`、`backend/app/services/__init__.py`（新增）、`backend/app/services/http_client.py`（新增）、`backend/alembic/versions/`（新遷移）。
- 不得觸碰：`backend/app/models/media_log.py`（本卡不需要改動）、`backend/app/api/media_log.py`、`backend/app/api/vocabulary.py`（現有 CRUD 端點不動，enrich 端點是後續卡片新增的檔案）。

## 需求

### `vocabulary` 表欄位新增

| 欄位 | 型別 | 限制 | 說明 |
|---|---|---|---|
| `en_definition` | Text | nullable | 英文解釋，僅 `language='en'` 使用（沿用既有「API 層驗證、DB 層不加 CHECK」慣例） |

### 新增 `subtitle_line` 表

| 欄位 | 型別 | 限制 | 說明 |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | |
| `media_log_id` | Integer | FK -> `media_log.id`, NOT NULL, index, ON DELETE CASCADE | |
| `start_ms` | Integer | NOT NULL | 字幕行開始時間（毫秒） |
| `end_ms` | Integer | NOT NULL | 字幕行結束時間（毫秒） |
| `text` | Text | NOT NULL | 字幕文字 |

### 共用外部 API client

- `backend/app/services/http_client.py`：
  - `class ExternalApiError(Exception)`：統一的外部 API 失敗例外（逾時、連線失敗、非 2xx）。
  - `def get_json(url: str, params: dict | None = None, timeout: float = 5.0) -> dict`：用 `httpx.get()`，非 2xx 或逾時／連線錯誤一律包成 `ExternalApiError` 拋出，帶原始錯誤訊息。
  - 呼叫方（TASK-008/009）負責把 `ExternalApiError` 轉成 `HTTPException(status_code=502, detail=...)`。

## 驗收標準

- `alembic upgrade head` 可從既有 schema（已有 `media_log`/`vocabulary`）平滑升級到新版本，新增 `en_definition` 欄位與 `subtitle_line` 表；`alembic downgrade -1` 可回滾到本卡之前的狀態。
- `subtitle_line.media_log_id` 的 `ON DELETE CASCADE` 行為：刪除 `media_log` 後，該筆所有 `subtitle_line` 一併消失（透過真實 SQLite 連線 + `PRAGMA foreign_keys=ON` 驗證，延續 TASK-003 的驗證方式）。
- `get_json()` 對逾時／連線失敗／非 2xx 三種情況皆拋出 `ExternalApiError`（可用 `httpx` 的 mock transport 或指向不存在的 port 測試，不依賴真實外部服務）。
- 既有 `pytest` 測試（TASK-001~006 累積的全部測試）不受影響，全數通過。

## 實作備註

- 這張卡只建模型／遷移／client 封裝，不建任何 enrich 端點（那是 TASK-008~011 的範圍）。
- `subtitle_line` 不建 CRUD API；TASK-010 會直接提供「上傳並整批取代」的單一端點，不需要通用 CRUD。

## 驗證契約

- 單元測試：`pytest backend/tests/test_http_client.py`
- 整合測試：`pytest backend/tests/test_epic2_migration.py`（`alembic upgrade head`/`downgrade -1`、`subtitle_line` CASCADE 行為）
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`pip install -r backend/requirements.txt` 成功。
- 螢幕截圖：不適用。
- 安全性檢查：`get_json()` 對外部回應內容不做 `eval`/動態執行，僅做 JSON 解析；逾時預設值避免請求無限期卡住拖垮伺服器。

## 完成證據

- 變更的檔案：
  - `backend/app/models/vocabulary.py`（新增 `en_definition`）
  - `backend/app/models/subtitle_line.py`（新增 `SubtitleLine`）、`app/models/__init__.py`
  - `backend/app/services/__init__.py`、`app/services/http_client.py`（`get_json()` 支援注入 `httpx.Client` 供測試用）
  - `backend/alembic/versions/d2f0916462fe_add_en_definition_and_subtitle_line.py`
  - `backend/tests/test_http_client.py`、`backend/tests/test_epic2_migration.py`
- 執行過的指令：
  - `alembic revision --autogenerate -m "add en_definition and subtitle_line"`
  - `alembic upgrade head`（套用到 dev DB）
  - `pytest -q` → `48 passed`
  - `ruff check .` → `All checks passed!`
- 測試輸出：`48 passed, 1 warning in 0.90s`（同前幾卡的 httpx deprecation 警告，非本卡範圍）。涵蓋：schema 升級/降級一步、`subtitle_line` 的 `ON DELETE CASCADE`、`get_json()` 對成功/非2xx/逾時/連線失敗/非-JSON body 五種情況、陣列回應正確透傳。
- 螢幕截圖：不適用。
- 已知限制：`get_json()` 加了 `client` 參數方便測試注入 `httpx.MockTransport`，正式呼叫路徑不受影響（未傳入時走原本的 `httpx.get()`）。
- 審查關卡發現與修正（架構+安全性 agent 審查後套用）：
  - 安全性關卡發現 `get_json()` 對非 JSON body／3xx 回應會讓 `response.json()` 的 `ValueError` 未包裝直接洩漏，破壞「呼叫方只需處理 `ExternalApiError`」的契約 → 已修正為捕捉並包成 `ExternalApiError`，並補上 `test_get_json_raises_on_non_json_body` 測試。
  - 安全性關卡建議明確設定 `follow_redirects=False`（原本僅是 httpx 預設值，未顯式宣告）→ 已在兩個呼叫路徑顯式設定。
  - 架構關卡發現 `get_json()` 回傳型別標注為 `dict`，但主要目標 Free Dictionary API 回傳頂層陣列 → 已改為 `Any`，並補上 `test_get_json_returns_list_body` 驗證陣列回應正確透傳。
  - 架構關卡建議（記錄不強制修正）：`SubtitleLine` 未含 `created_at`/`updated_at`（因整批取代生命週期，時間戳意義不大，屬有意識取捨）；SQLite Alembic 遷移未啟用 `render_as_batch`（目前 SQLite 3.45 相容，非阻塞）。
  - 安全性關卡對 TASK-008/009 的必要控制建議：呼叫端點在把使用者輸入（headword）組進 URL path 前，需用 `urllib.parse.quote(..., safe="")` 做 URL-safe encoding，避免特殊字元破壞請求。
- 後續任務：TASK-008 英文單字自動查詢、TASK-009 德文→繁中翻譯、TASK-010 SRT 字幕上傳。
