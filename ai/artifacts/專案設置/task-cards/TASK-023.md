# AI-Ready 任務卡

## Metadata

- 任務：TASK-023 UI 設計系統 S2 — 視覺風格方向
- 上層規格：（Epic 0 UI 設計系統五階段流程，未另立 feature-spec，見 ai/skills/project-kickoff.md 步驟 2a）
- 上層 Epic：專案設置
- 上層 User Story：UI 設計系統
- 分軌：不適用（決策文件，非程式碼）
- 前置任務（dependsOn）：TASK-022（S1 已核准：React + Vite、shadcn/ui、Tailwind CSS）
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

依 S1 選定的框架與元件庫策略，產出 2-3 個 style tile（風格方向，非完整版面），讓人工比較整體氣質後選定一個，寫進 `ai/context/design-system.md` 的 S2 章節。

## 情境包（Context Pack）

- 相關檔案：`ai/context/design-system.md`（S2 章節）。
- 既有模式：套用 `ai/skills/design-craft.md` 十大紀律（4 的倍數間距、type scale、色彩分階、depth 三選一等），並比對高品質開源參考（Linear、shadcn-admin、TailAdmin、Letterboxd 等）。
- 假設：三個提案都用同一批真實專案資料示範（德文單字卡 `der Tisch`、追劇紀錄 `Friends`、複習統計），避免用 lorem ipsum 讓人工看不出實際效果。
- 未知事項：無。
- 允許變更的檔案：`ai/context/design-system.md`、`tools/kanban/cards/TASK-023.json`。
- 不得觸碰：`backend/`。

## 需求

- 產出 2-3 個 style tile，每個涵蓋：色彩情緒（含實際色票）、字體個性、圓角／陰影傾向、密度、亮／暗模式傾向、1-2 個參考產品。
- 以 Artifact 頁面呈現供人工視覺比較（而非純文字描述）。
- 經人工核准後，把選定結果與理由寫進 `design-system.md` 的「S2 風格方向」章節。

## 驗收標準

- `design-system.md` 的 S2 章節不再是「待補」，包含選定的 style tile 名稱、色彩情緒（含色票）、字體個性、圓角/陰影傾向、密度、亮暗模式、參考產品、人工核准（核准人／日期）。

## 實作備註

- 提出的三個 style tile（Artifact 比較頁：https://claude.ai/code/artifact/807a7b73-6256-4e01-98d4-92468d58d0dc）：
  1. **卡片抽屜 Card Catalogue** — 溫暖紙感、襯線標題、亮色為主。參考：Notion 文件模式、圖書館索引卡、Moleskine。
  2. **字幕夜場 Subtitle Room** — 深色電影感、字幕黃強調、等寬數據、暗色為主。參考：電影字幕配色、Letterboxd 深色模式、Terminal 介面。
  3. **學習儀表板 Signal Board** — 冷灰藍中性色、精準藍強調、亮暗雙模完整支援。參考：Linear、shadcn-admin、TailAdmin。
- 人工於對話中選定：**方向二「字幕夜場 Subtitle Room」**（暗色）。

## 驗證契約

- 單元測試：不適用（決策文件）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：不適用。
- Lint：不適用。
- Build：不適用。
- 螢幕截圖：Artifact 比較頁（見上方連結），三個提案皆用真實資料渲染。
- 安全性檢查：不適用。

## 完成證據

- 變更的檔案：
  - `ai/context/design-system.md`（填寫 S2 章節）
  - `tools/kanban/cards/TASK-023.json`（轉為 done）
- 執行過的指令：無（視覺決策任務，非程式碼變更）。
- 測試輸出：不適用。
- 螢幕截圖：Artifact 比較頁連結見上。
- 已知限制：暗色模式為主，亮色對應值留到 S3 定義 token 時一併給出（design-craft 規範兩種模式都要有考量，即使產品目前以暗色為主要使用情境）。
- 後續任務：TASK-024（S3 Design Token，從字幕夜場方向的色彩/字體/密度傾向展開完整 token 表）。
