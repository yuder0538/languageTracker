# AI-Ready 任務卡

## Metadata

- 任務：TASK-025 UI 設計系統 S4 — 核心元件庫
- 上層規格：（Epic 0 UI 設計系統五階段流程，未另立 feature-spec，見 ai/skills/project-kickoff.md 步驟 2a）
- 上層 Epic：專案設置
- 上層 User Story：UI 設計系統
- 分軌：不適用（本任務卡不拆分軌，一次做完整個元件庫）
- 前置任務（dependsOn）：TASK-024（S3 已核准：字幕夜場 Subtitle Room 完整 primitive/semantic token）
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-25

## 目標

只用 S3 核准的 design token，建立可跑的 `frontend/`（Vite+React+Tailwind+shadcn/ui）專案骨架與核心元件庫（button/input/select/checkbox/card/nav/modal/table/form/toast），每個元件涵蓋必要狀態，並登記回 `design-system.md` 的「S4 元件庫 Inventory」。

## 情境包（Context Pack）

- 相關檔案：`frontend/`（整個專案骨架與元件）、`ai/context/design-system.md`（S4 章節）。
- 既有模式：套用 `ai/skills/design-craft.md` 十大紀律；元件實作採 shadcn/ui「base-nova」style，以 `@base-ui/react` primitive 包裝、`class-variance-authority` 管理 variant，這是既有慣例（S1 核准的元件庫策略），非本卡新增。
- 假設：本產品是本機單人使用工具，表單複雜度低，不需要 react-hook-form/zod 等表單狀態管理庫；Form 元件用輕量的 `Field`/`FieldLabel`/`FieldDescription`/`FieldError` 組合 + React controlled state 即可。
- 未知事項：無。
- 允許變更的檔案：`frontend/`、`ai/context/design-system.md`、`tools/kanban/cards/TASK-025.json`。
- 不得觸碰：`backend/`。

## 需求

- 涵蓋 button、input、select、checkbox、card、nav、modal/dialog、table、form、toast/alert 十類元件（實際落地為 13 個檔案，因應 shadcn/ui 的元件切分慣例）。
- 每個元件涵蓋必要狀態：預設、hover、focus、停用、載入（button）、錯誤（input/select/checkbox）。
- 全部只用 S3 token，不得引入新色值/字級/間距。
- 用真實專案資料（非 lorem ipsum）在一個可視化展示頁（`frontend/src/App.tsx`）中示範所有元件與狀態。
- 登記進 `design-system.md` 的「S4 元件庫 Inventory」表格。

## 驗收標準

- `frontend/` 可透過 `npm install && npm run dev` 啟動，`App.tsx` 完整展示全部元件與必要狀態。
- `design-system.md` 的 S4 章節不再是「待補」，inventory 表每列都填了狀態、涵蓋狀態、用到的 token、檔案位置。
- 所有元件的顏色/圓角/間距/字級都能對應回 S3 token 表，沒有孤立新值。
- 人工在本機跑起來確認外觀與互動後核准。

## 實作備註

- 專案骨架與大部分元件（shadcn/ui CLI 拉入的 button/input/select/checkbox/card/navigation-menu/dialog/table/badge/alert/label/separator/sonner/switch）在本卡執行前已由前一輪工作建立好，本卡接手時的缺口是：Button 缺 loading 狀態、缺 Form 組合元件、`App.tsx` 仍是 Vite 預設模板（未展示任何實際元件）、`design-system.md` S4 章節仍是「待補」模板。
- Button 新增 `loading` prop：顯示 `Loader2Icon`（lucide-react，`animate-spin`）、`aria-busy`、並在 loading 時等同 disabled（互斥處理：`disabled={disabled || loading}`）。
- 新增 `frontend/src/components/ui/field.tsx`：`Field`（外層 flex 容器）／`FieldLabel`（包 `Label`，錯誤時變色）／`FieldDescription`／`FieldError`（無內容時回傳 `null`，避免空白 `<p>`）。刻意不用 react-hook-form/zod，理由見「情境包」假設。
- `App.tsx` 改為完整元件庫展示頁，用德文單字（der Tisch）、追劇紀錄（Friends S3E12）、複習排程（到期/排程中/Leech/已學會）等真實專案資料示範，並含亮／暗模式切換按鈕（`next-themes` 的 `useTheme`）。
- 移除未使用的 Vite 預設模板殘留：`App.css`、`assets/react.svg`、`assets/vite.svg`、`assets/hero.png`。

## 驗證契約

- 單元測試：不適用（此階段無測試框架設置，元件皆為 shadcn/ui 標準包裝）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：Niko 在本機執行 `npm run build`（`tsc -b && vite build`）確認，無錯誤。
- Lint：Niko 在本機執行 `npm run lint`（oxlint）確認，無錯誤。
- Build：Niko 在本機執行 `npm run build` 確認，無錯誤。
- 螢幕截圖：Niko 在本機執行 `npm run dev` 後目視確認展示頁（暗色背景、八大區塊標題皆顯示、亮暗模式切換正常、單字表格顯示德文資料、無破版或錯誤）。
- 安全性檢查：不適用（純前端展示元件，無外部輸入處理、無網路請求）。

## 完成證據

- 變更的檔案：
  - `frontend/src/components/ui/button.tsx`（新增 loading 狀態）
  - `frontend/src/components/ui/field.tsx`（新增，Form 組合元件）
  - `frontend/src/App.tsx`（改為完整元件庫展示頁）
  - `frontend/src/App.css`、`frontend/src/assets/{react.svg,vite.svg,hero.png}`（刪除，Vite 模板殘留）
  - `ai/context/design-system.md`（填寫 S4 章節 inventory 表）
  - `tools/kanban/cards/TASK-025.json`（stage 轉 done）
- 執行過的指令：Agent 端無（此環境無 Node.js）；Niko 本機執行 `npm install`、`npm run dev`、`npm run build`、`npm run lint`，皆無錯誤。
- 測試輸出：無自動化測試（此階段無測試框架設置），以 `npm run build`／`npm run lint` 通過 + 人工目視驗證為準。
- 螢幕截圖：Niko 本機執行 `npm run dev` 目視確認，未另外產出圖檔。
- 已知限制：
  1. Agent 執行環境沒有 Node.js，程式碼由 Niko 在本機驗證，Agent 端未親自跑過編譯器與 lint。
  2. Form 元件刻意不含 react-hook-form 等表單狀態管理庫（見實作備註理由），若後續功能 Epic 出現複雜表單驗證需求，屆時再評估是否要補上。
  3. Checkbox 沒有獨立的「載入」狀態示範（設計上 checkbox 沒有非同步載入語意，故此狀態不適用）。
- PR：https://github.com/yuder0538/languageTracker/pull/1（draft）
- 後續任務：TASK-026（S5 Dashboard 版面 mockup），`gates.ui`／`gates.product`／`gates.test` 已通過，可以開工。
