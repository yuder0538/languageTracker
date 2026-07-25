# AI-Ready 任務卡

## Metadata

- 任務：TASK-027 本地 Web UI — Epic 架構基礎
- 上層規格：（無獨立 feature-spec；範圍由 Niko 在對話中確認：本輪只做 Dashboard 頁面本身，不含單字庫/追劇紀錄管理 CRUD 畫面）
- 上層 Epic：本地 Web UI
- 上層 User Story：Epic 架構基礎
- 分軌：前端
- 前置任務（dependsOn）：TASK-001, TASK-002, TASK-003, TASK-004, TASK-005, TASK-006, TASK-007, TASK-008, TASK-009, TASK-010, TASK-011, TASK-012, TASK-013, TASK-014, TASK-015, TASK-016, TASK-017, TASK-018, TASK-019, TASK-020, TASK-021, TASK-022, TASK-023, TASK-024, TASK-025, TASK-026（「專案設置」Epic 全部卡片，依 `ai/skills/project-kickoff.md` 的強制連動規則）
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：（實作階段，非 UI 決策，依 `ai/process/review-gates.md` 不需 UI 關卡；已通過程式碼審查與自我檢查）

## 目標

建立「本地 Web UI」Epic 底下所有頁面共用的基礎設施：API client 封裝、en/de 語言 context 與切換、Vite dev server 代理設定，供 Dashboard 與後續頁面共用。

## 情境包（Context Pack）

- 相關檔案：`frontend/vite.config.ts`、`frontend/src/lib/api.ts`、`frontend/src/lib/language-context.tsx`、`frontend/src/main.tsx`。
- 既有模式：後端已在 `backend/app/api/router.py` 用 `/api/v1` 前綴掛載所有路由；前端 S4 已建立 shadcn/ui 元件庫與 design token。
- 假設：本產品是本機單人工具，不需要處理跨網域 CORS（改用 Vite dev proxy 讓瀏覽器端請求同源）；不需要身分驗證/授權（單人本機使用）。
- 未知事項：正式 production build 如何與後端共同部署（例如 FastAPI 掛載靜態檔案，或分開跑）尚未決定，目前只處理 `npm run dev` + `uvicorn --reload` 的本機開發情境，這也是兩份 README 目前唯一支援的用法。
- 允許變更的檔案：`frontend/`。
- 不得觸碰：`backend/`（本卡不改後端；後端變更見 TASK-028）。

## 需求

- API client：`fetch` 封裝，統一處理 `/api/v1` 前綴、JSON 標頭、錯誤訊息解析（FastAPI 的 `{"detail": "..."}` 格式）、204 無內容回應。
- en/de 語言 context：全域狀態＋切換函式，預設 `de`（呼應 S2/S3 決議：暗色/字幕夜場為主要使用情境），存到 `localStorage`（與 `next-themes` 的主題持久化模式一致）。
- Vite dev proxy：`/api` 代理到 `http://127.0.0.1:8000`（後端 `uvicorn` 預設 port，見 `backend/README.md`）。
- **刻意不做**（YAGNI，避免過度設計）：
  - 前端路由器（React Router 等）：目前只有 Dashboard 一個頁面，還不需要；等下一個真正的頁面（單字庫或追劇紀錄管理）動工時再引入，屆時本卡的 nav 佔位按鈕會改成真正的連結。
  - POST/PATCH/DELETE 的 API client 方法：Dashboard 是唯讀頁面，只需要 `apiGet`；等 CRUD 頁面動工時再擴充。

## 驗收標準

- `frontend/vite.config.ts` 設定 dev proxy，開發時瀏覽器可用相對路徑 `/api/v1/...` 呼叫後端，不會有 CORS 錯誤。
- 語言 context 切換後，重新整理頁面仍保留使用者上次選的語言。
- API client 對非 2xx 回應拋出帶有 FastAPI `detail` 訊息的錯誤，供呼叫端顯示。

## 實作備註

- `apiGet<T>(path, params)`：組出查詢字串（跳過 `undefined` 值），呼叫 `/api/v1{path}`，非 2xx 時嘗試解析 `{"detail": "..."}` 並包成 `ApiError`。
- `LanguageProvider`／`useLanguage`：`localStorage` key 為 `immersion-tracker:language`，與 `index.html` 裡 theme 的 FOUC 防閃爍腳本走同一種持久化慣例（不同 key，同樣手法）。
- Vite proxy 只在 `npm run dev` 生效；`changeOrigin: true` 避免後端看到的 Host header 是前端 origin。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架，`frontend/README.md` 也未設置）。
- 整合測試：不適用（由 TASK-029 的 Dashboard 頁面實際串接驗證）。
- E2E 測試：不適用。
- 型別檢查：待人工在本機執行 `npm run build`（`tsc -b && vite build`）確認；此執行環境無 Node.js，未能跑。
- Lint：待人工在本機執行 `npm run lint`確認；此執行環境無 Node.js，未能跑。**已知會有一項 warning**：`react/only-export-components`（`warn` 等級，不影響 lint 結果為 0 exit code）可能對 `language-context.tsx` 同時匯出 `LanguageProvider` 元件與 `useLanguage` hook 提出警告；這是 React context 慣用寫法（`next-themes` 自己的 `ThemeProvider` 也是同檔案export hook），不視為需要修正的問題。
- Build：待人工在本機執行 `npm run build` 確認；此執行環境無 Node.js，未能跑。
- 螢幕截圖：不適用（本卡無視覺產出，見 TASK-029）。
- 安全性檢查：不適用（純本機開發代理設定，無外部網路存取、無金鑰）。

## 完成證據

- 變更的檔案：
  - `frontend/vite.config.ts`（新增 dev proxy）
  - `frontend/src/lib/api.ts`（新增，API client）
  - `frontend/src/lib/language-context.tsx`（新增，語言 context）
  - `frontend/src/main.tsx`（掛上 `LanguageProvider`）
- 執行過的指令：無（此環境無 Node.js，見上方驗證契約與已知限制）。
- 測試輸出：不適用，待人工本機驗證（`npm run build`／`npm run lint`）。
- 螢幕截圖：不適用。
- 已知限制：此執行環境沒有 Node.js，程式碼正確性僅靠審查把關，尚未經編譯器與 lint 實際驗證；production 部署策略未決定，目前僅支援本機開發雙進程（`npm run dev` + `uvicorn --reload`）。
- 後續任務：TASK-028（複習歷史聚合 API）、TASK-029（Dashboard 頁面實作，使用本卡的 API client 與語言 context）。
