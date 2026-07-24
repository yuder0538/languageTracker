# AI-Ready 任務卡

## Metadata

- 任務：TASK-003 核心資料模型基礎
- 上層規格：（無，Epic 0 直接由 project-kickoff 產出）
- 上層 Epic：專案設置
- 上層 User Story：核心資料模型基礎
- 分軌：後端
- 前置任務（dependsOn）：TASK-001、TASK-002
- 狀態：草稿（待 TASK-001、TASK-002 完成後轉就緒；且需人工核准資料表欄位設計後才可實作）
- 風險等級：中（資料庫 schema／遷移屬於高風險類別，且日後變更成本高，故要求人工先核准欄位設計）
- Agent owner：claude
- 人工核准者：Niko

## 目標

用 SQLAlchemy 建立支援 `en`／`de` 語言隔離、且各自帶有語言特化欄位的 `media_log` 與 `vocabulary` 資料表，並用 Alembic 建立初始遷移，讓 SQLite 資料庫檔案可從零建立出這兩張表。這是後續所有 Epic（CRUD API、字典整合、SRS、UI 統計）共用的資料基礎，欄位設計錯誤會讓後面所有 Epic 連帶要改，因此本卡實作前須先經人工核准欄位設計。

## 情境包（Context Pack）

- 相關檔案：`backend/app/models/`、`backend/app/core/config.py`（TASK-002 產出的 `database_url`）。
- 既有模式：延續 TASK-001／TASK-002 的專案結構，使用 SQLAlchemy 2.x 宣告式模型（`DeclarativeBase`）。
- 假設：
  - 兩張表放同一個 SQLite 檔案（`database_url` 指向的檔案），不分庫。
  - 語言特化欄位採「單表 + nullable 專屬欄位」設計（不拆成 `vocabulary_en` / `vocabulary_de` 兩張表），簡化 CRUD 與跨語言查詢；語言專屬欄位的合法性（例如 `language='en'` 時 `de_artikel` 必須為空）在 API 層（Pydantic schema）驗證，不在 DB 層用 CHECK constraint 強制，避免 SQLite CHECK 語法過度複雜。
  - SRS（間隔重複）相關欄位（到期日、難度係數等）**不在本卡範圍**，留給 Phase 3 用 Alembic migration 另外加欄位，避免本卡欄位設計被尚未定案的演算法綁死。
- 未知事項：無（欄位設計已在下方「需求」列出，待人工核准）。
- 允許變更的檔案：`backend/app/models/*.py`（新增）、`backend/alembic/`（新增，含 `alembic.ini`、`env.py`、`versions/`）、`backend/app/core/db.py`（新增，SQLAlchemy engine／session 工廠）。
- 不得觸碰：`ai/`、`tools/`、`scripts/`。

## 需求

### `media_log` 資料表

| 欄位 | 型別 | 限制 | 說明 |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | |
| `language` | String(2) | NOT NULL, index，只允許 `en`／`de` | 語言隔離的核心欄位 |
| `title` | String | NOT NULL | 劇集／影片名稱 |
| `media_type` | String | NOT NULL，預設 `drama` | 例如 drama／movie／anime／youtube／podcast／other |
| `watched_date` | Date | NOT NULL | 觀看日期 |
| `duration_minutes` | Integer | NOT NULL，須 >= 0 | 本次觀看時長（分鐘），用於累積時數統計 |
| `notes` | Text | nullable | |
| `created_at` | DateTime | server_default now | |
| `updated_at` | DateTime | onupdate now | |

### `vocabulary` 資料表

| 欄位 | 型別 | 限制 | 說明 |
|---|---|---|---|
| `id` | Integer | PK, autoincrement | |
| `language` | String(2) | NOT NULL, index，只允許 `en`／`de` | 語言隔離的核心欄位 |
| `headword` | String | NOT NULL, index | 單字本身 |
| `part_of_speech` | String | nullable | 詞性（英德共用欄位） |
| `translation_zh` | Text | nullable | 繁中翻譯 |
| `example_sentence` | Text | nullable | 例句（Phase 2 SRT 對齊器會回填） |
| `media_log_id` | Integer | FK -> `media_log.id`, nullable, ON DELETE SET NULL | 單字來源的劇集紀錄 |
| `ipa` | String | nullable | 英文 KK/IPA 音標，僅 `language='en'` 時使用 |
| `de_artikel` | String(3) | nullable，只允許 `der`／`die`／`das` | 德文名詞冠詞，僅 `language='de'` 時使用 |
| `de_plural` | String | nullable | 德文複數型，僅 `language='de'` 時使用 |
| `de_conjugation` | Text（JSON 字串） | nullable | 德文動詞變位，僅 `language='de'` 時使用，先存 JSON 字串（例如 `{"ich":"gehe","du":"gehst",...}`），Phase 2 決定實際字典 API 回傳格式後再細化 |
| `notes` | Text | nullable | |
| `created_at` | DateTime | server_default now | |
| `updated_at` | DateTime | onupdate now | |

### 其他實作要求

