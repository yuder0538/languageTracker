# AI-Ready 任務卡

## Metadata

- 任務：TASK-044 Chart Tooltip 共用元件＋套用到「單字成長」卡片（含指標切換）
- 上層規格：`ai/artifacts/專案設置/screen-spec-dashboard.md`「追加需求（2026-07-30）」區塊、`ai/artifacts/專案設置/mockup-decision-dashboard-charts.md`（選定變體 A）
- 上層 Epic：本地 Web UI
- 上層 User Story：Dashboard 圖表擴充
- 分軌：前端
- 前置任務（dependsOn）：TASK-029
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko（2026-08-02 於本機真實瀏覽器＋手機確認 hover 對準、指標切換、觸控 tap 開合皆正確）

## 目標

在既有「單字成長」折線圖上，做出可重用的圖表 hover/tap tooltip（guideline＋浮動框），並新增指標切換下拉（每日新增／累積總量），讓這張卡片同時具備兩項追加需求的行為。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/Dashboard.tsx`（`VocabGrowthChart` 函式、`buildLinePoints` 輔助函式）、`frontend/src/components/ui/select.tsx`（既有 `Select` 元件）、`ai/context/design-system.md`（S4 inventory 已登記「Chart Tooltip」待實作列）。
- 既有模式：
  - `VocabGrowthChart`（`frontend/src/pages/Dashboard.tsx:164-230`）已用 `buildLinePoints()` 把 14 天資料算成 SVG `viewBox="0 0 700 170"` 座標，折線用 `polyline`，末端用 `circle`＋`text` 標「今天 +N」。本卡延伸同一份資料/座標計算，不重寫圖表骨架。
  - `Select`／`SelectTrigger`／`SelectValue`／`SelectContent`／`SelectItem` 已是完成狀態的 S4 元件（`frontend/src/components/ui/select.tsx`），沿用單字庫等既有頁面的用法，不新增元件。
  - 現有圖表 SVG 用 `width="100%"` 響應式渲染但 `viewBox` 固定 700x170，因此滑鼠/觸控座標需先用 `getBoundingClientRect()` 換算成 SVG 座標系（乘上 `700 / rect.width` 縮放係數），才能找到最近的資料點索引。
- 假設：
  - 指標下拉的預設值為「每日新增」（沿用 TASK-029 既有行為，避免使用者一打開就看到不熟悉的累積數字）；Niko 未在 mockup 決策裡指定初始值，若驗收時想要預設「累積總量」，屬於低成本的後續小改動。
  - 「累積總量」是 14 天視窗內的逐日累加（`values` 陣列的 running sum），不是全站歷史總單字量（KPI 側欄的「總單字量 342」）——兩者是不同數字，需在文案上避免混淆（沿用 mockup 的「今天累積 N 字」用語，不寫「總計」）。
  - Tooltip 只需支援單一資料點聚焦（一次顯示一個），不需要多點比較。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/pages/Dashboard.tsx`。
- 不得觸碰：`backend/`、`frontend/src/components/ui/`（重用既有 `Select`，不修改其原始碼）。

## 需求

- 「單字成長」卡片的 `CardHeader` 新增 `Select` 下拉，選項為「每日新增」／「累積總量」；切換時卡片本身位置/大小不變，只換內部折線資料與標題說明文字（例如「過去 14 天新增單字數」↔「過去 14 天累積單字量」）。
- 折線圖任一資料點：滑鼠 hover 移入附近時，顯示 guideline 垂直虛線＋浮動框（日期＋當日數值），移出後消失；觸控裝置以 tap 觸發同一顆 tooltip，再次 tap 別處或 tap 同一點取消。
- `<details>`「顯示資料表格」需同步反映目前選取的指標（欄位標題與數值皆隨切換更新）。
- 末端標籤文字隨指標切換：「今天 +N」（每日新增）／「今天累積 N 字」（累積總量）。

## 驗收標準

