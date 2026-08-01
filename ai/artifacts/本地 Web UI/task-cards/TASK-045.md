# AI-Ready 任務卡

## Metadata

- 任務：TASK-045 追劇時間趨勢卡片（新增，重用 Chart Tooltip）
- 上層規格：`ai/artifacts/專案設置/screen-spec-dashboard.md`「追加需求（2026-07-30）」區塊、`ai/artifacts/專案設置/mockup-decision-dashboard-charts.md`（選定變體 A）
- 上層 Epic：本地 Web UI
- 上層 User Story：Dashboard 圖表擴充
- 分軌：前端
- 前置任務（dependsOn）：TASK-044
- 狀態：草稿
- 風險等級：低
- Agent owner：claude
- 人工核准者：（待實作後 Niko 本機驗證）

## 目標

在 Dashboard 新增一張獨立的「追劇時間趨勢」卡片，用既有 `mediaLogs` 資料依 `watched_date` 彙總過去 14 天的 `duration_minutes`，版面與互動比照「單字成長」卡片（含 TASK-044 的 hover/tap tooltip）。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/Dashboard.tsx`（`VocabGrowthChart`、`buildLinePoints`、TASK-044 新增的 Tooltip 元件/邏輯、頁面主體 JSX 版面）、`frontend/src/lib/dashboard-api.ts`（`MediaLogRead`、`fetchMediaLogs`，皆已存在不需新增）。
- 既有模式：
  - Dashboard 已經在 `mediaLogs = useApi(() => fetchMediaLogs(language), [language])` 抓過完整清單（`frontend/src/pages/Dashboard.tsx:286`），並在同一個 `mediaLogs` 結果上做過前端聚合（`weekWatchMinutes`，`Dashboard.tsx:296-301`）；本卡的「依日彙總」是同一種「已有完整資料、前端算聚合」模式的延伸，**不需要新的後端端點**（比照 TASK-029 決議：資料量小，前端算即可）。
  - 圖表骨架、空狀態文案風格、`<details>` 資料表格直接照抄 `VocabGrowthChart` 的結構（`Dashboard.tsx:164-230`），只是把「新增單字數」換成「觀看分鐘數」。
- 假設：
  - 沿用 mockup 變體 A 的版面：新卡片獨立一整排、全寬，放在「單字成長」卡片下方、「複習日曆／最近追劇」2 欄 grid 上方（見 `dashboard-variant-charts-a.html`）。
  - 不做指標切換（screen-spec 明確排除，這張卡片只有一種指標：每日觀看分鐘數）。
  - `duration_minutes` 加總後以整數分鐘顯示，不做時分轉換（不同於側欄 KPI「本週觀看時數」的 `Xh Ym` 格式，因為這裡是逐日數值，維持跟 Y 軸刻度一致的單位）。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/pages/Dashboard.tsx`。
- 不得觸碰：`backend/`（無新端點）。

## 需求

- 新增卡片「追劇時間趨勢」，標題下方說明「過去 14 天每日觀看分鐘數」。
- 資料來源：既有 `mediaLogs.data`，依 `watched_date`（`YYYY-MM-DD`）分桶加總 `duration_minutes`，桶範圍為過去 14 天（比照 `VocabGrowthChart` 用 `VOCAB_GROWTH_DAYS` 常數的做法，新增對應常數，例如 `WATCH_TREND_DAYS = 14`）。
- 折線圖套用 TASK-044 的 Chart Tooltip（hover/tap 皆需支援），末端標「今天 N 分鐘」。
- 附「顯示資料表格」`<details>` 無障礙後備，欄位為「日期」／「觀看分鐘數」。
- 三態處理：
  - 載入中：`SkeletonBlock`（比照其他卡片）。
  - 錯誤：`ErrorNote`＋重試按鈕，只影響這張卡片，不拖累其他區塊（`mediaLogs` 這個 `useApi` 結果已經是獨立狀態，天然滿足這點）。
  - 空狀態（14 天內加總為 0）：折線圖仍渲染（全為 0 的平線）＋文字「過去 14 天沒有追劇紀錄。」（比照 `VocabGrowthChart` 「過去 14 天沒有新增單字。」的既有文案模式）。

## 驗收標準

- Dashboard 頁面新增「追劇時間趨勢」卡片，位置在「單字成長」卡片正下方、「複習日曆／最近追劇」2 欄 grid 正上方。
- 有追劇紀錄時，折線正確反映每日分鐘數加總，末端數字與當天實際加總一致。
- 資料庫該語言下 14 天內沒有任何追劇紀錄時，顯示「過去 14 天沒有追劇紀錄。」且圖表不報錯。
- hover/tap 資料點會出現 tooltip（日期＋分鐘數），行為與「單字成長」卡片一致（重用同一元件，非另刻一份）。
- 卡片的 padding／字級／圖表高度與「單字成長」卡片一致（視覺密度比對，滿足 screen-spec 視覺驗收標準）。
- `npm run build`／`npm run lint` 皆通過。

## 實作備註

- 新增一個 `WatchTimeTrendChart({ mediaLogs }: { mediaLogs: MediaLogRead[] })` 函式，緊接在 `VocabGrowthChart` 之後定義，結構對齊（buckets 用 `toLocalIsoDate` 產生過去 14 天的 key，逐筆 `mediaLogs` 依 `watched_date` 落桶加總 `duration_minutes`）。
- 折線的 Y 軸刻度上限用 `Math.max(1, ...values)`（沿用 `buildLinePoints` 既有邏輯，不需修改該共用函式），不必額外處理離群值。
- 卡片插入位置：在 `Dashboard()` 主體 JSX 裡，「單字成長」`<Card>` 區塊之後、`複習日曆／最近追劇` 的 `grid gap-4 md:grid-cols-2` 區塊之前，新增一個結構相同的 `<Card>`（`CardHeader` + 依 `mediaLogs.status` 分三態渲染）。
- 沿用 `mediaLogs` 既有的 `useApi` 結果，不重新呼叫 `fetchMediaLogs`（避免重複請求）。

## 驗證契約

- 單元測試：不適用（前端無測試框架）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：`npm run build`。
- Lint：`npm run lint`。
- Build：`npm run dev` 本機手動確認三態（新增/清空追劇紀錄測試空狀態與有資料狀態）。
- 螢幕截圖：有資料狀態一張、空狀態一張、hover 中狀態一張。
- 安全性檢查：不適用（純前端讀取既有資料，無新輸入處理、無新網路呼叫）。

## 完成證據

- 變更的檔案：待實作後填寫。
- 執行過的指令：待實作後填寫。
- 測試輸出：待實作後填寫。
- 螢幕截圖：待實作後填寫。
- 已知限制：待實作後填寫。
- 後續任務：無（本卡完成後「Dashboard 圖表擴充」User Story 全部完成）。
