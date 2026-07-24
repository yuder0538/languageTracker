# AI-Ready 任務卡

## Metadata

- 任務：TASK-012 SRS 排程資料模型與核心演算法
- 上層規格：（Epic 範圍由 project-kickoff 產出，未另立 feature-spec）
- 上層 Epic：雙語 SRS 與 Flashcard 測驗
- 上層 User Story：SRS 排程資料模型與核心演算法
- 分軌：後端
- 前置任務（dependsOn）：TASK-001、TASK-002、TASK-003、TASK-006（「專案設置」Epic 全部卡片，依 project-kickoff 強制規則；另加 TASK-006，因為本卡要在既有的 `vocabulary` 表上擴充欄位）
- 狀態：就緒（schema 設計已於對話中經人工核准）
- 風險等級：中（資料庫 schema 變更／新增資料表，屬於高風險類別；欄位設計已核准）
- Agent owner：claude
- 人工核准者：Niko

## 目標

為本 Epic 底下的複習佇列、作答評分、統計功能建立共用基礎：`vocabulary` 表新增 SRS 排程欄位、新增 `review_log` 表記錄複習歷史，並封裝簡化版 SM-2 間隔重複演算法的純函式，供 TASK-013~015 使用。

## 情境包（Context Pack）

- 相關檔案：`backend/app/models/vocabulary.py`、`backend/alembic/versions/`。
- 既有模式：延續 TASK-003 的 SQLAlchemy 2.x 宣告式模型與 Alembic autogenerate 流程；延續 TASK-007 直接擴充 `vocabulary` 表欄位、另建關聯表的做法（`subtitle_line` 之於 `review_log`）。
- 假設：
  - SRS 狀態直接加在 `vocabulary` 表（而非另立 1:1 關聯表），因為每個單字恰好對應一組排程狀態，加欄位比額外 join 更簡單，與既有 `ipa`/`en_definition`/`translation_zh` 等擴充欄位的做法一致。
  - `srs_next_review_at` 為 `null` 代表「尚未排程」（全新單字），複習佇列查詢時將其視為立即到期。
  - 演算法為簡化版 SM-2：`grade` 為 `again`/`hard`/`good`/`easy` 四級；`again` 重置 `srs_interval_days=1`、`srs_repetitions=0`、`srs_lapses += 1`；其餘依 `srs_ease_factor` 遞增間隔（`hard` 係數略降、`good` 標準遞增、`easy` 額外加成），`srs_ease_factor` 下限鎖在 1.3（SM-2 慣例）。
  - `review_log` 為 append-only 歷史記錄，不提供刪除/修改端點（本卡不建 CRUD API，只建表）。
- 未知事項：無（範圍已於對話中核准）。
- 允許變更的檔案：`backend/app/models/vocabulary.py`（加欄位）、`backend/app/models/review_log.py`（新增）、`backend/app/models/enums.py`（新增 `ReviewGrade` enum）、`backend/app/models/__init__.py`、`backend/app/services/srs.py`（新增，核心演算法純函式）、`backend/alembic/versions/`（新遷移）。
- 不得觸碰：`backend/app/api/`（本卡不建任何端點，那是 TASK-013/014 的範圍）、`backend/app/models/media_log.py`、`backend/app/models/subtitle_line.py`。

## 需求

### `vocabulary` 表欄位新增

| 欄位 | 型別 | 限制 | 說明 |
|---|---|---|---|
| `srs_interval_days` | Integer | NOT NULL, default 0 | 距下次複習的天數間隔；0 = 新卡/未排程 |
| `srs_ease_factor` | Float | NOT NULL, default 2.5 | 難度係數（SM-2 標準起始值） |
| `srs_repetitions` | Integer | NOT NULL, default 0 | 連續答對次數 |
| `srs_lapses` | Integer | NOT NULL, default 0 | 學會後又忘記的次數 |
| `srs_next_review_at` | DateTime | nullable | null = 尚未排程（立即可複習） |
| `srs_last_reviewed_at` | DateTime | nullable | 上次複習時間 |

### 新增 `review_log` 表

| 欄位 | 型別 | 限制 | 說明 |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | |
| `vocabulary_id` | Integer | FK -> `vocabulary.id`, NOT NULL, index, ON DELETE CASCADE | |
| `reviewed_at` | DateTime | NOT NULL, server_default now() | |
| `grade` | Enum(`again`/`hard`/`good`/`easy`) | NOT NULL | |
| `interval_days_after` | Integer | NOT NULL | 該次複習後算出的新間隔天數，供除錯與統計用 |

### 核心演算法

- `backend/app/services/srs.py`：
  - `@dataclass SrsState`：`interval_days: int`、`ease_factor: float`、`repetitions: int`、`lapses: int`。
  - `def schedule_next_review(state: SrsState, grade: ReviewGrade) -> SrsState`：純函式，輸入目前狀態與評分，回傳新狀態（含新的 `interval_days`/`ease_factor`/`repetitions`/`lapses`）；不碰 DB、不算日期，日期換算（`interval_days` → `next_review_at`）交給呼叫方（TASK-014）處理。

## 驗收標準

