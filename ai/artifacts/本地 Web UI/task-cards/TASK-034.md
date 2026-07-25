# AI-Ready 任務卡

## Metadata

- 任務：TASK-034 複習流程頁面
- 上層規格：`ai/artifacts/本地 Web UI/screen-spec-review.md`、`ai/artifacts/本地 Web UI/mockup-decision-review.md`（選定變體 B — 上下展開式）
- 上層 Epic：本地 Web UI
- 上層 User Story：Dashboard 頁面實作（複習流程是 Dashboard「開始複習」CTA 的落地，沿用同一個 User Story，不另立）
- 分軌：前端（後端 API 已存在，見情境包）
- 前置任務（dependsOn）：TASK-029
- 狀態：verify（等待人工本機驗證）
- 風險等級：低
- Agent owner：claude
- 人工核准者：（待 Niko 本機驗證後追加簽核）

## 目標

讓 Dashboard 上「開始複習」／「繼續複習」按鈕真正可用：一次顯示一張待複習卡片，使用者評分後自動進到下一張，全部複習完回 Dashboard。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/Review.tsx`（新增）、`frontend/src/lib/router.tsx`（新增 `/review` 路徑）、`frontend/src/App.tsx`（依路徑渲染三個頁面之一）、`frontend/src/pages/Dashboard.tsx`（CTA 改為導覽而非 toast 佔位）、`frontend/src/lib/dashboard-api.ts`（新增 `submitReview`／`ReviewGrade`）。
- 既有模式：後端 `GET /reviews/queue`（Dashboard 已在用）與 `POST /vocabulary/{id}/review`（Epic 3 已完成、已測試）皆是既有端點，本卡純前端串接，不動後端。
- 假設：
  - 複習佇列在頁面載入時抓一次，之後在同一個 session 內用本地 index 往前走，不重新呼叫 API（也就是複習中途不會因為某張卡評成「忘記」就把它重新插回佇列，同一個 session 只會看到起始那批卡片各一次）——這是為了讓「進度／共幾張」這個數字穩定不跳動，符合使用者描述的「點完自動跳下一張」直覺；日後若要支援「答錯的卡片同一個 session 內重考」，屬於獨立的行為變更，留待有需要再做。
  - 複習頁面**不含**側邊 icon rail（screen-spec 決議：全螢幕專注模式，複習時不該分心點去別頁），只有左上角「離開」按鈕。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/`。
- 不得觸碰：`backend/`。

## 需求

- 頂部：離開按鈕、進度列（第幾張／共幾張）、連續複習天數。
- 卡片：先顯示題目（單字＋詞性/冠詞），按「顯示答案」（或空白鍵）後在同一張卡片下方展開答案（翻譯），單字保留在原位不消失（變體 B 決議）。
- 顯示答案後出現 4 個評分按鈕（忘記/困難/一般/容易），可滑鼠點擊或按數字鍵 1/2/3/4。
- 評分送出中按鈕停用，避免重複送出；送出失敗顯示錯誤訊息，停留原卡片可重新評分。
- 佇列全部複習完顯示完成畫面；佇列本來就是空的顯示對應空狀態；兩者都提供回 Dashboard 的按鈕。

## 驗收標準

- 從 Dashboard 點「開始複習」／「繼續複習」，網址切到 `/review`，顯示第一張卡片。
- 顯示答案後，原本的單字仍然看得到（不是被答案取代或蓋掉）。
- 評分一張後自動換下一張，進度數字（例如 3/18）跟著更新。
- 全部評完後看到完成畫面，點按鈕能回到 Dashboard，且 Dashboard 的複習佇列數字會反映剛才複習的結果（重新整理後）。
- 鍵盤操作（空白鍵顯示答案、數字鍵 1-4 評分）跟滑鼠點擊效果一致。

## 實作備註

- `router.tsx` 的 `AppRoute` 型別新增 `"/review"`，`normalize()` 改用 `KNOWN_ROUTES` 陣列判斷（原本硬寫兩個字串比對，三條路徑後改用陣列查找比較不會漏改）。
- `Review.tsx` 用本地 `index`／`revealed`／`submitting` 三個 state 管理複習進度；語言切換時用 `useEffect` 重設 `index`/`revealed`（避免切換語言後卡在舊佇列的某個 index，讀取超出新佇列長度）。
- 鍵盤事件監聽器的 `useEffect` 依 `[current, revealed, submitting]` 重新訂閱（不含 `handleGrade` 本身），確保每次重新訂閱時抓到的都是當下最新的卡片與狀態，這是刻意的權衡而非疏漏（詳見程式碼註解）。
- 4 個評分按鈕語意色沿用 screen-spec 決議：`text-destructive`（忘記）／`text-warning`（困難）／`text-info-500`（一般，S3 token 沒有註冊 semantic 的 `--color-info` slot，改用 raw scale 的 `info-500`）／`text-success`（容易），難度遞增對應「危險→成功」色相，符合直覺。
- Dashboard 的 `FocusCard` 新增 `onStartReview` prop，取代原本寫死的 `toast.info("複習頁面尚未實作")`；`Dashboard.tsx` 移除了不再使用的 `toast` import（避免 `noUnusedLocals` 建置錯誤）。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架）。
- 整合測試：不適用（呼叫的既有後端端點已有 Epic 3 的 pytest 覆蓋）。
- E2E 測試：不適用。
- 型別檢查：待人工在本機執行 `npm run build` 確認；此執行環境無 Node.js，未能跑。
- Lint：待人工在本機執行 `npm run lint` 確認；此執行環境無 Node.js，未能跑。
- Build：待人工在本機執行 `npm run build` 確認；此執行環境無 Node.js，未能跑。
- 螢幕截圖：待人工本機驗證後提供；此環境無瀏覽器/螢幕截圖工具，未能產出。
- 安全性檢查：不適用（呼叫既有後端 API，無新輸入處理邏輯）。

## 完成證據

- 變更的檔案：
  - `frontend/src/lib/router.tsx`（新增 `/review` 路徑）
  - `frontend/src/pages/Review.tsx`（新增，複習頁面）
  - `frontend/src/App.tsx`（依路徑渲染 Dashboard/Vocabulary/Review）
  - `frontend/src/pages/Dashboard.tsx`（CTA 改為導覽到 `/review`，移除未使用的 `toast` import）
  - `frontend/src/lib/dashboard-api.ts`（新增 `submitReview`／`ReviewGrade`）
- 執行過的指令：無（此環境無 Node.js，見上方驗證契約）。
- 測試輸出：不適用，待人工本機驗證。
- 螢幕截圖：不適用，待人工本機執行後補上。
- 已知限制：
  1. 此執行環境沒有 Node.js，程式碼正確性僅靠審查把關。
  2. 同一個複習 session 內，答錯（忘記）的卡片不會重新排進本次佇列讓你馬上重考，要等下次開複習（或後端排程判定又到期）才會再出現。這是刻意的範圍限縮（見情境包假設），非 bug。
  3. 沒有德文冠詞填空模式（`card_type=artikel`，後端已支援但前端未串接），只做標準複習模式。
- 後續任務：Niko 本機驗證後回填人工核准；下一個候選是「德文冠詞填空複習模式」或「單字刪除」。
