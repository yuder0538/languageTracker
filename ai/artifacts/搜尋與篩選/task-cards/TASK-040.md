# AI-Ready 任務卡

## Metadata

- 任務：TASK-040 單字庫與追劇紀錄搜尋列
- 上層規格：`ai/artifacts/搜尋與篩選/screen-spec-search-filter-toolbar.md`
- 上層 Epic：搜尋與篩選
- 上層 User Story：單字庫與追劇紀錄搜尋列
- 分軌：前後端串接
- 前置任務（dependsOn）：無
- 狀態：就緒
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-26（mockup 變體 A 已選定，見 mockup-decision）

## 目標

單字庫列表頁（`/vocabulary`）與追劇紀錄列表頁（`/media-logs`）標題列各加一個搜尋框：單字庫依單字（headword）搜尋，追劇紀錄依劇名（title）搜尋，即時（debounce）套用，不做進階篩選下拉。

## 情境包（Context Pack）

- 相關檔案：
  - `backend/app/api/media_log.py`（`list_media_logs`，新增 `title: str | None` 查詢參數，比照 `vocabulary.py` 的 `headword` ilike 模式）
  - `backend/tests/test_media_log_api.py`（新增 title 篩選測試，比照既有 `test_list_filters_by_language`）
  - `frontend/src/lib/dashboard-api.ts`（`fetchVocabulary`／`fetchMediaLogs` 簽章加可選 `search` 參數）
  - `frontend/src/pages/Vocabulary.tsx`（標題列加搜尋框，`useApi` deps 帶入 debounced 搜尋字串）
  - `frontend/src/pages/MediaLog.tsx`（同上，依劇名搜尋）
- 既有模式：
  - 後端 `GET /vocabulary` 已有 `headword: str | None`＋`ilike(f"%{headword}%")` 的部分比對搜尋，`list_media_logs` 直接照抄同一種寫法加 `title`。
  - 前端 `useApi(fetcher, deps)`（`frontend/src/hooks/use-api.ts`）依 `deps` 變化重打 API；把 debounced 搜尋字串放進 `deps` 陣列即可，不需改 hook 本身。
  - `apiGet` 已自動濾掉 `undefined` 參數，空字串搜尋框可直接傳 `undefined`（不送 query）或空字串（後端 ilike `%%` 等同不篩選皆可，未特別要求）。
- 假設：
  - 搜尋為 debounce 300ms 即時篩選，不需按鈕；語言切換時搜尋框重置為空。
  - 不做詞性／來源劇集／類型／日期區間等進階篩選下拉（見 mockup-decision 選定的變體 A 範圍）。
  - 不動任何既有 CRUD／enrich／刪除邏輯。
- 未知事項：無。
- 允許變更的檔案：`backend/app/api/media_log.py`、`backend/tests/test_media_log_api.py`、`frontend/src/lib/dashboard-api.ts`、`frontend/src/pages/Vocabulary.tsx`、`frontend/src/pages/MediaLog.tsx`。
- 不得觸碰：`backend/app/api/vocabulary.py`（既有 `headword` 篩選已存在，前端直接使用即可，不需改後端）、其他既有頁面／元件。

## 需求

- 單字庫頁標題列右側、「新增單字」按鈕左邊，加一個帶搜尋圖示的輸入框，placeholder「搜尋單字…」，輸入後 debounce 300ms 呼叫 `fetchVocabulary(language, { headword: value || undefined })`。
- 追劇紀錄頁比照，placeholder「搜尋劇名…」，呼叫 `fetchMediaLogs(language, { title: value || undefined })`；後端 `GET /media-logs` 新增 `title` 查詢參數（`ilike` 部分比對，比照 `headword` 寫法）。
- 語言切換（EN/DE）時搜尋框清空、回復未篩選列表。
- 搜尋無結果時，表格區域顯示「找不到符合「{關鍵字}」的單字／紀錄」文字＋「清除搜尋」按鈕，與既有「還沒有任何資料」空狀態文案區分。
- 不影響既有新增／編輯／刪除／自動查詢／朗讀等既有功能。

## 驗收標準

