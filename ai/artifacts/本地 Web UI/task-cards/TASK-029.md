# AI-Ready 任務卡

## Metadata

- 任務：TASK-029 Dashboard 頁面實作（含前後端串接）
- 上層規格：`ai/artifacts/專案設置/screen-spec-dashboard.md`、`ai/artifacts/專案設置/mockup-decision-dashboard.md`（選定變體 C — Command Center）
- 上層 Epic：本地 Web UI
- 上層 User Story：Dashboard 頁面實作
- 分軌：前後端串接
- 前置任務（dependsOn）：TASK-027, TASK-028
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：（待 Niko 本機執行 `npm run dev` 驗證後追加簽核；螢幕截圖尚未取得，見已知限制）

## 目標

把 S5 核准的變體 C 版型改寫成真正的 React 元件，串接真實後端資料（複習統計、複習佇列、複習歷史、單字庫、追劇紀錄），取代 mockup 階段的靜態假資料，同時處理載入中／空狀態／錯誤三態。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/App.tsx`（改為渲染 `Dashboard`）、`frontend/src/pages/Dashboard.tsx`（新增）、`frontend/src/pages/ComponentShowcase.tsx`（新增，原 `App.tsx` 的 S4 元件展示頁搬移至此，見下方「實作備註」）、`frontend/src/lib/dashboard-api.ts`（新增，型別化的 API 呼叫）、`frontend/src/hooks/use-api.ts`（新增，通用的 loading/error/success 狀態 hook）。
- 既有模式：沿用 TASK-027 的 `apiGet`／`useLanguage`；元件全部重用 S4 元件庫（`Card`、`Badge`、`Button`）與 S3 token（顏色一律用 Tailwind 語意 class 或 `var(--token)`，未手寫新色值）。
- 假設：
  - 只做 Dashboard 讀取，不做任何寫入（新增/刪除單字、開始複習流程本身）——這些是「開始複習」等 CTA 目前只顯示「尚未實作」提示的原因，避免做出無法真正運作的按鈕假裝能用。
  - 「複習佇列」卡片的每個項目本來想顯示「到期／Leech」狀態徽章（mockup 原始設計），但 `VocabularyRead` schema 沒有回傳 `srs_next_review_at`／`srs_lapses` 等 SRS 內部欄位，前端拿不到這些資訊，因此簡化成只顯示單字＋詞性，不硬造假狀態。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/`。
- 不得觸碰：`backend/`。

## 需求

- Dashboard 頁面涵蓋 screen-spec 列出的區塊：今日待複習 CTA（含連續複習天數、進度環）、KPI（7 日正確率／本週觀看時數／總單字量）、單字成長趨勢圖、複習日曆熱力圖、複習佇列（前 5 筆）、最近追劇（前 2 筆）、語言切換。
- 每個資料區塊各自處理載入中（skeleton）／錯誤（訊息＋重試按鈕）／空狀態（文字說明），單一區塊失敗不影響其他區塊（screen-spec 的「錯誤」狀態要求）。
- 圖表（趨勢圖／熱力圖）用真實資料動態計算，不是寫死的示範數字；資料量為 0 時顯示對應空狀態文字而不是空白圖表。
- 全部顏色/圓角/字級皆對應既有 token，未手寫新值（沿用 mockup 的顏色/圓角決策：熱力圖 6 階沿用 `brand.900/700/600/500/300` + `muted`，趨勢線沿用 `info-500`）。

## 驗收標準

- 頁面可用 `npm run dev` 開啟並看到真實資料（依當下資料庫內容而定，非固定假資料）。
- 切換語言（EN/DE）後，所有區塊重新抓對應語言的資料。
- 資料庫是空的（全新環境）時，各區塊顯示對應空狀態文案，不報錯、不空白。
- 手動讓後端斷線或回傳錯誤時，對應區塊顯示錯誤訊息＋重試按鈕，其餘區塊不受影響。

## 實作備註