- `alembic upgrade head` 可從既有 schema 平滑升級，新增六個 `vocabulary` 欄位與 `review_log` 表；`alembic downgrade -1` 可回滾。
- `review_log.vocabulary_id` 的 `ON DELETE CASCADE` 行為：刪除 `vocabulary` 後，該筆所有 `review_log` 一併消失（真實 SQLite 連線 + `PRAGMA foreign_keys=ON` 驗證）。
- `schedule_next_review()`：`again` 一律重置間隔為 1 天、`repetitions` 歸零、`lapses` 遞增；`good`/`easy`/`hard` 依 ease factor 遞增間隔且 `repetitions` 遞增；`ease_factor` 不會低於 1.3 下限。
- 既有 `pytest` 測試（TASK-001~011 累積的全部測試）不受影響，全數通過。

## 實作備註

- 這張卡只建模型／遷移／演算法純函式，不建任何 API 端點（那是 TASK-013~015 的範圍）。
- `review_log` 不建 CRUD API；只有 TASK-014 的評分端點會寫入它，TASK-015 的統計端點會讀取它。

## 驗證契約

- 單元測試：`pytest backend/tests/test_srs_algorithm.py`
- 整合測試：`pytest backend/tests/test_srs_migration.py`（`alembic upgrade head`/`downgrade -1`、`review_log` CASCADE 行為）
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`pip install -r backend/requirements.txt` 成功；`uvicorn app.main:app` 正常啟動。
- 螢幕截圖：不適用。
- 安全性檢查：純函式不涉及外部輸入／網路；`review_log` 為內部記錄表，無使用者直接寫入路徑（本卡不開端點）。

## 完成證據

- 變更的檔案：
  - `backend/app/models/vocabulary.py`（新增六個 `srs_*` 欄位）
  - `backend/app/models/review_log.py`（新增）、`app/models/__init__.py`
  - `backend/app/models/enums.py`（新增 `ReviewGrade`）
  - `backend/app/services/srs.py`（新增，`SrsState`、`schedule_next_review()`）
  - `backend/alembic/versions/3bdbced4ba98_add_srs_scheduling_fields_and_review_log.py`（手動補上 NOT NULL 欄位的 `server_default`，autogenerate 預設不會加）
  - `backend/tests/test_srs_algorithm.py`、`backend/tests/test_srs_migration.py`
  - `backend/tests/test_epic2_migration.py`（修正既有測試：原本 `command.upgrade(alembic_config, "head")` 後 `downgrade("-1")` 假設 head 就是 epic2 的 migration，本卡在其後新增一版 migration 後這個假設不成立，改為直接指定 `"d2f0916462fe"` 這個 revision id）
- 執行過的指令：
  - `alembic revision --autogenerate -m "add srs scheduling fields and review_log"`
  - `alembic upgrade head`（套用到 dev DB，DB 內已有 1 筆既有 `vocabulary` 資料列）
  - `pytest -q` → `105 passed`
  - `ruff check .` → `All checks passed!`
- 測試輸出：`108 passed, 1 warning in 1.77s`（審查後補測試，原始為 105 passed）。涵蓋：SM-2 演算法（again 重置/lapses 遞增、首次與第二次複習的固定間隔、第三次起依 ease factor 遞增、hard/easy 相對 good 的間隔差異、ease factor 下限 1.3 從多個起始值測試皆不會再往下）、schema 升級/降級、`review_log` CASCADE、新資料列與**既有資料列**（migration 前就存在的 row）的 SRS 欄位預設值皆正確 backfill。
- 螢幕截圖：不適用。
- 已知限制：autogenerate 產生的 `add_column` 對 NOT NULL 欄位預設不含 `server_default`，若表內已有資料會在 SQLite 上失敗——已手動補上（`0`/`2.5`/`0`/`0`），並補上自動化測試重現「migration 前就有資料列」的情境驗證 backfill 正確（而不只是手動驗證過一次的 dev DB）。
- 審查關卡發現與修正（架構+安全性+測試 agent 審查後套用）：
  - 架構關卡（APPROVE）發現：本卡新寫的 `test_srs_migration.py::test_downgrade_one_step_removes_srs_changes` 犯了跟剛修好的 `test_epic2_migration.py` 一模一樣的錯——用 `upgrade(alembic_config, "head")` 再 `downgrade("-1")`，一旦 TASK-013+ 在其後新增 migration 就會壞掉 → 已改為明確指定 `"3bdbced4ba98"` revision id。
  - 測試關卡（CONCERNS→已補）發現兩個缺口：(1) 沒有測試重現「migration 前就有既有資料列」情境，等於這卡手動修正的 `server_default` bug 沒有自動化回歸保護 → 已補 `test_upgrade_backfills_existing_rows_with_default_srs_values`；(2) ease factor 下限只從單一起始值測試 → 已補「已在下限」與「遠高於下限」兩個額外起始值案例。
  - 安全性關卡（PASS）：本卡無 API 端點，無新增攻擊面；`server_default` 為硬編碼常數，非外部輸入，無注入風險。
- 後續任務：TASK-013 複習佇列 API、TASK-014 複習作答評分 API、TASK-015 複習統計與進度追蹤。
