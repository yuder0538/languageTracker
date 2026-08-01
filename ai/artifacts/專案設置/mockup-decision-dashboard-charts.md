# Mockup 決策

## Metadata

- 功能：本地 Web UI（Phase 4）／Dashboard 追加需求（2026-07-30）：單字成長指標切換／圖表 Tooltip／追劇時間趨勢卡片
- 畫面：Dashboard（首頁）
- 決策負責人：Niko
- 狀態：已選定

## 變體

三個變體皆用同一批真實專案資料（14 天單字成長、14 天追劇分鐘數），內容範圍相同（單字成長指標切換＋圖表 hover tooltip＋新增「追劇時間趨勢」卡片），差異在**指標切換元件、tooltip 樣式、新卡片版面位置**三個維度。檔案：`ai/artifacts/專案設置/mockups/dashboard-variant-charts-{a,b,c}.html`。

| 變體 | 說明 | 優點 | 風險 |
|---|---|---|---|
| A — Select＋浮動 tooltip＋獨立全寬（推薦） | 指標切換用 Select 下拉；tooltip 為 guideline 垂直線＋浮動框顯示在資料點上方；追劇時間趨勢卡獨立一整排，全寬堆疊在單字成長卡下方。 | 重用既有 `Select` 元件不需新做；guideline＋上方浮動框的 tooltip 可讀性最好，數值不會被手指／游標遮住；獨立全寬讓新圖表有足夠寬度，兩張圖表都維持一致的視覺密度。 | 垂直空間占用最多，手機版需要多滑動一段距離。 |
| B — Segmented pill＋下方 tooltip＋2 欄並排 | 指標切換用 pill 按鈕（兩個並列）；tooltip 為 guideline＋貼齊圖表底部的緊湊框；追劇時間趨勢卡與單字成長卡並排（2 欄 grid）。 | 兩張趨勢圖並排方便左右對照；版面比 A 精簡。 | Segmented pill 是元件庫沒有的新樣式（Select 已核准，pill 切換未登記）；2 欄並排在中等螢幕寬度可能擁擠，且每張圖表寬度變窄，可讀性略降於 A。 |
| C — 純文字連結＋貼點小型 tooltip＋併入底部三卡列 | 指標切換用純文字連結（「新增／累積」）；tooltip 貼在資料點右上角、無 guideline；追劇時間趨勢卡塞進畫面底部三卡列（與複習日曆、最近追劇並排）。 | 最省垂直空間，畫面資訊密度最高。 | 純文字連結切換視覺提示最弱，容易被忽略；無 guideline 的貼點 tooltip 在資料點密集時容易互相遮擋；三卡並排讓每張圖表明顯變小，與「單字成長」主卡的視覺密度不一致，違反 screen-spec 追加需求裡「兩卡版面密度需一致」的驗收標準。 |

## 設計系統對照

- 重用的 token／元件：`color.bg.surface`／`color.border.default`／`color.fg.primary`／`color.fg.muted`／`color.link`／`radius.control`／`space.stack-sm`；下拉選單重用既有 `Select`（`frontend/src/components/ui/select.tsx`），非新元件。
- 新做並登記回 inventory 的元件：**Chart Tooltip**（浮動資料點提示框）——三個變體都需要這個新 pattern，因為現有圖表是手刻 SVG（非 DOM 元素），無法直接重用 base-ui 的 `Tooltip` primitive 定位邏輯，需自行以滑鼠座標／觸控事件計算定位。已依變體 A 的畫法（guideline＋上方浮動框）登記進 `design-system.md` S4 inventory，例外採用 `shadow.sm` 而非背景分層做 depth（理由：tooltip 浮在 SVG 折線內容之上，屬於 S2 陰影規則列舉的「暗模式極少數需要浮起感時」情境，非卡片本身的一般化陰影使用）。

## 選定的變體

- 變體：A — Select 下拉＋浮動 tooltip（guideline＋上方框）＋新卡片獨立全寬堆疊
- 為何選這個：Select 下拉重用既有元件不需新做；guideline＋上方浮動框的 tooltip 可讀性最好；獨立全寬讓「追劇時間趨勢」卡與「單字成長」卡維持一致的版面密度，符合 screen-spec 追加需求的視覺驗收標準。
- 實作前要求的修改：無，Niko 直接選定 A，未要求調整。

## 人工核准

- 核准者：Niko
- 日期：2026-08-01
- 備註：從 A／B／C 三個方向中選定 A，下一步依 `ai/skills/implementation-plan.md` 把這段追加需求拆成任務卡。
