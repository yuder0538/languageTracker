# 設計系統（Design System）

由 Epic 0「專案設置」的「UI 設計系統」User Story 分五階段（框架 → 風格 → design token → 元件庫 → 版面）逐步填寫。**這份文件是後續所有功能 Epic 做 UI 時的單一事實來源**：任何前端任務開工前都要先讀它，能用既有 token／元件就必須用；缺的元件要照既有風格補做並登記回這裡（見 `ai/skills/project-kickoff.md` 步驟 6 與 `ai/skills/ui-mockup-gate.md`）。

狀態：S1-S5 已核准，UI 設計系統五階段流程完成。後續功能 Epic 的 UI 任務開工前仍須先讀本文件；新畫面缺元件時依既有規則補做並登記回本文件。

## S1 底層框架

- UI 框架／建置工具：React + Vite（純 SPA，不需 SSR）
- 元件庫策略：採用現成 — shadcn/ui（程式碼直接複製進專案、非 npm 包裝，利於後續客製 design token）
- 樣式方案：Tailwind CSS（與 shadcn/ui 標準搭配）
- 選定理由：本產品是本機單人使用的工具（無多租戶、無需 SSR/SEO），Vite+React 起模最快、複雜度最低；shadcn/ui 讓元件樣式完全可控，便於配合後續 S3 定案的 design token 客製，優於 MUI/Ant Design 較重的預設視覺風格，也優於從零自建的高成本。
- 人工核准：Niko / 2026-07-25

## S2 風格方向

- 選定的 style tile：字幕夜場 Subtitle Room（三個提案：卡片抽屜 Card Catalogue／字幕夜場 Subtitle Room／學習儀表板 Signal Board，比較頁見 TASK-023 完成證據）
- 色彩情緒：電影字幕感、專注、夜間。近黑背景（#121214）＋卡片底（#1B1B1E）＋字幕黃強調（#E8B944，唯一強調色，用於狀態標籤／到期標記等需要注意力的地方）＋次強調藍（#4FA3C7，連結／次要資訊用）＋邊線（#2B2B2E）。
- 字體個性：全程無襯線（system-ui / Segoe UI / PingFang TC / 微軟正黑體 fallback），標題字重 600、內文 400，靠字級與顏色分層而非襯線；所有數字／時間一律等寬字（tabular nums），呼應字幕時間碼的視覺語言。
- 圓角／陰影傾向：小圓角（3px，字幕框感）；不用陰影，靠卡片底色（#1B1B1E）與背景色（#121214）的層次分深淺，避免深色模式下陰影不明顯的問題。
- 密度：緊湊（卡片內距 16px 起跳，非 24px）。
- 亮／暗模式：以暗色為主；亮色模式在 S3 定義 token 時一併給出對應淺色值，供系統跟隨或未來需要時使用，但預設與主要使用情境是暗色。
- 參考產品：電影字幕配色、Letterboxd 深色模式、Terminal 介面。
- 人工核准：Niko / 2026-07-25

## S3 Design Token 清單

從 S2 選定的「字幕夜場 Subtitle Room」（暗色為主、無襯線、等寬數據、不用陰影靠背景分層）展開。暗色為主要模式，亮色對應值一併列出供系統跟隨或未來需要時使用。

### Primitive Token — 色彩

**Grey scale**（中性色，微暖、非藍調，呼應「電影夜場」而非「科技冷灰」）

| Token | 值 | 備註 |
|---|---|---|
| grey.50 | `#F7F7F8` | 亮模式頁面底 |
| grey.100 | `#EDEDED` | 暗模式主文字 |
| grey.200 | `#D4D4D6` | 亮模式邊線 |
| grey.300 | `#B0B0B3` | |
| grey.400 | `#8C8C90` | |
| grey.500 | `#6E6E72` | 亮模式次要文字 |
| grey.600 | `#525256` | |
| grey.700 | `#38383B` | |
| grey.800 | `#26262A` | 暗模式 surface-hover／chip 底 |
| grey.900 | `#1B1B1E` | 暗模式卡片底（surface） |
| grey.950 | `#121214` | 暗模式頁面底 |

**Accent scale**（字幕黃，唯一主強調色，H≈43°）

| Token | 值 |
|---|---|
| accent.100 | `#F6E7C4` |
| accent.300 | `#E8BE66` |
| accent.500 | `#E8B944`（基準） |
| accent.600 | `#C89B2F` |
| accent.700 | `#A17D26` — 亮模式文字用（對白底對比更足） |
| accent.900 | `#524014` |

