# AI-Ready 任務卡

## Metadata

- 任務：TASK-043 設定頁（前端，含 AppRail 入口與真實 API 串接）
- 上層規格：`ai/artifacts/設定與偏好/feature-spec.md`、`screen-spec-settings.md`、`mockup-decision-settings.md`
- 上層 Epic：設定與偏好
- 上層 User Story：每日新卡引入上限設定
- 分軌：前端
- 前置任務（dependsOn）：TASK-042
- 狀態：審查中
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-27（mockup 變體 A 已選定，見 `mockup-decision-settings.md`）

## 目標

新增 `/settings` 頁面（選定變體 A：置中單卡表單），`AppRail` 主導覽新增設定入口，實際串接 TASK-042 的 `GET`／`PATCH /settings`，讓 Niko 能在網頁上查看與調整「每日新卡引入上限」。

## 情境包（Context Pack）

- 相關檔案：
  - `frontend/src/lib/dashboard-api.ts`（新增 `fetchSettings()`／`updateSettings()`，沿用既有 `apiGet`／`apiPatch`）
  - `frontend/src/pages/Settings.tsx`（新增畫面）
  - `frontend/src/components/app-rail.tsx`（`NAV_ITEMS` 新增一筆設定項目）
  - `frontend/src/lib/router.tsx`（`AppRoute`／`KNOWN_ROUTES` 新增 `"/settings"`）
  - `frontend/src/App.tsx`（新增 `path === "/settings"` 分支）
- 既有模式：
  - API client：比照 `dashboard-api.ts` 既有的 `fetchXxx`／`updateXxx` 函式寫法，用既有 `apiGet`／`apiPatch`（`frontend/src/lib/api.ts`），不新增 `apiPut` 之類的新 helper（後端端點已定為 `PATCH`，見 TASK-042）。
  - 導覽：`AppRail`（`frontend/src/components/app-rail.tsx`）`NAV_ITEMS` 陣列直接加一筆 `{ route: "/settings", label: "設定", icon: SettingsIcon }`（`lucide-react` 既有圖示庫，比照現有 `LayoutDashboardIcon` 等寫法），不需改 `AppRail` 元件邏輯本身。
  - 路由：比照 `frontend/src/lib/router.tsx` 既有 `AppRoute` 型別與 `KNOWN_ROUTES` 陣列的加法模式（純字串聯集，非新路由邏輯）。
  - 表單元件：`Field`＋`Input`＋`Button`＋`Card`（`frontend/src/components/ui/`），錯誤態用 `Input` 既有的 `aria-invalid`／`Field` 的錯誤文字連動；成功提示用既有 `sonner` toast（`frontend/src/components/ui/sonner.tsx`），比照 `Vocabulary.tsx` 新增/編輯成功時的 toast 用法。
- 假設：
  - 版面採 mockup 變體 A：置中單卡（`max-width: 480px` 上下），非分組清單版型（變體 B 未選）。
  - 前端做基本的即時輸入驗證（1～500 整數）避免明顯錯誤送出，但仍要處理後端 422 的情況（例如兩個分頁同時修改的極端情境），不能只靠前端驗證。
  - 頁面沒有「取消」按鈕（單一欄位、單一動作，改錯了直接改回原數字再存即可，不需要額外的取消狀態管理）。
- 未知事項：無。
- 允許變更的檔案：見上方「相關檔案」清單。
- 不得觸碰：其他既有頁面（`Vocabulary.tsx`、`MediaLog.tsx`、`Review.tsx` 等）、`AppRail` 既有導覽項目的順序與樣式邏輯（只新增一筆，不重排既有項目）。

## 需求

- `AppRail` 主導覽群組新增「設定」入口（沿用 icon-only 按鈕樣式與既有 active 狀態邏輯），點擊導向 `/settings`。
- `/settings` 頁面開啟時呼叫 `GET /settings`，顯示目前的「每日新卡引入上限」數值；讀取中顯示 loading 態（輸入框停用或 skeleton，比照既有頁面 loading 慣例）；讀取失敗顯示錯誤狀態＋重試按鈕。
- 輸入框旁／下方顯示說明文字：「複習佇列每天最多引入幾張全新單字（不影響已到期需複習的舊卡）」。
- 輸入非 1～500 整數時，前端擋下送出並顯示錯誤文字「請輸入 1～500 之間的整數」，`Input` 呈現 `aria-invalid` 錯誤態。
- 送出合法值：呼叫 `PATCH /settings`，成功後 toast 提示「已儲存」，輸入框顯示新值；若後端回 422，顯示對應錯誤文字，不假裝成功。
- 儲存中按鈕顯示 loading 態並停用，避免重複送出。

## 驗收標準

