# AI-Ready 任務卡

## Metadata

- 任務：TASK-036 追劇紀錄管理頁面
- 上層規格：（無獨立 feature-spec／screen-spec；版型直接沿用已核准的單字庫頁面模式，見下方情境包）
- 上層 Epic：本地 Web UI
- 上層 User Story：（新，「追劇紀錄管理頁面」，與「單字庫管理頁面」平行）
- 分軌：前端（後端 API 已存在，見情境包）
- 前置任務（dependsOn）：TASK-035
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-25（本機測試導覽、新增、編輯、刪除四個動作皆成功，`npm run build`／`npm run lint` 皆通過）

## 目標

新增追劇紀錄管理頁面：列表、新增、編輯、刪除，直接做完整 CRUD（不像單字庫當初分階段做），因為版型已經被驗證過（Dialog 彈窗新增/編輯＋確認對話框刪除），沒有新的版型抉擇需要走 mockup-gate。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/MediaLog.tsx`（新增）、`frontend/src/components/app-rail.tsx`（「追劇紀錄」從 toast 佔位改為真正導覽）、`frontend/src/lib/router.tsx`（新增 `/media-logs` 路徑）、`frontend/src/App.tsx`、`frontend/src/lib/dashboard-api.ts`（新增 `createMediaLog`／`updateMediaLog`／`deleteMediaLog`／對應型別）。
- 既有模式：後端 `GET/POST/PATCH/DELETE /media-logs` 皆是 Epic 1 已完成、已測試的既有端點，本卡純前端串接，不動後端；**版面直接沿用 `Vocabulary.tsx` 已核准的模式**（TASK-030 選定變體 A：Dialog 彈窗新增／編輯，TASK-035 的刪除確認對話框），因為這是同一個 App 內第二個「列表＋CRUD」畫面，版型問題已經在單字庫那次解決過，不需要重新走一次 mockup-gate 的多變體比較流程。
- 假設：直接做完整 CRUD（新增/列表/編輯/刪除），不像單字庫當初分批（TASK-030 只做新增+列表，TASK-033/035 才補編輯/刪除）——因為這次已經知道使用者會要編輯刪除，且版型已驗證過，一次做完比分批更有效率。字幕上傳（`POST /media-logs/{id}/subtitles`）與 CSV 匯入匯出不在本卡範圍。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/`。
- 不得觸碰：`backend/`。

## 需求

- 表格列出目前語言的追劇紀錄（劇名／類型／觀看日期／時長）。
- 「新增追劇紀錄」按鈕開啟 Dialog 表單：劇名（必填）、類型（下拉：影集/電影/紀錄片/其他）、觀看日期（date input，預設今天）、觀看時長分鐘數（必填，不可為負）、備註（選填）。
- 每列「編輯」「刪除」圖示，編輯開啟同一個 Dialog 並預填資料；刪除彈確認對話框。
- 涵蓋 loading／error／empty／送出中四態。
- `AppRail` 的「追劇紀錄」圖示改為真正導覽到 `/media-logs`（原本只會跳 toast）。

## 驗收標準

- 點側邊欄「追劇紀錄」圖示，網址切到 `/media-logs`，看到列表畫面。
- 新增一筆追劇紀錄成功後，表格立即顯示新資料。
- 編輯一筆紀錄，Dialog 開啟時欄位已預填目前資料。
- 刪除前有確認對話框，確認後該筆從列表消失。
- 觀看時長留空或輸入負數時，顯示對應的欄位錯誤訊息，不會送出。

## 實作備註

- `MediaLog.tsx` 的結構（`XxxDialog` 新增/編輯共用＋`DeleteConfirmDialog`＋主頁面表格）直接複製 `Vocabulary.tsx` 的既有模式，只是欄位換成劇名/類型/觀看日期/時長/備註，維持整個 App 內「列表＋CRUD」畫面的一致互動語言。
- `watched_date` 用原生 `<input type="date">`（`Input` 元件本來就是薄封裝、直接透傳 `type` 屬性），不需要額外的日期選擇器元件。
- `media_type` 用固定 4 個選項的 Select（影集/電影/紀錄片/其他），對應後端自由字串欄位（無列舉限制），選填值直接存成字串。
- `AppRail` 移除了不再需要的 `toast` import（原本「追劇紀錄」按鈕用 toast 佔位，現在是真正的 `NAV_ITEMS` 項目）。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架）。
- 整合測試：不適用（呼叫的既有後端端點已有 Epic 1 的 pytest 覆蓋）。
- E2E 測試：不適用。
- 型別檢查：Niko 本機執行 `npm run build`，第一次執行有錯（TS2322，見「已知限制」與完成證據），修正後通過。
- Lint：Niko 本機執行 `npm run lint` 確認通過，無錯誤。
- Build：Niko 本機執行 `npm run build` 確認通過（修正後）。
- 螢幕截圖：未產出圖檔，Niko 目視確認導覽、新增、編輯、刪除四個動作皆正常。
- 安全性檢查：不適用（呼叫既有後端 API，刪除有二次確認）。

## 完成證據

- 變更的檔案：
  - `frontend/src/lib/router.tsx`（新增 `/media-logs` 路徑）
  - `frontend/src/components/app-rail.tsx`（「追劇紀錄」改為真正導覽）
  - `frontend/src/pages/MediaLog.tsx`（新增，完整 CRUD 頁面）
  - `frontend/src/App.tsx`（依路徑渲染 `MediaLog`）
  - `frontend/src/lib/dashboard-api.ts`（新增 `createMediaLog`／`updateMediaLog`／`deleteMediaLog`／`MediaLogCreate`／`MediaLogUpdate`）
- 執行過的指令：Agent 端無（此環境無 Node.js）；Niko 本機執行 `npm run build`（第一次失敗、修正後通過）、`npm run lint`（通過）；本機手動測試導覽/新增/編輯/刪除。
- 測試輸出：無自動化測試，以本機建置/lint 通過 + 人工手動操作驗證為準。
- 螢幕截圖：不適用，待人工本機執行後補上。
- 已知限制：
  1. **驗證階段發現並修正**：`npm run build` 第一次執行報 4 處 TS2322 型別錯誤（`Vocabulary.tsx` 三處、`MediaLog.tsx` 一處）——base-ui 的 `Select` `onValueChange` 回呼型別是 `(value: string | null, ...) => void`（清除選取時會傳 `null`），但程式碼直接把 `useState` 的 setter（只接受 `string`）當回呼傳入，型別對不上。改用 inline arrow function（`(value) => setXxx(value ?? "")`）把 `null` 轉成空字串／預設值。這證實了此執行環境缺乏 Node.js 的風險是真實的：純審查沒抓到這個錯誤，靠 Niko 本機建置才抓到。
  2. 不含字幕上傳（`.srt`）、CSV 匯入匯出，這些後端 API 都已存在，屬於後續 User Story 範圍。
- 後續任務：無。
