import { RotateCcwIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle } from "@/components/ui/card"
import { AppRail } from "@/components/app-rail"
import { useLanguage } from "@/lib/language-context"
import { useRouter } from "@/lib/router"
import { useApi } from "@/hooks/use-api"
import {
  fetchMediaLogs,
  fetchReviewHistory,
  fetchReviewQueue,
  fetchReviewStats,
  fetchVocabulary,
  type MediaLogRead,
  type ReviewHistoryDay,
  type ReviewStats,
  type VocabularyRead,
} from "@/lib/dashboard-api"

const VOCAB_GROWTH_DAYS = 14
const HISTORY_DAYS = 35
const WEEKDAY_LABELS = ["日", "一", "二", "三", "四", "五", "六"]

function formatDate(iso: string) {
  const [, m, d] = iso.split("-")
  return `${Number(m)}/${Number(d)}`
}

function weekdayLabel(iso: string) {
  return WEEKDAY_LABELS[new Date(`${iso}T00:00:00`).getDay()]
}

function ErrorNote({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="flex flex-col items-start gap-2 text-sm text-destructive">
      <span>讀取失敗：{message}</span>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RotateCcwIcon /> 重試
      </Button>
    </div>
  )
}

function SkeletonBlock({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-md bg-muted ${className}`} />
}

// ---- 今日複習進度環 ----

function FocusCard({
  stats,
  statsError,
  retryStats,
  queueCount,
  queueError,
  retryQueue,
  onStartReview,
}: {
  stats: ReviewStats | null
  statsError: string | null
  retryStats: () => void
  queueCount: number | null
  queueError: string | null
  retryQueue: () => void
  onStartReview: () => void
}) {
  const loading = stats === null && !statsError
  const remaining = queueCount ?? 0
  const done = stats?.reviewed_today ?? 0
  const total = done + remaining
  const ratio = total > 0 ? done / total : 0
  const circumference = 2 * Math.PI * 70
  const dash = circumference * ratio

  return (
    <Card className="flex flex-col items-center gap-6 p-6 sm:flex-row sm:p-8">
      <div className="relative size-40 shrink-0">
        <svg viewBox="0 0 160 160" width="160" height="160" className="-rotate-90">
          <circle cx="80" cy="80" r="70" fill="none" style={{ stroke: "var(--muted)" }} strokeWidth="12" />
          <circle
            cx="80"
            cy="80"
            r="70"
            fill="none"
            style={{ stroke: "var(--primary)" }}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${dash} ${circumference}`}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-semibold">
            {loading ? "…" : `${done}/${total}`}
          </span>
          <span className="text-xs text-muted-foreground">已複習</span>
        </div>
      </div>
      <div className="flex flex-1 flex-col gap-2">
        {statsError ? (
          <ErrorNote message={statsError} onRetry={retryStats} />
        ) : (
          <span className="text-sm font-medium text-primary">
            {loading ? <SkeletonBlock className="h-4 w-32" /> : `🔥 連續複習 ${stats?.streak_days ?? 0} 天`}
          </span>
        )}
        {queueError ? (
          <ErrorNote message={queueError} onRetry={retryQueue} />
        ) : (
          <span className="text-xl font-semibold">
            {queueCount === null
              ? <SkeletonBlock className="h-7 w-48" />
              : remaining > 0
                ? `還有 ${remaining} 張待複習`
                : "今天的複習都完成了"}
          </span>
        )}
        <Button
          className="mt-1 self-start"
          disabled={remaining === 0}
          onClick={onStartReview}
        >
          {remaining > 0 ? "繼續複習 →" : "今天沒有待複習"}
        </Button>
      </div>
    </Card>
  )
}

// ---- 單字成長趨勢圖 ----

function buildLinePoints(values: number[]) {
  const width = 700
  const height = 170
  const padLeft = 40
  const padRight = 20
  const padTop = 20
  const padBottom = 20
  const max = Math.max(1, ...values)
  const plotWidth = width - padLeft - padRight
  const plotHeight = height - padTop - padBottom
  const stepX = values.length > 1 ? plotWidth / (values.length - 1) : 0
  const points = values.map((v, i) => ({
    x: padLeft + i * stepX,
    y: padTop + plotHeight - (v / max) * plotHeight,
  }))
  return { points, max, width, height, padLeft, padTop, padBottom, plotHeight }
}

