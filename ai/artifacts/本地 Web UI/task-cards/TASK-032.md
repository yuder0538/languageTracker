# AI-Ready 任務卡

## Metadata

- 任務：TASK-032 單字發音朗讀（瀏覽器 TTS）
- 上層規格：延伸 `ai/artifacts/本地 Web UI/screen-spec-vocabulary.md`（同一畫面新增一個小動作，非新畫面）
- 上層 Epic：本地 Web UI
- 上層 User Story：單字自動查字典/翻譯（沿用同一個 User Story，跟自動查詢是同一批「幫使用者省力」的小功能）
- 分軌：前端（純瀏覽器功能，不需要後端）
- 前置任務（dependsOn）：TASK-031
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：Niko / 2026-07-25（本機點擊喇叭圖示確認有聲音、朗讀正常，`npm run build`／`npm run lint` 皆通過）

## 目標

單字庫列表每個單字旁加一個喇叭圖示，點下去用瀏覽器內建語音朗讀單字，讓使用者不用自己想發音。

## 情境包（Context Pack）

- 相關檔案：`frontend/src/pages/Vocabulary.tsx`。
- 既有模式：瀏覽器原生 [Web Speech API](https://developer.mozilla.org/docs/Web/API/SpeechSynthesis)（`speechSynthesis.speak()`），不需要任何後端支援、不需要新增 npm 套件、不需要外部 API 金鑰。
- 假設：機器合成語音，不是真人錄音字典發音；Niko 明確選了這個方案而非「串接字典真人發音」，因為兩個語言都能用、不用等外部服務、實作最快，真人發音留待未來有需要再做。
- 未知事項：不同瀏覽器/作業系統內建的語音品質不一（依系統安裝的語音引擎而定），這不是程式碼能控制的範圍。
- 允許變更的檔案：`frontend/src/pages/Vocabulary.tsx`。
- 不得觸碰：`backend/`。

## 需求

- 每個單字旁一個喇叭圖示，點擊朗讀該單字。
- 依單字的語言（`word.language`）設定朗讀語音的語言代碼（`en-US`／`de-DE`），確保念的腔調對。
- 瀏覽器不支援語音朗讀時，顯示 toast 錯誤提示，不噴出無法理解的 JS 錯誤。
- 朗讀中給一個輕量的視覺提示（喇叭圖示變色），讓使用者知道有反應。

## 驗收標準

- 點德文單字的喇叭，念出來是德文腔調；點英文單字，是英文腔調。
- 連續點不同單字的喇叭，前一個發音會被打斷、播放新的（不會疊在一起同時念）。
- 圖示本身不擋到既有的自動查詢、單字文字排版。

## 實作備註

- `speak(text, language, onEnd)`：純函式，`SpeechSynthesisUtterance` 設定 `lang`，`onend`／`onerror` 都導回同一個 callback 讓呼叫端清掉「正在朗讀」的狀態（不用分開處理成功/失敗，朗讀本身沒有「失敗訊息」可顯示，播放結束或出錯的收尾動作一樣）。
- 每次朗讀前呼叫 `speechSynthesis.cancel()` 停掉前一個朗讀，避免使用者連續點擊時聲音疊在一起。
- 用 `speakingId`（單一 id，非 Set）追蹤目前朗讀中的單字——語音同一時間只會有一個在播，不像自動查詢可能多列同時進行中，不需要 Set。

## 驗證契約

- 單元測試：不適用（純瀏覽器 API 呼叫，此階段前端無測試框架）。
- 整合測試：不適用。
- E2E 測試：不適用。
- 型別檢查：Niko 本機執行 `npm run build` 確認通過，無錯誤。
- Lint：Niko 本機執行 `npm run lint` 確認通過，無錯誤。
- Build：Niko 本機執行 `npm run build` 確認通過。
- 螢幕截圖：不適用（聽覺功能）；Niko 本機點擊喇叭圖示確認真的有聲音、朗讀正常。
- 安全性檢查：不適用（純前端瀏覽器 API，無資料傳輸）。

## 完成證據

- 變更的檔案：
  - `frontend/src/pages/Vocabulary.tsx`（新增 `speak()` 函式與喇叭圖示）
- 執行過的指令：Agent 端無（此環境無 Node.js）；Niko 本機執行 `npm run build`、`npm run lint`，皆通過；本機實際點擊測試發音。
- 測試輸出：無自動化測試，以本機建置/lint 通過 + 人工實際聽測驗證為準。
- 螢幕截圖：不適用（聽覺功能）。
- 已知限制：
  1. 此執行環境沒有 Node.js，程式碼正確性僅靠審查把關。
  2. 機器合成語音，非真人字典發音；語音品質依使用者作業系統/瀏覽器內建語音引擎而定，程式碼無法控制。
  3. 若未來想換成真人字典發音，需要另外串接一個有發音檔的字典/翻譯服務（目前 English 用的 Free Dictionary API 常附發音檔連結，德文目前用的 MyMemory 翻譯 API 沒有此功能）。
- 後續任務：無。
