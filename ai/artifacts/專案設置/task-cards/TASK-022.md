# AI-Ready 任務卡

## Metadata

- 任務：TASK-022 UI 設計系統 S1 — 底層框架與元件庫策略
- 上層規格：（Epic 0 UI 設計系統五階段流程，未另立 feature-spec，見 ai/skills/project-kickoff.md 步驟 2a）
- 上層 Epic：專案設置
- 上層 User Story：UI 設計系統
- 分軌：不適用（決策文件，非程式碼）
- 前置任務（dependsOn）：無
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko

## 目標

為專案首次展開的「本地 Web UI」Epic 決定底層框架、UI 元件庫策略與樣式方案，寫進 `ai/context/design-system.md` 的 S1 章節，作為後續 S2-S5 與所有前端任務卡的基礎。

## 情境包（Context Pack）

- 相關檔案：`ai/context/design-system.md`（S1 章節）、`tools/kanban/epics.json`。
- 既有模式：無（專案目前為純後端，這是第一次導入前端）。
- 假設：
  - 產品為本機單人使用的工具（見 `ai/artifacts/README.md` 與各 Epic 定義），不需要 SSR、多租戶或伺服端渲染。
  - Epic 定義已明確寫「React SPA」（`tools/kanban/epics.json` 的「本地 Web UI」Epic），故 UI 框架選 React 屬既定方向，本次決策聚焦在建置工具、元件庫策略與樣式方案。
- 未知事項：前端與後端的實際串接方式（開發時 Vite dev server 代理 FastAPI，或直接 CORS 呼叫）留給後續架構基礎任務卡決定。
- 允許變更的檔案：`ai/context/design-system.md`、`tools/kanban/epics.json`、`tools/kanban/cards/`。
- 不得觸碰：`backend/`。

## 需求

- 列出建置工具、元件庫策略、樣式方案各 2-3 個合理選項，附優劣與建議。
- 經人工核准後，把選定結果與理由寫進 `design-system.md` 的「S1 底層框架」章節。

## 驗收標準

- `design-system.md` 的 S1 章節不再是「待補」，包含 UI 框架、元件庫策略、樣式方案、選定理由、人工核准（核准人／日期）。
- 決策已記錄核准者與日期。

## 實作備註

- 提出的選項：
  - 建置工具：Vite + React（推薦，純 SPA、無需 SSR）vs Next.js（過度設計，本機單人工具不需要）。
  - 元件庫策略：shadcn/ui（推薦，程式碼直接複製進專案、非 npm 包裝、利於客製 design token）vs MUI（開發快但 Material Design 識別度重）vs Ant Design（資料密集介面強但視覺風格重）vs 自建（成本最高）。
  - 樣式方案：Tailwind CSS（推薦，與 shadcn/ui 標準搭配）vs CSS Modules vs CSS-in-JS。
- 人工於對話中選定：Vite + React、shadcn/ui、Tailwind CSS。

## 驗證契約

- 單元測試：不適用（決策文件）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：不適用。
- Lint：不適用。
- Build：不適用（尚無可跑的前端專案）。
- 螢幕截圖：不適用。
- 安全性檢查：不適用。

## 完成證據

- 變更的檔案：
  - `ai/context/design-system.md`（填寫 S1 章節）
  - `tools/kanban/epics.json`（新增「UI 設計系統」User Story 於「專案設置」Epic 底下）
  - `tools/kanban/cards/TASK-022.json` ~ `TASK-026.json`（S1-S5 五張任務卡，S1 完成、S2-S5 待辦）
- 執行過的指令：無（決策與文件任務，非程式碼變更）。
- 測試輸出：不適用。
- 螢幕截圖：不適用。
- 已知限制：無。
- 後續任務：TASK-023（S2 視覺風格方向）。