function VocabGrowthChart({ vocabulary }: { vocabulary: VocabularyRead[] }) {
  const today = new Date()
  const buckets = new Map<string, number>()
  for (let i = VOCAB_GROWTH_DAYS - 1; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    buckets.set(d.toISOString().slice(0, 10), 0)
  }
  for (const word of vocabulary) {
    const day = word.created_at.slice(0, 10)
    if (buckets.has(day)) buckets.set(day, (buckets.get(day) ?? 0) + 1)
  }
  const days = Array.from(buckets.keys())
  const values = Array.from(buckets.values())
  const total = values.reduce((sum, v) => sum + v, 0)

  if (vocabulary.length === 0) {
    return (
      <p className="px-4 pb-4 text-sm text-muted-foreground">
        還沒有任何單字紀錄，開始新增單字後這裡會顯示成長趨勢。
      </p>
    )
  }

  const { points, max, width, height, padLeft, padTop, plotHeight } = buildLinePoints(values)
  const linePoints = points.map((p) => `${p.x},${p.y}`).join(" ")
  const areaPoints = `${linePoints} ${points[points.length - 1].x},${padTop + plotHeight} ${points[0].x},${padTop + plotHeight}`
  const last = points[points.length - 1]

  return (
    <div className="px-4 pb-4">
      <svg viewBox={`0 0 ${width} ${height}`} width="100%" height={height} role="img" aria-label="每日新增單字折線圖">
        <line x1={padLeft} y1={padTop} x2={width - 20} y2={padTop} style={{ stroke: "var(--border)" }} strokeWidth={1} />
        <line x1={padLeft} y1={padTop + plotHeight} x2={width - 20} y2={padTop + plotHeight} style={{ stroke: "var(--border)" }} strokeWidth={1} />
        <text x={padLeft - 10} y={padTop + 4} textAnchor="end" fontSize={11} style={{ fill: "var(--muted-foreground)" }}>{max}</text>
        <text x={padLeft - 10} y={padTop + plotHeight + 4} textAnchor="end" fontSize={11} style={{ fill: "var(--muted-foreground)" }}>0</text>
        <polygon points={areaPoints} style={{ fill: "var(--info-500)" }} opacity={0.1} />
        <polyline points={linePoints} fill="none" style={{ stroke: "var(--info-500)" }} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={last.x} cy={last.y} r={4} style={{ fill: "var(--primary)", stroke: "var(--card)" }} strokeWidth={2} />
        <text x={last.x - 8} y={last.y - 12} textAnchor="end" fontSize={12} fontWeight={600} style={{ fill: "var(--foreground)" }}>
          今天 +{values[values.length - 1]}
        </text>
        <text x={padLeft} y={height - 4} fontSize={11} style={{ fill: "var(--muted-foreground)" }}>{formatDate(days[0])}</text>
        <text x={width - 20} y={height - 4} textAnchor="end" fontSize={11} style={{ fill: "var(--muted-foreground)" }}>{formatDate(days[days.length - 1])}</text>
      </svg>
      <details className="mt-1">
        <summary className="cursor-pointer text-xs text-primary select-none">顯示資料表格</summary>
        <table className="mt-2 w-full text-xs [font-variant-numeric:tabular-nums]">
          <thead>
            <tr><th className="p-1 text-left">日期</th><th className="p-1 text-left">新增單字</th></tr>
          </thead>
          <tbody>
            {days.map((day, i) => (
              <tr key={day} className="border-t border-border">
                <td className="p-1">{formatDate(day)}</td>
                <td className="p-1">{values[i]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
      {total === 0 && (
        <p className="mt-2 text-xs text-muted-foreground">過去 {VOCAB_GROWTH_DAYS} 天沒有新增單字。</p>
      )}
    </div>
  )
}

// ---- 複習日曆熱力圖 ----

function heatLevelClass(count: number) {
  if (count === 0) return "bg-muted"
  if (count <= 3) return "bg-brand-900"
  if (count <= 7) return "bg-brand-700"
  if (count <= 12) return "bg-brand-600"
  if (count <= 17) return "bg-brand-500"
  return "bg-brand-300"
}

function ReviewHeatmap({ history }: { history: ReviewHistoryDay[] }) {
  const totalReviewed = history.reduce((sum, day) => sum + day.reviewed_count, 0)

  return (
    <div className="px-4 pb-4">
      {/* grid-cols-7 wraps every 7 cells onto a new row on its own, so a flat
          map (oldest first) already lays out as one row per week. */}
      <div className="grid max-w-[280px] grid-cols-7 gap-[3px]">
        {history.map((day) => (
          <div
            key={day.date}
            title={`${day.date}（週${weekdayLabel(day.date)}） · ${day.reviewed_count} 張`}
            className={`aspect-square rounded-sm ${heatLevelClass(day.reviewed_count)}`}
          />
        ))}
      </div>
      <div className="mt-2 flex items-center gap-1 text-xs text-muted-foreground">
        少
        <div className="size-2.5 rounded-sm bg-muted" />
        <div className="size-2.5 rounded-sm bg-brand-900" />
        <div className="size-2.5 rounded-sm bg-brand-700" />
        <div className="size-2.5 rounded-sm bg-brand-600" />
        <div className="size-2.5 rounded-sm bg-brand-500" />
        <div className="size-2.5 rounded-sm bg-brand-300" />
        多
      </div>
      {totalReviewed === 0 && (
        <p className="mt-2 text-xs text-muted-foreground">過去 {HISTORY_DAYS} 天還沒有複習紀錄。</p>
      )}
    </div>
  )
}

// ---- 頁面主體 ----

export default function Dashboard() {
  const { language } = useLanguage()
  const { navigate } = useRouter()

  const stats = useApi(() => fetchReviewStats(language), [language])
  const queue = useApi(() => fetchReviewQueue(language), [language])
  const history = useApi(() => fetchReviewHistory(language, HISTORY_DAYS), [language])
  const vocabulary = useApi(() => fetchVocabulary(language), [language])
  const mediaLogs = useApi(() => fetchMediaLogs(language), [language])

  const totalVocab = vocabulary.status === "success" ? vocabulary.data.length : null
  const newThisWeek =
    vocabulary.status === "success"
      ? vocabulary.data.filter(
          (w) => Date.now() - new Date(w.created_at).getTime() <= 7 * 24 * 60 * 60 * 1000
        ).length
      : null

  const weekWatchMinutes =
    mediaLogs.status === "success"
      ? mediaLogs.data
          .filter((log) => Date.now() - new Date(log.watched_date).getTime() <= 7 * 24 * 60 * 60 * 1000)
          .reduce((sum, log) => sum + log.duration_minutes, 0)
      : null

  const recentMedia: MediaLogRead[] = mediaLogs.status === "success" ? mediaLogs.data.slice(0, 2) : []

  const accuracy7d =
    history.status === "success"
      ? (() => {
          const last7 = history.data.slice(-7)
          const reviewed = last7.reduce((sum, d) => sum + d.reviewed_count, 0)
          const correct = last7.reduce((sum, d) => sum + d.correct_count, 0)
          return reviewed > 0 ? Math.round((correct / reviewed) * 100) : null
        })()
      : null

  return (
    <div className="flex min-h-screen">
      <AppRail />

      <main className="flex flex-1 flex-col gap-6 p-8">
        <FocusCard
          stats={stats.status === "success" ? stats.data : null}
          statsError={stats.status === "error" ? stats.message : null}
          retryStats={stats.retry}
          queueCount={queue.status === "success" ? queue.data.length : null}
          queueError={queue.status === "error" ? queue.message : null}
          retryQueue={queue.retry}
          onStartReview={() => navigate("/review")}
        />

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">單字成長</CardTitle>
            <p className="text-xs text-muted-foreground">過去 {VOCAB_GROWTH_DAYS} 天新增單字數</p>
          </CardHeader>
          {vocabulary.status === "loading" && <div className="px-4 pb-4"><SkeletonBlock className="h-[170px] w-full" /></div>}
          {vocabulary.status === "error" && <div className="px-4 pb-4"><ErrorNote message={vocabulary.message} onRetry={vocabulary.retry} /></div>}
          {vocabulary.status === "success" && <VocabGrowthChart vocabulary={vocabulary.data} />}
        </Card>

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">複習日曆</CardTitle>
              <p className="text-xs text-muted-foreground">過去 {HISTORY_DAYS} 天每日複習張數</p>
            </CardHeader>
            {history.status === "loading" && <div className="px-4 pb-4"><SkeletonBlock className="h-32 w-72" /></div>}
            {history.status === "error" && <div className="px-4 pb-4"><ErrorNote message={history.message} onRetry={history.retry} /></div>}
            {history.status === "success" && <ReviewHeatmap history={history.data} />}
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-sm">最近追劇</CardTitle>
            </CardHeader>
            <div className="flex flex-col">
              {mediaLogs.status === "loading" && (
                <div className="flex flex-col gap-2 px-4 pb-4">
                  <SkeletonBlock className="h-10 w-full" />
                  <SkeletonBlock className="h-10 w-full" />
                </div>
              )}
              {mediaLogs.status === "error" && <div className="px-4 pb-4"><ErrorNote message={mediaLogs.message} onRetry={mediaLogs.retry} /></div>}
              {mediaLogs.status === "success" && recentMedia.length === 0 && (
                <p className="px-4 pb-4 text-sm text-muted-foreground">還沒有追劇紀錄，去新增一筆吧。</p>
              )}
              {recentMedia.map((log) => (
                <div key={log.id} className="flex items-center gap-3 border-t border-border px-4 py-3 first:border-t-0">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted text-sm">🎬</div>
                  <div>
                    <div className="text-sm font-medium">{log.title}</div>
                    <div className="text-xs text-muted-foreground">{log.watched_date} · {log.duration_minutes} 分鐘</div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </main>

      <aside className="flex w-[280px] flex-col gap-4 border-l border-border p-6">
        <div className="border-b border-border pb-3">
          <div className="text-xs text-muted-foreground">7 日正確率</div>
          <div className="text-xl font-semibold">
            {history.status === "loading" ? <SkeletonBlock className="h-6 w-16" /> : accuracy7d === null ? "—" : `${accuracy7d}%`}
          </div>
        </div>
        <div className="border-b border-border pb-3">
          <div className="text-xs text-muted-foreground">本週觀看時數</div>
          <div className="text-xl font-semibold">
            {weekWatchMinutes === null
              ? mediaLogs.status === "error" ? "—" : <SkeletonBlock className="h-6 w-20" />
              : `${Math.floor(weekWatchMinutes / 60)}h ${weekWatchMinutes % 60}m`}
          </div>
        </div>
        <div className="pb-1">
          <div className="text-xs text-muted-foreground">總單字量</div>
          <div className="text-xl font-semibold">
            {totalVocab === null
              ? vocabulary.status === "error" ? "—" : <SkeletonBlock className="h-6 w-14" />
              : totalVocab}
          </div>
          {newThisWeek !== null && newThisWeek > 0 && (
            <div className="text-xs text-primary">本週 +{newThisWeek}</div>
          )}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">複習佇列</CardTitle>
            <p className="text-xs text-muted-foreground">今日到期</p>
          </CardHeader>
          <div className="flex flex-col">
            {queue.status === "loading" && (
              <div className="flex flex-col gap-2 px-4 pb-4">
                <SkeletonBlock className="h-8 w-full" />
                <SkeletonBlock className="h-8 w-full" />
              </div>
            )}
            {queue.status === "error" && <div className="px-4 pb-4"><ErrorNote message={queue.message} onRetry={queue.retry} /></div>}
            {queue.status === "success" && queue.data.length === 0 && (
              <p className="px-4 pb-4 text-sm text-muted-foreground">今天沒有待複習的卡片。</p>
            )}
            {queue.status === "success" &&
              queue.data.slice(0, 5).map((word) => (
                <div key={word.id} className="border-t border-border px-4 py-2.5 text-sm first:border-t-0">
                  <div className="font-medium">{word.headword}</div>
                  {word.part_of_speech && (
                    <div className="text-xs text-muted-foreground">{word.part_of_speech}</div>
                  )}
                </div>
              ))}
          </div>
        </Card>
      </aside>
    </div>
  )
}
