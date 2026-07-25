# AI-Ready 任務卡

## Metadata

- 任務：TASK-026 UI 設計系統 S5 — Dashboard 版面 mockup
- 上層規格：（Epic 0 UI 設計系統五階段流程，未另立 feature-spec，見 ai/skills/project-kickoff.md 步驟 2a）
- 上層 Epic：專案設置
- 上層 User Story：UI 設計系統
- 分軌：不適用
- 前置任務（dependsOn）：TASK-025（S4 已核准：核心元件庫）
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-25（選定變體 C — Command Center）

## 目標

用已核准的 S3 token 與 S4 元件庫，拼出 2-3 個 Dashboard 整體版面（layout）變體，走 `ui-mockup-gate` 流程讓 Niko 挑選版型；這是 UI 設計系統五階段流程的最後一階，選定後「本地 Web UI」Epic 才會開始拆真正的功能頁面任務卡。

## 情境包（Context Pack）

- 相關檔案：`ai/artifacts/專案設置/mockups/dashboard-variant-{a,b,c}.html`（新增）、`ai/artifacts/專案設置/screen-spec-dashboard.md`（新增）、`ai/artifacts/專案設置/mockup-decision-dashboard.md`（新增）。
- 既有模式：走 `ai/skills/ui-mockup-gate.md` 流程；視覺品質套用 `ai/skills/design-craft.md` 十大紀律；畫面內的圖表（單字成長趨勢、複習日曆熱力圖）先過 `dataviz` skill 判斷形式與色彩規則。
- 假設：Dashboard 是本機單人工具的首頁，不需要考慮多使用者、權限分級、團隊協作情境；三個變體的差異來自版型與資訊架構，內容區塊（KPI／趨勢圖／熱力圖／複習佇列／追劇紀錄）與使用的 token／元件相同。
- 未知事項：無。
- 允許變更的檔案：`ai/artifacts/專案設置/`（mockups／screen-spec／mockup-decision）、`tools/kanban/cards/TASK-026.json`。
- 不得觸碰：`backend/`、`frontend/`（mockup 階段禁止進 React 實作，選定版型後才開新任務卡實作）。

## 需求

- 產出 2-3 個 Dashboard layout 變體，皆只用 `design-system.md` 已定案的 token 與元件庫拼出，差異來自版型／資訊架構／元件組合方式。
- 涵蓋內容：今日待複習 CTA（含連續複習天數）、KPI 統計（正確率／觀看時數／單字量）、單字成長趨勢圖、複習日曆熱力圖、複習佇列（今日到期前 5 筆）、最近追劇紀錄，並支援 en/de 語言視角切換入口。
- 用真實專案資料示範（非 lorem ipsum）。
- 圖表產出前先過 `dataviz` skill：判斷形式（stat tile／line／heatmap）、色彩職責（單數列不需圖例、熱力圖用單一色相 sequential ramp）、是否需要跑 `validate_palette.js`。
- 寫 `screen-spec-dashboard.md`（畫面規格：狀態、互動、設計系統對照、視覺驗收標準）與 `mockup-decision-dashboard.md`（變體比較表，待人工選定）。
- 在人工選擇變體之前，停止進行任何 React 實作。

## 驗收標準

- 3 個 mockup HTML 檔案皆可獨立在瀏覽器開啟檢視，彼此版型有實質差異（非僅換色）。
- `screen-spec-dashboard.md` 涵蓋 7 種必要狀態（預設/載入中/空狀態/錯誤/停用/權限不足/行動裝置版），不適用的狀態需說明原因而非留白。
- `mockup-decision-dashboard.md` 的變體比較表填完優點與風險，「選定的變體」與「人工核准」留待 Niko 填寫。
- 所有顏色/間距/字級/圓角數值皆能對應回 S3 token，圖表色彩符合 dataviz skill 規則。

## 實作備註