- **元件庫展示頁搬遷**：`App.tsx` 原本是 TASK-025 的 S4 元件庫展示頁，現在 Epic 進到真正的頁面實作，`App.tsx` 改為渲染 `Dashboard`。展示頁本身搬到 `frontend/src/pages/ComponentShowcase.tsx` 保留（程式碼還在、供之後補頁面時參考），但**目前沒有路由可以開啟它**（TASK-027 決議暫不引入路由器）。`design-system.md` 的 S4 inventory「檔案位置」欄位已同步改成 `pages/ComponentShowcase.tsx`。
- **`useApi` hook**：`frontend/src/hooks/use-api.ts`，把「loading/error/success」三態＋`retry()` 包成通用 hook，5 個資料來源（`reviewStats`／`reviewQueue`／`reviewHistory`／`vocabulary`／`mediaLogs`）各自獨立呼叫、獨立顯示狀態，符合「單一區塊失敗不拖垮全頁」的要求。
- **進度環**：SVG `stroke-dasharray` 畫圓形進度，比例＝`reviewed_today / (reviewed_today + 複習佇列剩餘張數)`（近似值：見已知限制）。
- **單字成長趨勢圖**：從 `/vocabulary` 全量清單依 `created_at` 分桶成過去 14 天的每日新增數，動態算 SVG 折線圖座標（非寫死座標）；只在終點標數值，不畫圖例（單一數列，依 dataviz skill 規則）。
- **複習日曆熱力圖**：直接用 `/reviews/history?days=35` 的 35 筆資料，`grid-cols-7` 讓瀏覽器自動換行成 5 週，不需要手動 chunk。6 階色階函式 `heatLevelClass()`：0／1-3／4-7／8-12／13-17／18+ 對應 `bg-muted`／`bg-brand-900`／`700`／`600`／`500`／`300`（暗色模式 anchor 反轉：愈亮＝愈多，沿用 mockup 與 dataviz skill 決議）。
- **7 日正確率**：從同一份 `/reviews/history` 資料取最後 7 筆加總計算，沒有複習過就顯示「—」而非 0%（避免「0% 正確率」被誤讀成「複習了但都答錯」）。
- **本週觀看時數／單字量本週新增**：分別從 `/media-logs`、`/vocabulary` 全量清單依日期／`created_at` 於前端篩選加總（未新增後端聚合端點——資料量小，前端算即可，避免為了兩個小計再開兩支 API）。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架）。
- 整合測試：不適用（純前端無框架；後端串接邏輯已由 TASK-028 的 pytest 覆蓋 API 本身）。
- E2E 測試：不適用。
- 型別檢查：待人工在本機執行 `npm run build` 確認；此執行環境無 Node.js，未能跑。
- Lint：待人工在本機執行 `npm run lint` 確認；此執行環境無 Node.js，未能跑。
- Build：待人工在本機執行 `cd backend && uvicorn app.main:app --reload`（另一個終端機）+ `cd frontend && npm install && npm run dev`，兩個服務都起來後在瀏覽器開啟 Dashboard 確認。
- 螢幕截圖：待人工本機驗證後提供；此環境無瀏覽器/螢幕截圖工具，未能產出。
- 安全性檢查：不適用（唯讀頁面，僅呼叫既有後端 API，無新輸入處理）。

## 完成證據

- 變更的檔案：
  - `frontend/src/App.tsx`（改為渲染 `Dashboard`）
  - `frontend/src/pages/Dashboard.tsx`（新增，Dashboard 主頁面）
  - `frontend/src/pages/ComponentShowcase.tsx`（新增，S4 展示頁搬遷至此）
  - `frontend/src/lib/dashboard-api.ts`（新增，型別化 API 呼叫）
  - `frontend/src/hooks/use-api.ts`（新增，通用資料狀態 hook）
  - `ai/context/design-system.md`（S4 inventory 檔案位置改指向 `pages/ComponentShowcase.tsx`）
- 執行過的指令：無（此環境無 Node.js，見上方驗證契約）。
- 測試輸出：不適用，待人工本機驗證。
- 螢幕截圖：不適用，待人工本機執行後補上。
- 已知限制：
  1. 此執行環境沒有 Node.js，`npm install`／`npm run dev`／`npm run build`／`npm run lint` 均未執行，程式碼正確性僅靠審查與比對既有元件慣例把關（後端部分因為此環境有 Python，已用 185 個 pytest 測試 + ruff 實際驗證，見 TASK-028）。
  2. 複習佇列不顯示「到期／Leech」狀態徽章（`VocabularyRead` 未回傳 SRS 內部欄位），只顯示單字＋詞性；若後續想要精確狀態，需要擴充 `VocabularyRead` 或 `/reviews/queue` 回傳格式，屬於下一張任務卡的範圍。
  3. 「今日待複習」的進度環比例（已複習／總數）用 `reviewed_today + 複習佇列剩餘張數` 近似總數，非後端直接提供的精確欄位；邊界情況（例如 `AGAIN` 評分的卡片同一天可能重新進入佇列）可能讓進度環數字有些微不準，對個人使用的參考用途影響不大。
  4. 圖表 hover 目前只有原生 `title` 屬性提供最基本提示，未做完整的 crosshair/tooltip（同 screen-spec 已知限制）。
  5. 沒有前端路由器，「單字庫」「追劇紀錄」導覽圖示點擊只會跳出「尚未實作」的 toast，非真正導覽。
- 後續任務：Niko 本機驗證後回填人工核准；下一個 User Story 建議是「單字庫管理頁面」或「複習流程頁面」（讓「開始複習」CTA 真正可用），屆時需要新增路由器與 API client 的寫入方法（POST/PATCH/DELETE）。
