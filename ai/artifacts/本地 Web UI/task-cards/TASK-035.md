# AI-Ready 任務卡

## Metadata

- 任務：TASK-035 單字刪除功能
- 上層規格：延伸 `ai/artifacts/本地 Web UI/screen-spec-vocabulary.md`（同一畫面補上最後一個 CRUD 動作，非新畫面）
- 上層 Epic：本地 Web UI
- 上層 User Story：單字庫管理頁面
- 分軌：前端（後端 `DELETE /vocabulary/{id}` 已存在，見情境包）
- 前置任務（dependsOn）：TASK-033
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-25（本機測試刪除流程成功，`npm run build`／`npm run lint` 皆通過）

## 目標

補齊單字庫最後一個 CRUD 動作：刪除單字，含確認對話框避免手滑誤刪。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/Vocabulary.tsx`（新增 `DeleteConfirmDialog`）、`frontend/src/lib/api.ts`（新增 `apiDelete`）、`frontend/src/lib/dashboard-api.ts`（新增 `deleteVocabulary`）。
- 既有模式：後端 `DELETE /vocabulary/{vocabulary_id}` 是 Epic 1 已完成、已測試的既有端點（回傳 204 No Content），本卡純前端串接，不動後端。
- 假設：刪除是高風險、不可逆動作，一律要求二次確認（Dialog 彈窗，「確定刪除」用 `destructive` 樣式），不做「直接點刪除圖示就刪掉」的設計。
- 未知事項：無。
- 允許變更的檔案：`frontend/src/`。
- 不得觸碰：`backend/`。

## 需求

- 表格「操作」欄新增垃圾桶圖示（紅色，與編輯/自動查詢圖示並排）。
- 點擊彈出確認對話框，顯示「確定要刪除『{headword}』？」與不可復原提示。
- 確認後才真正呼叫 `DELETE`；取消或關閉對話框不做任何事。
- 刪除成功：對話框關閉、表格移除該筆、toast 顯示成功訊息。
- 刪除失敗：對話框保持開啟，toast 顯示錯誤訊息，可重試。

## 驗收標準

- 點垃圾桶圖示，先看到確認對話框，不會直接刪除。
- 點「取消」，資料不受影響。
- 點「確定刪除」，該筆單字從列表消失，不需要手動重新整理頁面。
- 送出中按鈕顯示 loading 態，避免重複點擊。

## 實作備註

- `DeleteConfirmDialog` 用受控 `word: VocabularyRead | null` 決定開關（`null` = 關閉），跟 `WordDialog` 的 `editingWord` 是同一種模式，維持這個檔案內的一致性。
- `apiDelete<T>(path)`：`api.ts` 新增的第三個方法（繼 `apiGet`/`apiPost`/`apiPatch` 之後），對應 204 回應（既有的 `request()` 已處理 204 回傳 `undefined`，不需要額外改動）。
- 確定刪除按鈕用既有 `Button` 的 `variant="destructive"` 樣式，符合「危險動作用危險色」的既有慣例（沿用複習頁面評分按鈕、Dashboard mockup 刪除示範等既有用法）。

## 驗證契約

- 單元測試：不適用（此階段前端無測試框架）。
- 整合測試：不適用（呼叫的既有後端端點已有 Epic 1 的 pytest 覆蓋）。
- E2E 測試：不適用。
- 型別檢查：Niko 本機執行 `npm run build` 確認通過。第一次執行發現一個跟本卡無關的既有型別錯誤（`Select` 的 `onValueChange` 型別，見 TASK-036 完成證據的修正說明，同一次修正涵蓋本頁面用到的 `Select`），修正後通過。
- Lint：Niko 本機執行 `npm run lint` 確認通過，無錯誤。
- Build：Niko 本機執行 `npm run build` 確認通過。
- 螢幕截圖：未產出圖檔，Niko 目視確認刪除流程：點垃圾桶圖示先彈確認框、確定刪除後該筆從列表消失。
- 安全性檢查：不適用（呼叫既有後端 API，且有二次確認防呆）。

## 完成證據

- 變更的檔案：
  - `frontend/src/lib/api.ts`（新增 `apiDelete`）
  - `frontend/src/lib/dashboard-api.ts`（新增 `deleteVocabulary`）
  - `frontend/src/pages/Vocabulary.tsx`（新增 `DeleteConfirmDialog`、表格新增刪除圖示）
- 執行過的指令：Agent 端無（此環境無 Node.js）；Niko 本機執行 `npm run build`、`npm run lint`，皆通過；本機手動測試刪除流程。
- 測試輸出：無自動化測試，以本機建置/lint 通過 + 人工手動操作驗證為準。
- 螢幕截圖：不適用，待人工本機執行後補上。
- 已知限制：此執行環境沒有 Node.js，程式碼正確性僅靠審查把關。
- 後續任務：無（追劇紀錄管理頁面見 TASK-036）。
