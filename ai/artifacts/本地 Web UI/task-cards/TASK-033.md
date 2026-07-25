# AI-Ready 任務卡

## Metadata

- 任務：TASK-033 單字編輯功能
- 上層規格：延伸 `ai/artifacts/本地 Web UI/screen-spec-vocabulary.md`（同一畫面新增編輯能力，非新畫面）
- 上層 Epic：本地 Web UI
- 上層 User Story：單字庫管理頁面（原本明確排除編輯，本卡補上；見下方情境包）
- 分軌：前端（後端 `PATCH /vocabulary/{id}` 已存在，見情境包）
- 前置任務（dependsOn）：TASK-030
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-25（本機把「das Fenster」的翻譯從「此」改成「窗戶」，確認編輯功能正常，`npm run build`／`npm run lint` 皆通過）

## 目標

讓使用者能修正單字資料——直接動機：Niko 實測自動翻譯（TASK-031）把「das Fenster」翻成「此」（MyMemory 翻譯 API 的已知品質問題，見任務卡「實作備註」），但沒有編輯功能就沒辦法修正錯誤資料，只能將就。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/Vocabulary.tsx`（把 `AddWordDialog` 重構成通用的 `WordDialog`，同時支援新增／編輯兩種模式）、`frontend/src/lib/api.ts`（新增 `apiPatch`）、`frontend/src/lib/dashboard-api.ts`（新增 `updateVocabulary`／`VocabularyUpdate`）。
- 既有模式：後端 `PATCH /vocabulary/{id}` 是 Epic 1 已完成、已測試的既有端點（`exclude_unset` 局部更新，語言不可變更），本卡純前端串接，不動後端。
- 假設：編輯表單欄位跟新增表單完全一樣（單字／詞性／冠詞／翻譯／來源劇集／備註），不編輯 `ipa`／`en_definition`／`example_sentence`——這些欄位保留給「自動查詢」（TASK-031）填入，維持職責分工清楚（自動查詢負責音標/解釋/翻譯的「首次填入」，編輯負責「手動修正」，兩者互補不重疊）。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/`。
- 不得觸碰：`backend/`。

## 需求

- 表格每列「操作」欄新增一個鉛筆圖示（編輯），跟既有的「自動查詢」放大鏡圖示並排。
- 點編輯開啟跟「新增單字」同一個 Dialog，但標題變「編輯單字」、欄位預先帶入該單字目前的資料、送出按鈕變「儲存」，呼叫 `PATCH` 而非 `POST`。
- 儲存成功：Dialog 關閉、表格重新整理顯示新資料、toast 顯示成功訊息。
- 儲存失敗：Dialog 保持開啟、欄位內容保留、toast 顯示錯誤訊息。

## 驗收標準

- 點編輯圖示，Dialog 彈出時所有欄位都已經是該單字目前的值（不是空白表單）。
- 修改翻譯欄位、按儲存，表格裡的翻譯立即更新成新值。
- 不小心點到編輯又想放棄：點「取消」或按 ESC，資料不會被改動。
- 新增流程（原本 TASK-030 的功能）維持正常，沒有因為這次重構而壞掉。

## 實作備註

- 把 `AddWordDialog` 重構成 `WordDialog`，用 `editingWord: VocabularyRead | null` 這個 prop 判斷模式（`null` = 新增，非 `null` = 編輯），避免維護兩份幾乎一樣的表單程式碼（新增/編輯的欄位、驗證邏輯、UI 排版完全共用，只有標題文字、送出時呼叫的 API、按鈕文字不同）。
- 用 `useEffect` 依 `[open, editingWord]` 在每次 Dialog 開啟時重設表單：`editingWord` 有值就帶入該單字資料，沒有就清空——這樣不需要在「送出成功」與「取消」兩個不同的地方各自處理重設表單的邏輯，開啟時機一到就自動處理好。
- 父層元件（`Vocabulary`）用 `openCreateDialog()`／`openEditDialog(word)` 兩個小函式分別設定 `editingWord` 再開啟 Dialog，取代原本直接 `setDialogOpen(true)`。
- MyMemory 翻譯 API 品質問題：它是「翻譯記憶庫」（比對已翻譯過的句子片段），不是真正的機器翻譯引擎，查單一詞組（尤其德文→中文這種語言對）容易比對到不相關的片段。這是既有服務（Epic 2）的已知限制，不在本卡範圍內修正，但編輯功能提供了修正管道。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架）。
- 整合測試：不適用（呼叫的既有後端端點已有 Epic 1 的 pytest 覆蓋）。
- E2E 測試：不適用。
- 型別檢查：Niko 本機執行 `npm run build` 確認通過，無錯誤。
- Lint：Niko 本機執行 `npm run lint` 確認通過，無錯誤。
- Build：Niko 本機執行 `npm run build` 確認通過。
- 螢幕截圖：未產出圖檔，Niko 目視確認編輯「das Fenster」翻譯欄成功從「此」改成「窗戶」，表格立即更新。
- 安全性檢查：不適用（呼叫既有後端 API，無新輸入處理邏輯）。

## 完成證據

- 變更的檔案：
  - `frontend/src/lib/api.ts`（新增 `apiPatch`）
  - `frontend/src/lib/dashboard-api.ts`（新增 `updateVocabulary`／`VocabularyUpdate`）
  - `frontend/src/pages/Vocabulary.tsx`（`AddWordDialog` 重構為 `WordDialog`，支援新增/編輯兩種模式；表格新增編輯圖示）
- 執行過的指令：Agent 端無（此環境無 Node.js）；Niko 本機執行 `npm run build`、`npm run lint`，皆通過；本機手動測試編輯流程。
- 測試輸出：無自動化測試，以本機建置/lint 通過 + 人工手動操作驗證為準。
- 螢幕截圖：不適用，待人工本機執行後補上。
- 已知限制：
  1. 此執行環境沒有 Node.js，程式碼正確性僅靠審查把關。
  2. 不能編輯 `ipa`／`en_definition`／`example_sentence`（刻意排除，見情境包假設）；若使用者想手動修正這幾個欄位，目前還是只能透過 API 文件。
  3. 不支援刪除單字（仍是刻意排除的範圍，留給後續 User Story）。
- 後續任務：下一個候選是「單字刪除」或「複習流程頁面」。