**Secondary scale**（次強調藍，連結／次要資訊，同時作為語意 info 色，H≈197°）

| Token | 值 |
|---|---|
| secondary.300 | `#7FC7DF` |
| secondary.500 | `#4FA3C7`（基準） |
| secondary.700 | `#2E6580` — 亮模式文字用 |

**語意色**（與強調色分開，各自獨立色相，避免與主強調黃混淆）

| Token | 值（500 基準） | 用途 |
|---|---|---|
| success.500 | `#3EA574` | 成功／答對／已完成 |
| warning.500 | `#D97B29` | 警示（刻意偏橘、與強調黃區隔） |
| danger.500 | `#E5484D` | 錯誤／刪除／答錯 |
| info.500 | `#4FA3C7` | 沿用 secondary scale |

### Primitive Token — 字級 / 字重 / 行高

| 類別 | Token | 值 |
|---|---|---|
| 字級 scale | font-size.* | `11 / 12 / 13 / 14 / 16 / 18 / 20 / 24 / 30 / 36 / 48`（px） |
| 字重 | font-weight.regular | 400（內文） |
| 字重 | font-weight.medium | 500（強調文字） |
| 字重 | font-weight.semibold | 600（標題，S2 決議：字幕夜場不用 700 重標題，維持克制） |
| 行高 | line-height.heading | 1.25 |
| 行高 | line-height.body | 1.6 |
| 字距 | letter-spacing.heading | -0.01em |
| 字距 | letter-spacing.body | 0（中文一律 0） |
| 字距 | letter-spacing.label | 0.04em（大寫小標籤限定） |
| 字族 | font.display / font.body | `-apple-system, "Segoe UI", Roboto, "PingFang TC", "Microsoft JhengHei", sans-serif` |
| 字族 | font.mono | `ui-monospace, "SFMono-Regular", Consolas, "Liberation Mono", monospace`（數字／時間戳一律用，含 `tabular-nums`） |

### Primitive Token — 間距 / 圓角 / 陰影 / z-index / 動效

| 類別 | Token | 值 |
|---|---|---|
| 間距 scale | space.* | `4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64`（px） |
| 圓角 | radius.control | 4px（按鈕／輸入框） |
| 圓角 | radius.card | 3px（卡片，S2 決議：字幕框感、非圓潤） |
| 圓角 | radius.modal | 6px（對話框等大面積容器） |
| 圓角 | radius.pill | 999px（狀態標籤／badge，維持可掃視性） |
| 陰影 | shadow.none | `none`（暗模式預設：不用陰影，靠 surface 三階分層） |
| 陰影 | shadow.sm | `0 1px 2px rgba(0,0,0,.24), 0 1px 1px rgba(0,0,0,.16)`（暗模式極少數需要浮起感時） |
| 陰影 | shadow.light-sm | `0 1px 2px rgba(20,18,10,.06), 0 6px 16px rgba(20,18,10,.08)`（亮模式對應，白底陰影比背景分層更明顯，depth 選陰影） |
| z-index | z.dropdown / z.sticky / z.overlay / z.modal / z.toast / z.tooltip | `10 / 20 / 30 / 40 / 50 / 60` |
| 動效 | duration.fast / base / slow | `120ms / 160ms / 240ms` |
| 動效 | easing.standard | `cubic-bezier(.2,0,0,1)` |
| 動效 | — | 全域遵守 `prefers-reduced-motion` |

### Semantic Token

**暗模式（主要模式）**

| Token | 對應 primitive | 用途 |
|---|---|---|
| color.bg.page | grey.950 | 頁面底色 |
| color.bg.surface | grey.900 | 卡片／面板底色（elevation 第一層） |
| color.bg.surface-hover | grey.800 | 卡片 hover／overlay（elevation 第二層，取代陰影） |
| color.border.default | grey.800 | 卡片／輸入框邊線 |
| color.fg.primary | grey.100 | 主要文字 |
| color.fg.muted | grey.500→調亮至 `#9A9A9A` | 次要文字（暗底需比 grey.500 亮，見元件實測值） |
| color.fg.on-accent | grey.950 | 黃色強調底上的文字（深色字對比足） |
| color.accent.default / hover / active | accent.500 / accent.600 / accent.700 | 主要互動元素（按鈕、到期標籤、focus ring） |
| color.link | secondary.500 | 次要資訊／連結 |
| color.success / warning / danger / info | success.500 / warning.500 / danger.500 / info.500 | 語意狀態，與 accent 分開，不共用色相 |

