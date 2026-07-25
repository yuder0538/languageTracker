# AI-Ready 任務卡

## Metadata

- 任務：TASK-031 單字庫自動查字典/翻譯
- 上層規格：延伸 `ai/artifacts/本地 Web UI/screen-spec-vocabulary.md`（同一個畫面新增一個動作，非新畫面，未另立 screen-spec）
- 上層 Epic：本地 Web UI
- 上層 User Story：單字自動查字典/翻譯
- 分軌：前端（後端 API 已存在，見情境包）
- 前置任務（dependsOn）：TASK-030
- 狀態：verify（等待人工本機驗證）
- 風險等級：低
- Agent owner：claude
- 人工核准者：（待 Niko 本機驗證後追加簽核）

## 目標

在單字庫列表每一列加一個「自動查詢」動作：英文單字回填音標／英文解釋，德文單字回填中文翻譯，讓使用者不用自己動手查意思。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/Vocabulary.tsx`、`frontend/src/lib/dashboard-api.ts`（新增 `enrichEnDictionary`／`enrichDeTranslation`）。
- 既有模式：後端 `POST /vocabulary/{id}/enrich/en-dictionary`（呼叫 Free Dictionary API，回填 `ipa`／`en_definition`）與 `POST /vocabulary/{id}/enrich/de-translation`（呼叫 MyMemory 翻譯 API，回填 `translation_zh`）皆是 Epic 2 已完成、已測試的既有端點，本卡純粹前端串接，不動後端。
- 假設：這是對既有「單字庫」畫面的小幅擴充（加一個動作、兩個新欄位顯示），不是新畫面、不涉及版面版型的抉擇，因此不另外走完整的 2-3 變體 mockup 比較流程（唯一合理做法是「每列一個小動作按鈕」，沒有真正的版型分歧可比較），僅在此任務卡記錄設計決策。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/`。
- 不得觸碰：`backend/`。

## 需求

- 表格新增「自動查詢」欄，每列一個圖示按鈕（放大鏡；查詢中顯示 spinner 並停用）。
- 點擊依目前語言視角呼叫對應端點；成功後：toast 顯示成功、該列資料重新整理顯示新回填的內容。
- 失敗（字典查無此字 / 外部服務暫時無法連線）：toast 顯示後端回傳的錯誤訊息，不影響其他列。
- 英文單字：音標顯示在單字旁邊（`/aɪ/` 形式的小字）；解釋（`en_definition`）過長時用 `title` 提示（hover 顯示），避免撐爆表格欄寬。
- 德文單字：翻譯結果直接顯示在既有的「翻譯」欄。

## 驗收標準

- 點擊查詢按鈕後，按鈕立即顯示 loading 態、停用，避免重複點擊。
- 查詢成功後不需要手動整頁重新整理就能看到新資料。
- 英文單字查詢成功後，單字旁邊出現音標。
- 德文單字查詢成功後，翻譯欄出現中文翻譯。
- 查無此字或外部服務錯誤時，清楚的錯誤訊息（不是籠統的「發生錯誤」）。

## 實作備註

- 用 `Set<number>` (`enrichingIds`) 追蹤目前正在查詢中的單字 id，多列可以同時查詢互不干擾。
- 圖示按鈕沒有用 `Button` 的 `loading` prop（該 prop 會在 spinner 之外「額外」渲染 children，兩個 icon 疊在一起在小尺寸的 icon 按鈕上會顯示錯誤），改為自己依 `isEnriching` 條件渲染 `Loader2Icon` 或 `SearchIcon` 兩者擇一，並用 `disabled` 手動控制。
- 查詢成功後呼叫既有 `vocabulary.retry()` 重新整理整份清單（會讓表格短暫回到 loading skeleton 再顯示新資料），沒有做「只更新這一列」的局部更新——對本機小型資料集來說幾乎感覺不到延遲，換取實作簡單、不需要額外的樂觀更新/合併邏輯。
- 翻譯欄用 `truncate` + `title` 屬性避免長解釋撐爆表格，這也是 dataviz skill／design-craft 慣用的「資料太長就用 tooltip 承接」處理方式。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架）。
- 整合測試：不適用（呼叫的既有後端端點已有 Epic 2 的 pytest 覆蓋）。
- E2E 測試：不適用。
- 型別檢查：待人工在本機執行 `npm run build` 確認；此執行環境無 Node.js，未能跑。
- Lint：待人工在本機執行 `npm run lint` 確認；此執行環境無 Node.js，未能跑。
- Build：待人工在本機執行 `npm run build` 確認；此執行環境無 Node.js，未能跑。
- 螢幕截圖：待人工本機驗證後提供；此環境無瀏覽器/螢幕截圖工具，未能產出。
- 安全性檢查：不適用（呼叫既有後端 API，後端本身已對外部字典/翻譯 API 呼叫做過錯誤處理）。

## 完成證據

- 變更的檔案：
  - `frontend/src/pages/Vocabulary.tsx`（新增自動查詢欄與互動邏輯）
  - `frontend/src/lib/dashboard-api.ts`（新增 `enrichEnDictionary`／`enrichDeTranslation`）
  - `tools/kanban/epics.json`（新增「單字自動查字典/翻譯」User Story）
- 執行過的指令：無（此環境無 Node.js，見上方驗證契約）。
- 測試輸出：不適用，待人工本機驗證。
- 螢幕截圖：不適用，待人工本機執行後補上。
- 已知限制：
  1. 此執行環境沒有 Node.js，程式碼正確性僅靠審查與比對既有元件慣例把關。
  2. 查詢成功後整份清單重新整理（非局部更新單一列），本機小型資料集下延遲不明顯，資料量變大後可考慮改為只更新該列。
  3. 英文單字若 Free Dictionary API 查無資料（外語詞、罕見字、拼字錯誤），會顯示 502 錯誤，使用者需要自行修正拼字後重試；沒有做「模糊比對建議」之類的體驗優化。
- 後續任務：Niko 本機驗證後回填人工核准；下一個候選 User Story 是「單字庫編輯/刪除」或「複習流程頁面」。