- 下拉切換「每日新增」/「累積總量」時，折線形狀、Y 軸最大值刻度、末端標籤、資料表格數值都正確切換，卡片高度與版面不跳動。
- 滑鼠移到折線任一點附近（例如 ±10px 容許誤差內以最近點為準）出現 tooltip，內容為該點日期＋數值；移出圖表區域後 tooltip 消失。
- 觸控裝置（或用瀏覽器 devtools 的觸控模擬）tap 資料點出現 tooltip，tap 圖表外任意處或再 tap 同一點會關閉。
- Tooltip 使用 `shadow.sm` token 做浮起感（依 `design-system.md` S4 inventory 登記的例外規則），文字對比達 WCAG AA。
- `npm run build`／`npm run lint` 皆通過。

## 實作備註

- Tooltip 用一個小型內部元件（例如 `ChartTooltip`）+ 一段共用的「找最近資料點」邏輯（例如 `useNearestPoint` 或純函式），定義在 `Dashboard.tsx` 內（沿用現有「所有 Dashboard 圖表函式都在同一檔案」的慣例，不新開檔案/資料夾），讓 TASK-045 的「追劇時間趨勢」卡片可以直接重用同一個函式與元件。
- Hover 用 `onMouseMove`／`onMouseLeave` 綁在 `<svg>` 上；觸控用 `onTouchStart`（配合 `e.preventDefault()` 避免觸發瀏覽器預設的捲動/縮放手勢干擾）。
- 座標換算：`onMouseMove`/`onTouchStart` 拿到的是螢幕像素座標，需用 `svgRef.current.getBoundingClientRect()` 算出相對於 SVG 元素左上角的位置，再乘上 `700 / rect.width` 換成 `viewBox` 座標，才能對照 `buildLinePoints()` 算出的 `points[].x`。
- 累積總量計算：`values.reduce((acc, v, i) => { acc.push((acc[i-1] ?? 0) + v); return acc }, [])`，複用同一組 `buckets`/`days`，只是要傳給 `buildLinePoints` 的陣列不同。
- Tooltip 定位：guideline 是一條 `x1=x2=<資料點 x>` 的垂直 `<line>`；浮動框用 `<foreignObject>` 或 SVG 外層的絕對定位 `<div>`（`position: absolute`, 用 JS 算好的 px 座標）皆可，選一種能讓文字用一般 HTML/CSS 排版（而非手刻 SVG `<text>` 多行）的做法，方便之後调整文案。

## 驗證契約

- 單元測試：不適用（前端無測試框架，沿用 TASK-029 既有慣例）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：`npm run build`。
- Lint：`npm run lint`。
- Build：`npm run dev` 本機手動操作下拉切換與 hover/tap。
- 螢幕截圖：兩種指標各一張、hover 中狀態一張、觸控 tap 中狀態一張（或桌面模擬）。
- 安全性檢查：不適用（純前端顯示邏輯，無新輸入處理、無新網路呼叫）。

## 完成證據

- 變更的檔案：
  - `frontend/src/pages/Dashboard.tsx`（新增 `GrowthMetric` 型別與 `GROWTH_METRIC_LABELS`；新增共用 `useChartHover` hook 與 `ChartTooltip` 元件；`VocabGrowthChart` 改為接受 `metric` prop，計算 `cumulativeValues`／依 metric 切換顯示資料、末端標籤、資料表格欄位；`Dashboard()` 新增 `growthMetric` state 與 `CardHeader` 內的 `Select` 下拉）
- 執行過的指令：
  - `npm run build`（`tsc -b && vite build`）→ 通過，無型別錯誤
  - `npm run lint`（`oxlint`）→ 通過，僅既有、與本卡無關的 5 個 `only-export-components` 警告（既有檔案，非本卡新增）
  - 本機同時啟動後端（`venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`）與前端（`npm run dev -- --host 127.0.0.1 --port 5173`），用真實資料庫（47 筆德文單字）驗證
