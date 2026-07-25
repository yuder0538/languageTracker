# AI-Ready 任務卡

## Metadata

- 任務：TASK-030 單字庫頁面實作（含前端路由器導入）
- 上層規格：`ai/artifacts/本地 Web UI/screen-spec-vocabulary.md`、`ai/artifacts/本地 Web UI/mockup-decision-vocabulary.md`（選定變體 A — Dialog 彈窗新增）
- 上層 Epic：本地 Web UI
- 上層 User Story：單字庫管理頁面
- 分軌：前端（後端 API 已存在，不需要後端/串接分卡，見下方情境包）
- 前置任務（dependsOn）：TASK-027, TASK-029
- 狀態：verify（等待人工本機驗證）
- 風險等級：低
- Agent owner：claude
- 人工核准者：（待 Niko 本機執行 `npm run dev` 驗證後追加簽核）

## 目標

做出單字庫頁面：唯讀列表＋新增單字（Dialog 彈窗），並導入最小的前端路由器讓「單字庫」導覽真正可以切換頁面（先前 TASK-027 刻意延後這件事，等真正第二個頁面出現才做）。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/lib/router.tsx`（新增）、`frontend/src/components/app-rail.tsx`（新增，從 `Dashboard.tsx` 抽出共用導覽列）、`frontend/src/pages/Vocabulary.tsx`（新增）、`frontend/src/pages/Dashboard.tsx`（改用 `AppRail`）、`frontend/src/App.tsx`／`frontend/src/main.tsx`（掛路由器）、`frontend/src/lib/api.ts`（新增 `apiPost`）、`frontend/src/lib/dashboard-api.ts`（新增 `createVocabulary`／`VocabularyCreate`）。
- 既有模式：後端 `POST /api/v1/vocabulary`、`GET /api/v1/vocabulary`、`GET /api/v1/media-logs` 皆已存在且有既有測試覆蓋（Epic 1 建立），本卡純粹是前端串接既有 API，不需要新增或修改任何後端程式碼。
- 假設：
  - 不用路由函式庫（React Router 等）：此環境無 Node.js 無法驗證新套件真的能裝好建置成功，改用瀏覽器原生 History API（`pushState`/`popstate`）手刻最小路由，只有兩條路徑（`/`、`/vocabulary`），足夠應付目前規模，之後路由變複雜再評估換函式庫。
  - 範圍依 Niko 確認：只做列表＋新增，不含編輯、刪除、自動查字典/翻譯、CSV 匯入匯出（這些留給後續 User Story，見 `tools/kanban/epics.json`）。
  - 新增表單不含 `example_sentence`／`ipa` 欄位（這兩個屬於「自動查字典/翻譯/例句對齊」功能的填入對象，不在本卡範圍）。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/`。
- 不得觸碰：`backend/`。

## 需求

- 導入最小路由器：`/` 對應 Dashboard、`/vocabulary` 對應單字庫頁面，支援瀏覽器上一頁/下一頁與網址列直接輸入。
- 把 Dashboard 與單字庫頁面共用的 icon rail 導覽抽成 `AppRail` 元件，「單字庫」項目改為真正導覽（不再是「尚未實作」toast），「追劇紀錄」維持 toast 佔位（該頁面還不存在）。
- 單字庫頁面：唯讀表格列出目前語言的單字（單字／詞性／翻譯／冠詞／建立時間），「新增單字」按鈕開啟 Dialog 表單。
- 新增表單欄位：單字（必填）、詞性（下拉）、冠詞（僅德文語言視角顯示）、翻譯（選填）、來源劇集（選填，下拉列出目前語言的追劇紀錄，無資料時停用並顯示「尚無追劇紀錄」）、備註（選填）。
- 新增成功：關閉 Dialog、清空表單、表格重新整理、toast 顯示成功訊息。
- 新增失敗（後端 422/500）：Dialog 保持開啟、欄位內容保留、toast 顯示錯誤訊息。
- 涵蓋 screen-spec 列出的狀態：預設／載入中／空狀態／錯誤／表單送出中（停用態）。

## 驗收標準