- `backend/app/core/db.py`：建立 SQLAlchemy `engine`（讀取 `settings.database_url`）與 `SessionLocal`、`get_db()` FastAPI 依賴（yield session，用完自動 close）。
- 用 Alembic 管理 schema：`alembic init alembic`、設定 `env.py` 讀取 `app.core.config.get_settings().database_url` 與 `app.models.Base.metadata`，產生初始 migration（建立 `media_log`、`vocabulary` 兩張表），並確認 `alembic upgrade head` 可從零建立出 SQLite 檔案與兩張表。
- `data/` 目錄（SQLite 檔案存放處）需存在或由程式啟動時自動建立；`data/*.db` 需被 `.gitignore` 排除（TASK-002 已處理 `.env`／`*.db`，這裡只需確認涵蓋 `data/` 目錄）。

## 驗收標準

- `alembic upgrade head` 可在乾淨環境下成功執行，產生 SQLite 檔案並建出 `media_log`、`vocabulary` 兩張表，欄位與上方表格一致。
- `alembic downgrade base` 可成功回滾（drop 掉兩張表），確認遷移可逆。
- 可用 SQLAlchemy session 分別對兩張表做基本 insert／query，並驗證：
  - 插入 `language='en'` 與 `language='de'` 的 `vocabulary` 資料互不干擾，可依 `language` 篩選出各自的資料集。
  - `vocabulary.media_log_id` 可正確關聯到 `media_log.id`，刪除對應 `media_log` 後，`vocabulary.media_log_id` 依 `ON DELETE SET NULL` 變成 `NULL` 而不是整筆單字被刪除。
- `pytest` 涵蓋上述行為的整合測試皆通過。

## 實作備註

- 語言合法值（`en`／`de`）與德文冠詞合法值（`der`／`die`／`das`）先用 Python `Enum` 定義在 `app/models/enums.py`，供 model 與後續 API schema 共用，避免字串到處手打。
- 這張卡只建模型與 migration，不建 CRUD API（那是 Epic「多語言資料庫與後端 API」的範圍）。
- 若人工核准時要求調整欄位（例如新增／改名），先更新這張卡的「需求」表格取得再次核准，再動手實作，不要邊做邊改欄位設計。

## 驗證契約

- 單元測試：`pytest backend/tests/test_models.py`（模型層級的欄位限制、預設值）。
- 整合測試：`pytest backend/tests/test_db_migration.py`（實際跑 `alembic upgrade head`／`downgrade base`，驗證表結構與外鍵行為）。
- E2E 測試：不適用。
- 型別檢查：不強制。
- Lint：`ruff check backend/`
- Build：`pip install -r backend/requirements.txt` 成功（需新增 `alembic` 套件）。
- 螢幕截圖：不適用。
- 安全性檢查：SQLite 檔案路徑不可寫死絕對路徑或使用者家目錄外洩隱私路徑；確認 `data/` 目錄已被 `.gitignore` 排除，避免個人單字庫內容意外進版控。

## 完成證據

- 變更的檔案：
  - `backend/app/models/base.py`、`enums.py`、`media_log.py`、`vocabulary.py`、`__init__.py`
  - `backend/app/core/db.py`（engine、`SessionLocal`、`get_db()`、SQLite `PRAGMA foreign_keys=ON`、`ensure_sqlite_dir_exists()`）
  - `backend/alembic.ini`、`backend/alembic/env.py`（改用 `app.core.config.get_settings().database_url`、`target_metadata = Base.metadata`）
  - `backend/alembic/versions/eff9d22d5269_create_media_log_and_vocabulary_tables.py`
  - `backend/tests/test_models.py`、`backend/tests/test_db_migration.py`
  - `backend/requirements.txt`（新增 `alembic`）
- 執行過的指令：
  - `alembic revision --autogenerate -m "create media_log and vocabulary tables"`
  - `alembic upgrade head` → 成功建出 `media_log`、`vocabulary` 兩張表
  - `alembic downgrade base` → 成功清空兩張表，再 `alembic upgrade head` 復原，確認遷移可逆
  - `pytest -q` → `11 passed`
  - `ruff check .` → `All checks passed!`
- 測試輸出：`11 passed, 1 warning in 0.98s`（同前兩卡的 httpx deprecation 警告，非本卡範圍）。涵蓋：語言隔離查詢、`duration_minutes` 負數拒絕、`de_artikel` enum 往返、FK `ON DELETE SET NULL` 實際行為（透過真實 SQLite 連線 + `PRAGMA foreign_keys=ON` 驗證）。
- 螢幕截圖：不適用。
- 已知限制：
  - 實作過程中發現並修正一個潛在 bug：SQLAlchemy 的 `Enum` 型別預設用 Python enum 的**名稱**（`EN`/`DE`）存進 DB，而不是**值**（`en`/`de`）；已加上 `values_callable=lambda e: [m.value for m in e]` 修正，並在 autogenerate 前重新生成一次遷移確認欄位值正確為小寫。
  - `alembic/versions/` 已排除在 `ruff` 檢查範圍外（自動產生的遷移腳本，行為由 Alembic 產生器決定，不手動維護格式）。
  - `alembic.ini` 內只能放 ASCII 註解——本機 Windows 環境的 configparser 用系統 locale（cp950）讀檔，塞中文註解會直接讓 `alembic` 指令噴 `UnicodeDecodeError`，已改回英文註解。
- 後續任務：Epic「多語言資料庫與後端 API」的 TASK-004（API 服務骨架）。
