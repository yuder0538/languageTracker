# AI-Ready 任務卡

## Metadata

- 任務：TASK-038 修正德文翻譯回傳簡體字（改用繁體）
- 上層規格：無（既有服務的 bug 修正，非新功能）
- 上層 Epic：本地 Web UI
- 上層 User Story：單字自動查字典/翻譯
- 分軌：後端
- 前置任務（dependsOn）：TASK-031
- 狀態：完成
- 風險等級：低
- Agent owner：claude
- 人工核准者：（純後端 bug 修正，已用真實測試驗證，不需 UI 審查關卡）

## 目標

Niko 實測發現「自動查詢」翻出來的中文是簡體字（例如 laufen 之前被翻成「运行」），但這個專案的介面與使用者都是繁體中文，要修正成繁體輸出。

## 情境包（Context Pack）

- 相關檔案：`backend/app/services/de_translation.py`、`backend/tests/test_de_translation_service.py`。
- 既有模式：MyMemory 翻譯 API（`fetch_de_to_zh_translation`）沿用 Epic 2 建立的既有服務，本卡只改一個參數，不改函式簽章或呼叫端。
- 假設：MyMemory 的 `langpair` 參數裡單獨的 `zh` 語言代碼預設解析成簡體中文（`zh-CN`），這是 MyMemory 這個服務本身的行為，不是我們程式碼邏輯錯誤。
- 未知事項：無（已用真實 API 請求驗證，見完成證據）。
- 允許變更的檔案：`backend/app/services/de_translation.py`、`backend/tests/`。
- 不得觸碰：其他後端模組。

## 需求

- `langpair` 參數從 `"de|zh"` 改成 `"de|zh-TW"`，明確指定繁體中文。
- 更新既有測試斷言的 `params` 期望值。

## 驗收標準

- 對同一個德文單字（例如 laufen）發送翻譯請求，回傳繁體字（跑步）而非簡體字（跑步的簡體是「跑步」本身無差異，但像「运行」vs「運行」這種有繁簡差異的字就看得出來）。
- 既有測試全數通過，無新增失敗。

## 實作備註

- 這是單一參數修正，不涉及函式簽章或呼叫端（`app/api/vocabulary.py` 的 `enrich_de_translation` 端點完全不用改）。
- **已用真實 MyMemory API 請求驗證**（此執行環境有網路存取）：
  - `langpair=de|zh`（修正前）→ `laufen` 翻成「运行」，回應內的 `"target":"zh-CN"` 證實預設解析成簡體。
  - `langpair=de|zh-TW`（修正後）→ `laufen` 翻成「跑步」，回應內的 `"target":"zh-TW"` 證實正確解析成繁體。
  - 這不是憑空猜測的修法，是先發真實請求比對兩種語言代碼的實際回應後才確定的修法。

## 驗證契約

- 單元測試：`backend/tests/test_de_translation_service.py` 既有 5 個測試全數通過（其中一個更新了 `langpair` 期望值）。
- 整合測試：不適用（服務層測試已涵蓋）。
- E2E 測試：不適用。
- 型別檢查：不適用（Python 專案，ruff 涵蓋 lint）。
- Lint：`ruff check .` 已執行，全數通過。
- Build：不適用（Python，無 build 步驟）。
- 螢幕截圖：不適用（純 API 修正）。
- 安全性檢查：不適用（唯讀外部 API 呼叫參數調整，無新輸入處理）。

## 完成證據

- 變更的檔案：
  - `backend/app/services/de_translation.py`（`langpair` 改為 `de|zh-TW`）
  - `backend/tests/test_de_translation_service.py`（更新期望的 `params`）
- 執行過的指令：
  - `curl "https://api.mymemory.translated.net/get?q=laufen&langpair=de%7Czh-TW"` → 確認回傳繁體「跑步」，`target: zh-TW`
  - `curl "https://api.mymemory.translated.net/get?q=laufen&langpair=de%7Czh"` → 確認修正前回傳簡體「运行」，`target: zh-CN`
  - `pytest -q` → 185 passed（含本卡修改的測試）
  - `ruff check .` → All checks passed
- 測試輸出：見上，全數通過。Niko 亦於重啟後端後在實際 App 重新查詢單字，確認顯示正確繁體中文（「中文也沒問題」）。
- 螢幕截圖：不適用。
- 已知限制：MyMemory 是翻譯記憶庫比對服務，即使語言代碼修正為繁體，個別詞語的翻譯品質仍可能不準確（見 TASK-031 已記錄的已知限制），本卡只解決「簡體 vs 繁體」這個字集問題，不解決翻譯準確度問題；準確度問題已有 TASK-033 的編輯功能作為手動修正管道。
- 後續任務：無。