- 單字庫頁輸入單字關鍵字，列表在停止輸入後約 300ms 內只顯示符合的單字（部分比對，不分大小寫）。
- 追劇紀錄頁輸入劇名關鍵字，行為比照上述。
- 清空搜尋框，列表回復顯示全部資料。
- 切換語言（EN⇄DE）後搜尋框清空，列表顯示新語言的未篩選資料。
- 搜尋到無符合結果時顯示「找不到符合」空狀態文案，而不是誤植既有「還沒有任何資料」文案。
- `cd backend && pytest -q` 全數通過（含新增的 title 篩選測試）。
- `cd frontend && npm run build`／`npm run lint` 皆通過。
- Niko 本機以瀏覽器實際操作兩個頁面的搜尋，確認符合上述驗收標準後核准轉 done。

## 實作備註

- 後端：`list_media_logs` 加 `title: str | None = None` 參數，`if title is not None: query = query.filter(MediaLog.title.ilike(f"%{title}%"))`，插入順序與既有 `media_type`／日期區間篩選並列即可。
- 前端：`dashboard-api.ts` 的 `fetchVocabulary`／`fetchMediaLogs` 改為接受第二個可選參數物件（例如 `{ headword？: string }`／`{ title?: string }`），往下傳給 `apiGet` 的 `params`。
- 兩頁各自維護 `searchInput`（即時輸入）與 `debouncedSearch`（用 `useEffect` + `setTimeout` 300ms 更新）兩個 state，`useApi` 的 `deps` 用 `[language, debouncedSearch]`。
- 語言切換時搜尋框重置：可在 `useEffect` 監聽 `language` 變化時把 `searchInput`／`debouncedSearch` 一併清空。

## 驗證契約

- 單元測試：無新增（沿用既有 pytest 套件結構，新增測項見整合測試）。
- 整合測試：`backend/tests/test_media_log_api.py` 新增 title 篩選測試（比照 `test_list_filters_by_language` 的寫法）。
- E2E 測試：無（本專案無 E2E 套件，以 Niko 本機手動驗證取代）。
- 型別檢查：`npm run build`（TypeScript 隨 Vite build 檢查）。
- Lint：`npm run lint`（frontend）、`ruff check .`（backend）。
- Build：`npm run build`。
- 螢幕截圖：Niko 本機操作截圖或口頭確認皆可（沿用本專案既有驗證慣例）。
- 安全性檢查：不適用（低風險、無新增輸入寫入資料庫，僅查詢參數）。

## 完成證據

- 變更的檔案：
  - `backend/app/api/media_log.py`（`list_media_logs` 新增 `title` ilike 篩選參數）
  - `backend/tests/test_media_log_api.py`（新增 2 個 title 篩選測試）
  - `frontend/src/lib/dashboard-api.ts`（`fetchVocabulary`／`fetchMediaLogs` 加可選搜尋參數）
  - `frontend/src/pages/Vocabulary.tsx`（標題列搜尋框、debounce、語言切換重置、搜尋無結果空狀態）
  - `frontend/src/pages/MediaLog.tsx`（同上，依劇名搜尋）
- 執行過的指令：
  - `pytest -q`（backend，192 passed）
  - `ruff check .`（backend，全數通過）
  - `npm run build`（frontend，成功）
  - `npm run lint`（frontend，僅既有 pre-existing 的 fast-refresh 警告，無新增錯誤）
  - 本機以 `uvicorn` + `vite dev` 啟動，用 `claude-in-chrome` 實際操作瀏覽器驗證：單字庫頁搜尋「xyz」出現「找不到符合」空狀態＋清除搜尋按鈕正常運作、清除後列表復原；切換 EN／DE 時搜尋框清空且正確顯示「還沒有任何單字」（非搜尋空狀態）；追劇紀錄頁搜尋「dar」正確篩出「Dark」。驗證用的暫時測試資料（追劇紀錄 id 2/3）已透過 API 刪除清除，未留在資料庫。
- 測試輸出：pytest 192 passed；ruff 全數通過；`npm run build` 成功產出 dist。
- 螢幕截圖：透過 claude-in-chrome 截圖確認（單字庫搜尋列、無結果空狀態、追劇紀錄搜尋列），未另存檔案。
- 已知限制：無進階篩選（詞性／來源劇集／類型／日期區間），依 mockup-decision 選定範圍刻意不做。
- 後續任務：進階篩選（單字庫：詞性／來源劇集；追劇紀錄：類型／觀看日期區間）留給後續 User Story，需要時再開新任務卡。