- 測試輸出：無自動化測試（前端無測試框架，沿用既有慣例），以 build/lint 通過＋瀏覽器手動操作為準
- 螢幕截圖：Claude 用瀏覽器自動化工具實測並目視確認（未落地存檔）：
  1. 預設「每日新增」下拉選單正確顯示中文標籤（非原始 value 字串——過程中發現並修正了 base-ui `SelectValue` 在下拉未曾開啟前會顯示原始 `value`「daily」而非標籤「每日新增」的問題，改用 `<SelectValue>{(value) => GROWTH_METRIC_LABELS[value]}</SelectValue>` render-prop 寫死中文標籤）
  2. 切換為「累積總量」：折線變成 0→47 的遞增曲線，末端標籤正確顯示「今天累積 47 字」
  3. Hover 折線中段資料點：出現 guideline 虛線＋浮動框，內容為「7/26」「累積 19 字」，位置與數值正確
  4. 滑鼠移出圖表：tooltip 正確消失
  5. 展開「顯示資料表格」：欄位標題正確顯示「累積單字量」，14 筆逐日累積數值與圖表一致（0,0,0,0,0,0,16,19,25,31,32,36,42,47）
- 已知限制：
  1. ~~觸控裝置的 tap 開合~~ → Niko 2026-08-02 用手機實測確認無問題。
  2. 累積總量的計算基準是 14 天視窗內的逐日累加（非全站歷史總單字量），已在卡片與 mockup 決策文件註明避免與側欄「總單字量」混淆；本次測試資料剛好全部 47 筆單字都在 14 天內，因此兩個數字相同，未能用不同數字的情境驗證區別是否夠清楚，建議之後累積更久的資料再看一次。

## 2026-08-02 追加修正：Tooltip 對不準的 bug

- Niko 於 2026-08-01 在真實桌面瀏覽器回報 hover tooltip 「對不準」，經 devtools 檢查確認根因：圖表 `<svg viewBox="0 0 700 170">` 用 `width="100%"` 但未設定 `preserveAspectRatio`，預設值 `xMidYMid meet` 在寬螢幕視窗下會讓實際內容只置中填滿一小段，其餘留白（letterboxing），導致 `useChartHover` 依 `rect.width` 換算座標時算錯。此問題在 Claude 的瀏覽器自動化測試中未重現（自動化工具的座標派送方式不受此影響），僅在 Niko 的實機螢幕上出現。
- **第一版修正（已撤銷）**：曾嘗試加 `preserveAspectRatio="none"` 讓內容拉伸填滿容器。build/lint 通過、自動化 hover 測試也顯示對準了，但 Niko 實測回報「字很扁」——`preserveAspectRatio="none"` 對 X/Y 軸做不同比例的非等比縮放，連帶把 `<text>` 座標系一起拉伸變形，導致座標軸刻度、日期標籤、tooltip 文字全部視覺失真。此修正已撤銷。
- **正式修正**：改為保留預設 `preserveAspectRatio`（`xMidYMid meet`），不去動視覺渲染；而是修正 `useChartHover`（`Dashboard.tsx` 的 `nearestIndexAt`）的座標換算邏輯本身——用 `scale = Math.min(rect.width / viewBoxWidth, rect.height / viewBoxHeight)` 算出瀏覽器實際套用的縮放比例，再用 `offsetX = (rect.width - viewBoxWidth * scale) / 2` 算出置中留白的偏移量，還原成正確的 `svgX`。這樣視覺渲染完全不受影響（文字不變形），只修正滑鼠座標對應到資料點的數學。
- 已重新執行 `npm run build`／`npm run lint`，皆通過；瀏覽器自動化重新 hover 峰值點（+16 資料點），tooltip 正確顯示且文字清晰無變形。
- **Niko 2026-08-02 於本機真實瀏覽器確認**：「圖表都是對的」——hover 對準與文字清晰度問題皆已解決。
- 後續任務：TASK-045（追劇時間趨勢卡片，重用本卡的 `useChartHover`／`ChartTooltip`）。
