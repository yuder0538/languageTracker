# AI-Ready 任務卡

## Metadata

- 任務：TASK-024 UI 設計系統 S3 — Design Token
- 上層規格：（Epic 0 UI 設計系統五階段流程，未另立 feature-spec，見 ai/skills/project-kickoff.md 步驟 2a）
- 上層 Epic：專案設置
- 上層 User Story：UI 設計系統
- 分軌：不適用（決策文件，非程式碼）
- 前置任務（dependsOn）：TASK-023（S2 已核准：字幕夜場 Subtitle Room，暗色為主）
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

從 S2 選定的「字幕夜場 Subtitle Room」風格方向，展開完整的 primitive token（色彩、字級、字重/行高、間距、圓角、陰影、z-index、動效）與 semantic token（暗模式為主、亮模式對應值），寫進 `ai/context/design-system.md` 的 S3 章節。

## 情境包（Context Pack）

- 相關檔案：`ai/context/design-system.md`（S3 章節）。
- 既有模式：套用 `ai/skills/design-craft.md` 的 scale 紀律 — 間距只用 4 的倍數、字級只用 11/12/13/14/16/18/20/24/30/36/48、grey scale 為主再疊 primary/semantic、depth 三選一（暗模式選背景分層、亮模式對應改用陰影）。
- 假設：專案尚無可跑的前端框架（S4 才建立 Vite+React 骨架），依 project-kickoff 步驟 2a 允許先只寫 token 表、不產出實際 token 檔，S4 建骨架時再回填 `tailwind.config.ts` 路徑。
- 未知事項：無。
- 允許變更的檔案：`ai/context/design-system.md`、`tools/kanban/cards/TASK-024.json`。
- 不得觸碰：`backend/`。

## 需求

- Primitive token：grey scale（含各階明度）、accent scale（字幕黃）、secondary scale（次強調藍，兼作 info）、語意色（success/warning/danger，與 accent 分開色相）、字級 scale、字重、行高、字距、間距 scale、圓角、陰影、z-index、動效時間與曲線。
- Semantic token：暗模式（主要）與亮模式（次要，供系統跟隨）皆需定義，不可只做暗模式。
- 全部寫進 `design-system.md` 的「S3 Design Token 清單」。

## 驗收標準

- `design-system.md` 的 S3 章節不再是「待補」，primitive 與 semantic token 表皆完整，暗/亮模式皆有對應值。
- 語意色（success/warning/danger/info）與主強調色（accent，字幕黃）使用不同色相，不混用。
- 間距/字級/圓角數值全部落在 design-craft 規定的 scale 內，沒有孤立數值。

## 實作備註

- Grey scale 刻意選微暖中性色（非藍調），呼應「電影夜場」氣質而非「科技冷灰」，與 TASK-026（Signal Board 落選方向）的冷灰藍區隔。
- 密度沿用 S2 決議：卡片內距 16px（`space.card`），非舒適密度的 24px。
- 圓角沿用 S2 決議：卡片 3px（字幕框感），互動元件 4px，pill 元件維持 999px 以利掃視。
- 陰影沿用 S2 決議：暗模式預設不用陰影、靠 `surface`/`surface-hover` 兩階背景分層；亮模式（次要模式）改採陰影，因白底上背景分層不夠明顯。
- 語意色刻意避開字幕黃色相：warning 選偏橘（`#D97B29`）而非黃，避免與主強調色混淆。

## 驗證契約

- 單元測試：不適用（決策文件）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：不適用。
- Lint：不適用。
- Build：不適用（尚無可跑的前端框架）。
- 螢幕截圖：Artifact 預覽頁（見完成證據），token 套用到真實元件的畫面。
- 安全性檢查：不適用。

## 完成證據

- 變更的檔案：
  - `ai/context/design-system.md`（填寫 S3 章節：primitive + semantic token 全表）
  - `tools/kanban/cards/TASK-024.json`（轉為 done）
- 執行過的指令：無（決策與文件任務，非程式碼變更）。
- 測試輸出：不適用。
- 螢幕截圖：token 套用預覽 Artifact（暗色/亮色可切換，涵蓋按鈕五態、輸入框、單字卡、狀態標籤、統計數字、資料表格）：https://claude.ai/code/artifact/881a8386-2f14-4df6-9f9e-e26972a66ecc
- 已知限制：尚無真實 `tailwind.config.ts`／`tokens.css`，token 目前只存在於 `design-system.md` 的表格中；S4 建立前端專案骨架時需將此表轉為實際可跑的設定檔，轉換過程若發現數值需微調（例如 Tailwind 預設色階格式差異），以此表的語意與比例關係為準、允許調整精確 hex 值。
- 人工核准紀錄：Niko 看過 token 預覽 Artifact 後回覆「可以這顏色很棒」，核准轉 done。
- 後續任務：TASK-025（S4 核心元件庫，第一張會建立 `frontend/`〔Vite+React+Tailwind+shadcn/ui〕實際專案骨架的任務卡）。