**亮模式（次要模式，供系統跟隨或未來需要時使用）**

| Token | 對應 primitive | 用途 |
|---|---|---|
| color.bg.page | grey.50 | 頁面底色 |
| color.bg.surface | `#FFFFFF` | 卡片底色 |
| color.bg.surface-hover | grey.100 | 卡片 hover |
| color.border.default | grey.200 | 邊線 |
| color.fg.primary | grey.950 | 主要文字 |
| color.fg.muted | grey.500 | 次要文字 |
| color.fg.on-accent | grey.950 | 黃色強調底上的文字 |
| color.accent.default | accent.700 | 白底用較深的金色維持 AA 對比 |
| color.link | secondary.700 | 次要資訊／連結 |
| shadow.elevation | shadow.light-sm | 亮模式改用陰影而非背景分層 |

**通用（不分模式）**

| Token | 值 | 用途 |
|---|---|---|
| space.page | 32px | 頁面外距 |
| space.card | 16px | 卡片內距（S2 決議：緊湊密度，非 24px） |
| space.section-gap | 32px | 區塊間距 |
| space.stack-sm / stack-md | 8px / 16px | 元件內部堆疊間距 |

### 實際 token 檔位置

- 專案內真實 token 檔路徑：待補。目前尚無可跑的前端專案（Vite+React 骨架將於 S4 建立），依 `ai/skills/project-kickoff.md` 步驟 2a 說明，可先留空、僅以上表為準；S4 建立 `frontend/` 專案骨架時會一併產出 `tailwind.config.ts` 主題設定（對應上表）並回填實際路徑。
- 人工核准：Niko / 2026-07-25（token 預覽 Artifact 頁核准，見 TASK-024 完成證據）

## S4 元件庫 Inventory

每做一個核心元件就登記一列。後續 Epic 缺元件、照風格補做後也要回來補登。

底層採 shadcn/ui「base-nova」style（S1 核准的策略：程式碼直接複製進專案），元件皆以 `@base-ui/react` primitive 包裝、`class-variance-authority` 管理 variant，樣式全部走 S3 token 產出的 Tailwind 語意 class（`bg-primary`、`text-destructive`、`ring-ring/50` 等），未手刻任何獨立色值。真實 token 檔：`frontend/src/index.css`（primitive 色票 `--grey-*`/`--brand-*`/`--info-*` 與 light/`​.dark` 兩組 semantic 變數）＋ `frontend/tailwind.config` 由 `@theme inline` 直接在 CSS 內映射（Tailwind v4 不需獨立 config 檔）。狀態示範頁：`frontend/src/pages/ComponentShowcase.tsx`（本地 Web UI Epic 開始接真實頁面後，`App.tsx` 改為渲染 `Dashboard`；元件庫展示頁保留在原始碼中供之後補頁面時參考，目前尚未掛路由，見 TASK-027）。