- 點 icon rail 的「單字庫」能切換到 `/vocabulary`，網址列會變、瀏覽器上一頁能切回 Dashboard。
- 資料庫該語言沒有任何單字時，顯示空狀態文案＋新增入口，不是空白或錯誤。
- 新增一筆單字成功後，表格立即顯示新資料，不需要手動重新整理頁面。
- 送出中按鈕顯示 loading 態（沿用 S4 `Button` 的 `loading` prop），欄位停用防止重複送出。
- 語言切換後，列表與新增表單的德文特化欄位（冠詞）跟著切換。

## 實作備註

- `router.tsx`：`RouterProvider` 用 `useState` 存目前路徑＋監聽 `popstate`；`navigate()` 呼叫 `window.history.pushState` 再更新 state。只支援 `/`／`/vocabulary` 兩條路徑，非路徑一律 normalize 回 `/`。
- `AppRail`：`NAV_ITEMS` 陣列驅動 Dashboard／單字庫兩個真實導覽項目，`aria-current="page"` 標示目前頁面；追劇紀錄維持獨立的 toast 按鈕（尚無對應路徑）。
- `Vocabulary.tsx` 的新增 Dialog 用**受控** `open`/`onOpenChange`（不用 `DialogTrigger`），因為需要從「頂部新增單字」按鈕與「空狀態新增單字」按鈕兩處都能開啟同一個 Dialog。
- 冠詞欄位只在 `language === 'de'` 時渲染並送出，避免違反後端 `validate_language_specific_fields`（英文單字不可帶 `de_artikel`）。
- `apiPost<T>(path, body)`：`api.ts` 新增的第二個方法，`POST` + JSON body，複用既有的錯誤處理邏輯（`ApiError`）。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架）。
- 整合測試：不適用（呼叫的既有後端端點已有 Epic 1 的 pytest 覆蓋）。
- E2E 測試：不適用。
- 型別檢查：待人工在本機執行 `npm run build` 確認；此執行環境無 Node.js，未能跑。
- Lint：待人工在本機執行 `npm run lint` 確認；此執行環境無 Node.js，未能跑。
- Build：待人工在本機執行 `npm run build` 確認；此執行環境無 Node.js，未能跑。
- 螢幕截圖：待人工本機執行 `npm run dev`（需同時起後端）驗證後提供；此環境無瀏覽器/螢幕截圖工具，未能產出。
- 安全性檢查：不適用（呼叫既有後端 API，無新輸入處理邏輯；表單資料只送往本機後端）。

## 完成證據

- 變更的檔案：
  - `frontend/src/lib/router.tsx`（新增）
  - `frontend/src/components/app-rail.tsx`（新增）
  - `frontend/src/pages/Vocabulary.tsx`（新增）
  - `frontend/src/pages/Dashboard.tsx`（改用 `AppRail`，移除內嵌的 rail 標記與 `goToComingSoon`）
  - `frontend/src/App.tsx`（依路徑渲染 `Dashboard` 或 `Vocabulary`）
  - `frontend/src/main.tsx`（掛上 `RouterProvider`）
  - `frontend/src/lib/api.ts`（新增 `apiPost`）
  - `frontend/src/lib/dashboard-api.ts`（新增 `createVocabulary`／`VocabularyCreate`）
- 執行過的指令：無（此環境無 Node.js，見上方驗證契約）。
- 測試輸出：不適用，待人工本機驗證。
- 螢幕截圖：不適用，待人工本機執行後補上。
- 已知限制：
  1. 此執行環境沒有 Node.js，程式碼正確性僅靠審查與比對既有元件慣例把關。
  2. 路由器是手刻最小實作，不支援巢狀路由、路由參數、程式碼分割等進階功能；等頁面數量或複雜度成長再評估換成 React Router 之類的函式庫。
  3. 不含編輯／刪除／自動查字典翻譯／CSV 匯入匯出，這些後端 API 都已存在，純粹是本輪範圍刻意排除。
- 後續任務：Niko 本機驗證後回填人工核准；下一個候選 User Story 是「單字庫編輯/刪除」或「複習流程頁面」。
