# 畫面規格

## Metadata

- 功能：本地 Web UI（Phase 4）／Epic 0「UI 設計系統」S5
- 畫面：Dashboard（首頁）
- 狀態：草稿 | mockup 已核准 | 已實作 → **草稿，mockup 已產出待人工選定**

## 目的

使用者（唯一使用者 Niko）打開 App 後的第一個畫面，用來快速掌握「今天要做什麼」與「學得怎麼樣」：今日待複習卡片數、連續複習天數、正確率、追劇時數、單字增長趨勢、過去 5 週的複習日曆，並能一鍵切換 en/de 語言視角。這是本機單人工具，不需要處理多使用者、權限分級或團隊協作情境。

## 版面配置

三個變體的版面配置不同，共同的內容區塊如下（差異見下方「變體比較」）：

- 主要區域：今日待複習 CTA（含連續複習天數）、KPI 統計（正確率／觀看時數／總單字量或今日待複習張數）、單字成長趨勢圖、複習日曆熱力圖。
- 次要區域：複習佇列（今日到期前 5 筆）、最近追劇紀錄。
- 導覽：Dashboard／單字庫／追劇紀錄／複習 四個主要頁面之間切換。
- 動作：開始複習（導向複習頁）、切換 en/de 語言視角。

## 狀態

| 狀態 | 必要行為 | 空狀態／錯誤文案 | 驗證方式 |
|---|---|---|---|
| 預設 | 顯示所有 KPI、圖表、佇列與追劇紀錄 | — | 見 mockups/（螢幕截圖留待 S5 核准後、實作階段用真實資料截圖） |
| 載入中 | 各卡片顯示 skeleton（沿用 `bg-surface-hover` 色塊佔位），避免整頁白屏 | — | 待實作階段補截圖 |
| 空狀態 | 全新使用者尚無任何複習紀錄／追劇紀錄時：複習日曆全空、佇列顯示「今天沒有待複習的卡片」、追劇紀錄顯示「還沒有追劇紀錄，去新增一筆吧」 | 見前欄 | 待實作階段補截圖 |
| 錯誤 | API 讀取失敗時，各卡片區塊各自顯示「讀取失敗，請重試」＋重試按鈕，不整頁掛掉 | 「讀取失敗，請重試」 | 待實作階段補截圖 |
| 停用 | 不適用（本機單人工具無停用態的 Dashboard 檢視） | — | — |
| 權限不足 | 不適用（單人本機使用，無多使用者權限分級） | — | — |
| 行動裝置版 | 三個變體皆需能在窄螢幕下改為單欄堆疊；變體 A／C 的 sidebar／icon rail 在行動裝置版收合為頂部選單（mockup 階段以桌面版為主，行動裝置版留待選定版型後在 screen-spec 補完整規格） | — | 待實作階段補截圖 |

## 互動

| 動作 | 觸發條件 | 結果 | 失敗情境 |
|---|---|---|---|
| 開始複習 | 點擊「開始複習」CTA 按鈕 | 導向複習頁面，帶入今日待複習佇列 | 佇列為空時按鈕停用並顯示「今天沒有待複習」 |
| 切換語言視角 | 點擊 EN／DE 切換 | 全部 Dashboard 內容（KPI、圖表、佇列）依語言重新查詢 | API 失敗時保留原語言畫面並提示錯誤 |
| 展開資料表格 | 點擊圖表下方「顯示資料表格」 | 以原生 `<details>` 展開對應的無障礙表格版本（單字成長趨勢、複習日曆） | 不適用（純前端展開，無失敗情境） |
| 查看複習佇列項目 | 點擊佇列中的單字 | 導向該單字的詳情／編輯畫面 | 找不到對應單字時顯示 404 提示 |

## 設計系統對照

- 用到的既有 design token：`color.bg.page`／`color.bg.surface`／`color.bg.surface-hover`／`color.border.default`／`color.fg.primary`／`color.fg.muted`／`color.accent.*`／`color.link`（info-500，用於趨勢線）／`color.success`／`color.warning`／`color.danger`／`space.card`（16px）／`space.page`（32px）／`radius.card`（3px）／`radius.control`（4px）／`radius.pill`（999px）／字級 scale（11/12/13/14/16/18/20/24/30）／`font.mono`（表格數字用 tabular-nums）。
- 用到的既有元件：Card、Badge、Button、NavigationMenu（變體 A／B 的導覽）。
- 本畫面新做的元件／視覺模式（皆只用既有 token 組成，未引入新色值）：
  - **Stat tile（KPI 卡片）**：label + value（比例數字，非 tabular-nums）+ 可選 delta。已是 S4 `Card` 的組合用法，非全新元件，暫不需要獨立登記；若後續多處重複使用，可考慮抽成 `StatTile` 元件並登記回 inventory。
  - **單字成長趨勢圖（line chart）**：單一數列（`color.link` info-500），依 dataviz skill 判斷「trend over time、單數列」不需要圖例，只在終點（今天）標示數值。
  - **複習日曆熱力圖（calendar heatmap）**：單一色相（accent／brand 黃）depth 由淺至深対應複習張數多寡（暗色模式下「愈亮＝愈多」，符合 dataviz skill 的 sequential ramp 在暗色模式的 anchor 反轉規則）。
  - 兩個圖表皆附「顯示資料表格」的原生 `<details>` 展開，作為 dataviz skill 要求的「table-view 雙生」無障礙後備。
  - 依 dataviz skill 的六項檢查範圍：六項檢查只適用於「categorical 多數列」色票；本畫面的趨勢圖是單數列、熱力圖是單一色相 sequential ramp，兩者皆不在檢查範圍內（見 `color-formula.md`「Scope」），因此未執行 `validate_palette.js`，也不需要。

## 視覺驗收標準

- 文字在手機版與桌面版都不會被截斷。
- 主要動作（開始複習）清楚明確，是畫面上視覺權重最高的元素之一。
- 錯誤與空狀態明確呈現（見上方「狀態」表）。
- **色彩、字體、間距、圓角、陰影一律取自 `design-system.md` 的 design token，沒有硬寫的一次性數值。**
- **重複使用元件庫 inventory 裡的既有元件；任何新做的元件都依既有 token 與風格製作，且已登記回 inventory。**
- 圖表遵守 `ai/skills` 下 dataviz skill 的紀律：單數列不強加圖例、趨勢圖只標示終點數值、熱力圖用單一色相 sequential ramp、大數字（KPI value）用比例數字而非 tabular-nums、表格內數字才用 tabular-nums、每個圖表都有資料表格作為無障礙後備。