| 元件 | 狀態 | 涵蓋狀態 | 用到的 token | 檔案位置 | 截圖 | 來源階段 |
|---|---|---|---|---|---|---|
| Button | 完成 | 預設/hover/focus/停用/載入（新增 `loading` prop + `Loader2Icon` spinner） | `color.accent`/`color.bg.surface-hover`／`radius.control`／`duration.fast` | `frontend/src/components/ui/button.tsx` | pages/ComponentShowcase.tsx「Button」區塊 | S4 |
| Input | 完成 | 預設/focus/停用/錯誤（`aria-invalid`） | `color.border.default`／`color.danger`／`radius.control` | `frontend/src/components/ui/input.tsx` | pages/ComponentShowcase.tsx「Form」區塊 | S4 |
| Select | 完成 | 預設/focus/停用/錯誤/開啟中 | `color.border.default`／`color.bg.surface`／`radius.control` | `frontend/src/components/ui/select.tsx` | pages/ComponentShowcase.tsx「Form」區塊 | S4 |
| Checkbox | 完成 | 預設/勾選/停用/錯誤 | `color.accent`／`radius.control`（4px） | `frontend/src/components/ui/checkbox.tsx` | pages/ComponentShowcase.tsx「Form」區塊 | S4 |
| Field（Form 組合） | 完成 | 預設/含說明文字/錯誤（label 連動變色） | `color.danger`／`space.stack-sm` | `frontend/src/components/ui/field.tsx` | pages/ComponentShowcase.tsx「Form」區塊 | S4 |
| Card | 完成 | 預設/hover（table row 有 hover，card 本身依 S2 決議不做 hover 位移） | `color.bg.surface`／`radius.card`／`space.card` | `frontend/src/components/ui/card.tsx` | pages/ComponentShowcase.tsx「Card」區塊（der Tisch 單字卡／Friends 追劇紀錄卡） | S4 |
| Nav | 完成 | 預設/hover/focus/使用中（active） | `color.bg.surface-hover`／`radius.control` | `frontend/src/components/ui/navigation-menu.tsx` | pages/ComponentShowcase.tsx 頁首導覽列 | S4 |
| Modal/Dialog | 完成 | 開啟/關閉動畫/遮罩/focus trap（base-ui 內建） | `color.bg.surface`／`radius.modal`／`z.modal`／`duration.base` | `frontend/src/components/ui/dialog.tsx` | pages/ComponentShowcase.tsx「Modal」區塊（刪除單字確認） | S4 |
| Table | 完成 | 預設列/hover/選取（`data-state=selected`） | `color.border.default`／`color.bg.surface-hover` | `frontend/src/components/ui/table.tsx` | pages/ComponentShowcase.tsx「Table」區塊（單字庫列表） | S4 |
| Form | 完成 | 見 Field／Input／Select／Checkbox 各列 | — | `frontend/src/components/ui/field.tsx` | pages/ComponentShowcase.tsx「Form」區塊 | S4 |
| Toast | 完成 | success/error/info/loading 四種語意（sonner 內建） | `color.success`／`color.danger`／`color.info` | `frontend/src/components/ui/sonner.tsx` | pages/ComponentShowcase.tsx「Toast」區塊（點擊按鈕觸發） | S4 |
| Alert | 完成 | 預設/危險（destructive） | `color.bg.surface`／`color.danger` | `frontend/src/components/ui/alert.tsx` | pages/ComponentShowcase.tsx「Alert / Badge」區塊 | S4 |
| Badge | 完成 | default/secondary/destructive/success/warning/outline/ghost/link | `color.accent`／`color.success`／`color.warning`／`color.danger` | `frontend/src/components/ui/badge.tsx` | pages/ComponentShowcase.tsx「Card」「Table」「Alert / Badge」區塊 | S4 |
| Chart Tooltip | 待實作 | hover（滑鼠）/tap（觸控）；guideline 垂直線＋浮動框顯示於資料點上方 | `color.bg.surface`／`color.border.default`／`color.fg.primary`／`color.fg.muted`／`shadow.sm`（例外：手刻 SVG 圖表浮於內容之上，depth 用陰影而非背景分層，見 S2） | 待實作（規劃於 `frontend/src/pages/Dashboard.tsx`，沿用既有圖表函式同檔慣例；非 base-ui primitive——現有圖表為手刻 SVG，需自行以座標計算定位） | 見 `ai/artifacts/專案設置/mockups/dashboard-variant-charts-a.html` | 本地 Web UI Epic（Dashboard 追加需求，2026-07-30 提出，2026-08-01 選定變體 A） |

（「來源階段」記錄這個元件是 S4 初建，還是後續某個功能 Epic 補做並回登的。）

- 人工核准：Niko / 2026-07-25（在本機執行 `npm install && npm run dev` 開啟 pages/ComponentShowcase.tsx 展示頁確認暗色背景、八大區塊、亮暗模式切換、德文單字表格皆正常，並跑過 `npm run build`／`npm run lint` 皆無錯誤，核准）。

## S5 各介面版面

本產品只有一種使用者端（本機單人工具，無管理員／顧客之分）。

| 介面／使用者端 | 選定版型 | Mockup 決策紀錄 | 人工核准 |
|---|---|---|---|
| Dashboard（唯一使用者端首頁） | 變體 C — Command Center（左側 icon rail＋中央進度環主視覺＋右側 KPI／佇列欄，下方橫跨全寬放熱力圖與追劇紀錄） | `ai/artifacts/專案設置/mockup-decision-dashboard.md` | Niko / 2026-07-25 |