- 開啟 `/settings`，畫面顯示目前的每日新卡上限值（初次應為 15，或前面測試中改過的值）。
- 輸入 0 或 501 或非數字，按儲存無反應且顯示驗證錯誤文字，未呼叫 API（或呼叫後端 422 但前端已先擋下多數情境，兩者皆需驗證覆蓋）。
- 輸入合法值（例如 10）按儲存，出現「已儲存」toast，重新整理頁面後仍顯示 10（代表確實寫回後端持久化）。
- 點擊 `AppRail` 的設定圖示能正確導向 `/settings`，且該圖示在 `/settings` 頁顯示 active 態；點擊其他既有導覽項目仍正常運作，未被本次變更影響。
- `cd frontend && npm run build` 成功。
- `cd frontend && npm run lint` 無新增錯誤。
- Niko 本機以瀏覽器實際操作 `/settings` 頁面（讀取、修改、驗證錯誤、重新整理確認持久化）確認符合上述驗收標準後核准轉 done。

## 實作備註

- `Settings.tsx` 結構比照 mockup `ai/artifacts/設定與偏好/mockups/settings-variant-a.html` 的版面（eyebrow＋標題＋說明文字＋置中 Card），但用真實 React 元件（`Field`／`Input`／`Button`／`Card`）而非 mockup 的手刻 CSS。
- loading／error 狀態可參考既有 `Vocabulary.tsx` 或 `MediaLog.tsx` 對 `useApi` loading/error 狀態的既有處理慣例（沿用 `frontend/src/hooks/use-api.ts`）。
- 表單 local state：`inputValue`（輸入框當前字串）、`validationError`（前端驗證錯誤文字或 null）、`saving`（是否送出中）；儲存成功後用 API 回傳值同步 `inputValue`，不是直接信任使用者輸入值。

## 驗證契約

- 單元測試：無新增（本專案前端無元件單元測試套件，沿用專案慣例）。
- 整合測試：不適用（前端無整合測試套件）。
- E2E 測試：無（沿用專案慣例，以 Niko 本機手動驗證取代）。
- 型別檢查：`npm run build`（TypeScript 隨 Vite build 檢查）。
- Lint：`npm run lint`。
- Build：`npm run build`。
- 螢幕截圖：Niko 本機操作截圖或口頭確認皆可（沿用本專案既有驗證慣例）；需涵蓋預設、驗證錯誤、儲存成功三種狀態。
- 安全性檢查：不適用（低風險、無新增輸入寫入資料庫的敏感欄位，僅數字設定）。

## 完成證據

- 變更的檔案：
  - `frontend/src/lib/dashboard-api.ts`（新增 `AppSettings` 型別、`fetchSettings()`／`updateSettings()`）
  - `frontend/src/pages/Settings.tsx`（新增，置中單卡表單，loading/error/success 三態，前端驗證 1～500 整數，儲存成功用 `sonner` toast）
  - `frontend/src/components/app-rail.tsx`（`NAV_ITEMS` 新增「設定」項目，`SettingsIcon`）
  - `frontend/src/lib/router.tsx`（`AppRoute`／`KNOWN_ROUTES` 新增 `"/settings"`）
  - `frontend/src/App.tsx`（新增 `path === "/settings"` 分支）
- 執行過的指令：
  - `npm run build`（`tsc -b && vite build`）→ 通過，無型別錯誤
  - `npm run lint`（`oxlint`）→ 通過，僅既有、與本卡無關的 5 個 `only-export-components` 警告
  - 本機同時起後端(8000)/前端(5173)，實際串接真實 `/settings` API 驗證
- 測試輸出：無自動化測試（前端無測試框架，沿用既有慣例），以 build/lint 通過＋瀏覽器手動操作為準
- 螢幕截圖：Claude 用瀏覽器自動化工具實測並目視確認（未落地存檔）：
  1. 預設狀態：開啟 `/settings` 正確顯示目前值 15，AppRail 設定圖示 active
  2. 驗證錯誤狀態：輸入 0，按儲存後顯示紅框＋「請輸入 1～500 之間的整數」，未送出 API
  3. 儲存成功：輸入 20 按儲存，出現「已儲存」toast；重新整理頁面後仍顯示 20（確認持久化），測試後已改回 15 還原 Niko 的實際設定
- 已知限制：
  1. 後端 422 情境（例如非法值繞過前端驗證，或極端情況下兩個分頁同時修改）僅檢查程式邏輯（`try/catch` 顯示 `ApiError` 訊息），未實際模擬觸發過。
  2. 未實測窄螢幕（手機）版面，僅依既有頁面相同版面模式（無新增響應式規則）。
- 後續任務：無（本 User Story 到此完整），待 Niko 本機驗證後核准轉 done。
