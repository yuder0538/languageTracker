# AI-Ready 任務卡

## Metadata

- 任務：TASK-037 德文冠詞填空複習模式
- 上層規格：`ai/artifacts/本地 Web UI/screen-spec-review.md`「冠詞複習模式」章節（延伸既有複習畫面規格，非新畫面規格）
- 上層 Epic：本地 Web UI
- 上層 User Story：德文冠詞填空複習模式
- 分軌：前端（後端 API 已存在，見情境包）
- 前置任務（dependsOn）：TASK-034
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko（2026-07-25，本機驗證通過）

## 目標

複習頁面新增第二種模式：德文冠詞猜測（der/die/das），系統自動判對錯並更新排程，不用像標準模式一樣自己評分難易度。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/ReviewArtikel.tsx`（新增）、`frontend/src/components/review-mode-switch.tsx`（新增，兩個模式共用的切換元件）、`frontend/src/pages/Review.tsx`（加上模式切換）、`frontend/src/pages/Dashboard.tsx`（`FocusCard` 新增德文限定的次要入口連結）、`frontend/src/lib/router.tsx`（新增 `/review/artikel` 路徑）、`frontend/src/App.tsx`、`frontend/src/lib/dashboard-api.ts`（`fetchReviewQueue` 新增 `cardType` 參數、新增 `submitArtikelQuiz`／`ArtikelQuizResult`）。
- 既有模式：後端 `GET /reviews/queue?card_type=artikel`（只回傳已標注 `de_artikel` 的名詞）與 `POST /vocabulary/{id}/review/artikel-quiz`（自動判斷對錯、內部呼叫既有 SRS 排程邏輯）皆是 Epic 3 已完成、已測試的既有端點，本卡純前端串接，不動後端。
- 假設：這是德文限定功能（英文沒有冠詞，後端會直接 422 拒絕 `language=en&card_type=artikel` 的組合），因此：(1) 模式切換元件只在德文視角顯示；(2) 若使用者透過瀏覽器操作在英文視角下進到 `/review/artikel`，前端自動把語言切回德文而非讓後端噴 422 或顯示打不開的空頁面。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/`。
- 不得觸碰：`backend/`。

## 需求

- 新路徑 `/review/artikel`：卡片只顯示名詞本體（去掉 headword 開頭的冠詞文字），3 個按鈕（der/die/das，也可按數字鍵 1/2/3）。
- 選擇後立即送出、系統自動判對錯，畫面顯示回饋（答對/答錯＋正確答案），使用者按「下一張」（或空白鍵/Enter）才前進，不做無提示的自動跳轉。
- 標準複習頁與冠詞複習頁的頂部都新增一個小型模式切換（僅德文顯示），可以互相切換不用先離開再重進。
- Dashboard 的複習 CTA 卡片在德文視角下新增次要連結，作為額外入口。
- 佇列為空、載入中、讀取失敗、送出失敗、全部複習完，皆比照標準模式處理對應狀態。

## 驗收標準

- 德文視角下，Dashboard 出現「或練習德文冠詞」連結，點擊進到冠詞複習頁。
- 卡片上看不到冠詞（例如 headword 是「der Tisch」，畫面只顯示「Tisch」）。
- 選對/選錯都有清楚的視覺回饋（顏色＋文字），選錯時會標出正確答案。
- 兩個複習模式的切換元件可以互相導覽，且只在德文視角出現（英文視角完全看不到）。
- 用瀏覽器網址列直接輸入 `/review/artikel` 且目前語言是英文時，畫面會自動切回德文並正常顯示，不會卡住或報錯。

## 實作備註

- `stripArtikel(headword)` 用正則 `/^(der|die|das)\s+/i` 去掉開頭冠詞；假設 headword 的命名慣例是「冠詞 + 空格 + 名詞」（沿用專案至今新增德文名詞的既有慣例，例如「der Tisch」「die Freiheit」），若未來有 headword 不遵循這個慣例，這個名詞的冠詞複習卡片會直接顯示完整 headword（不會壞掉，只是可能露出冠詞，體驗打折但不影響功能）。
- `fetchReviewQueue` 加了第二個可選參數 `cardType`（預設 `"standard"`），既有呼叫端（`Dashboard.tsx`、`Review.tsx`）不用改就自動維持原本行為。
- `ReviewModeSwitch` 抽成獨立元件（`components/`），因為兩個複習頁面都要用同一份 UI，避免重複程式碼；只接受 `mode: "standard" | "artikel"` 決定哪一個按鈕反白。
- 語言防呆用 `useEffect` 監看 `language !== "de"` 就自動 `setLanguage("de")`；因為這個頁面本身沒有 `AppRail`（跟標準複習頁一樣走全螢幕專注模式，沒有側邊欄可以讓使用者自己切語言），不做防呆的話會卡在一個看不懂為什麼是空的或錯誤的頁面。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架）。
- 整合測試：不適用（呼叫的既有後端端點已有 Epic 3 的 pytest 覆蓋）。
- E2E 測試：不適用。
- 型別檢查：Niko 本機執行 `npm run build` 通過，無型別錯誤。
- Lint：Niko 本機執行 `npm run lint` 通過。
- Build：Niko 本機執行 `npm run build` 通過。
- 螢幕截圖：不適用，Niko 以實機操作（點擊/鍵盤操作）驗證功能，未另外提供截圖。
- 安全性檢查：不適用（呼叫既有後端 API，無新輸入處理邏輯）。

## 完成證據

- 變更的檔案：
  - `frontend/src/lib/router.tsx`（新增 `/review/artikel` 路徑）
  - `frontend/src/components/review-mode-switch.tsx`（新增）
  - `frontend/src/pages/ReviewArtikel.tsx`（新增）
  - `frontend/src/pages/Review.tsx`（加上模式切換元件）
  - `frontend/src/pages/Dashboard.tsx`（`FocusCard` 新增德文限定次要入口）
  - `frontend/src/App.tsx`（依路徑渲染 `ReviewArtikel`）
  - `frontend/src/lib/dashboard-api.ts`（`fetchReviewQueue` 新增 `cardType` 參數、新增 `submitArtikelQuiz`／`ArtikelQuizResult`／`ReviewCardType`）
  - `ai/artifacts/本地 Web UI/screen-spec-review.md`（新增「冠詞複習模式」章節）
- 執行過的指令：Niko 本機執行 `npm run build`、`npm run lint`（皆通過），並實機操作冠詞複習流程（含答對/答錯回饋、模式切換）。
- 測試輸出：Niko 回報「冠詞練習都成功順利」「build lint 都沒問題」。
- 螢幕截圖：不適用，Niko 以實機操作驗證。
- 已知限制：
  1. `stripArtikel` 依賴 headword 命名慣例（見實作備註），非結構化解析。
  2. 送出中沒有針對「選了答案但網路很慢」做額外的 loading 骨架，只是按鈕本身停用（`submitting` 狀態），跟標準模式的評分按鈕一致。
- 後續任務：無。