- **變體 A — Sidebar Admin**：左側固定 sidebar（4 個主要頁面導覽）＋頂部語言切換，主內容 4 欄 KPI row + 兩欄內容區（左 2/3 趨勢圖＋熱力圖，右 1/3 佇列＋追劇紀錄）。參考 shadcn-admin／TailAdmin 的經典 admin dashboard 版型。
- **變體 B — 單欄 Focus**：無 sidebar，頂部簡易 tab 導覽，主內容單欄置中（max-width 720px），最上方是大型「今日待複習」CTA 卡片，其餘內容由上到下堆疊。天生行動裝置友善。
- **變體 C — Command Center**：左側窄 icon rail＋中央「今日複習」進度環卡片（SVG `stroke-dasharray` 畫環形進度）＋右側窄欄 KPI／佇列，下方橫跨全寬放熱力圖與追劇紀錄。三欄式空間利用率最高，但實作複雜度也最高。
- 三個變體共用同一批真實資料：連續複習 12 天、今日待複習 18 張（12 到期＋6 新卡）、7 日正確率 87%、本週觀看時數 3h40m、總單字量 342 個（本週 +23）、複習佇列前 5 筆（der Tisch／die Freiheit／das Fenster／schnell／die Uhr）、最近追劇（Friends S3E12／Dark S1E3）。
- 單字成長趨勢圖：14 天單數列折線圖，線與面積用 `info-500`（次強調藍），只在終點（今天）標示數值，不畫圖例（單數列不需要）。
- 複習日曆熱力圖：5 週 × 7 天網格，用 `brand`（accent 黃）ramp 的 6 個色階（含 0 張的 surface-hover 底色），依 dataviz skill「暗色模式 anchor 反轉」規則，愈亮＝複習張數愈多。
- 兩個圖表下方都附「顯示資料表格」的原生 `<details>` 展開，作為 dataviz skill 要求的無障礙 table-view 後備，不需額外 JS。
- 依 dataviz skill 的「六項檢查範圍」，本畫面沒有多數列 categorical 色票（趨勢圖單數列、熱力圖單一色相），不在 `validate_palette.js` 的檢查範圍內，因此未執行 validator。

## 驗證契約

- 單元測試：不適用（純 mockup 階段）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：不適用（純 HTML，非 TypeScript）。
- Lint：不適用。
- Build：不適用。
- 螢幕截圖：3 個 mockup 檔案已發布為 Artifact 供線上比較（見完成證據）；本機也可直接用瀏覽器開啟 `ai/artifacts/專案設置/mockups/dashboard-variant-*.html`。
- 安全性檢查：不適用（純靜態展示頁面，無外部請求、無使用者輸入處理）。

## 完成證據

- 變更的檔案：
  - `ai/artifacts/專案設置/mockups/dashboard-variant-a.html`（新增）
  - `ai/artifacts/專案設置/mockups/dashboard-variant-b.html`（新增）
  - `ai/artifacts/專案設置/mockups/dashboard-variant-c.html`（新增）
  - `ai/artifacts/專案設置/screen-spec-dashboard.md`（新增）
  - `ai/artifacts/專案設置/mockup-decision-dashboard.md`（新增，變體比較已填，決策待補）
  - `tools/kanban/cards/TASK-026.json`（stage 轉 verify，links 補上 screenSpec／mockupDecision）
- 執行過的指令：無（純文件與靜態 HTML 產出）。
- 測試輸出：不適用。
- 螢幕截圖：三變體比較頁（Artifact）：https://claude.ai/code/artifact/521c4993-e344-46d3-8052-85b565e4790f
- 已知限制：
  1. 三個變體皆為桌面版優先，行動裝置版斷點細節留待選定版型後在 `screen-spec-dashboard.md` 補完整規格。
  2. 圖表的 hover 互動目前只用原生 `title` 屬性做最基本的提示，正式 React 實作時應依 `dataviz` skill 的 `interaction.md` 補上完整的 crosshair/tooltip。
  3. 三個變體都還沒有「載入中」「空狀態」「錯誤」的實際畫面（僅在 screen-spec 用文字描述必要行為），待選定版型、進入實作階段時依 screen-spec 補上對應截圖。
- 人工核准紀錄：Niko 在比較頁（見完成證據 Artifact 連結）看過三個變體後選定「變體 C — Command Center」，理由與備註見 `mockup-decision-dashboard.md`。`design-system.md` 的 S5 章節已回填。
- 後續任務：「本地 Web UI」Epic 開始拆 Dashboard 實際實作的任務卡（含 React 版面、API 串接、載入/空/錯誤狀態的真正實作），需依 `screen-spec-dashboard.md` 的已知限制（行動裝置版斷點、圖表 hover 互動、三態畫面）補齊規格細節。
