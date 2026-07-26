import { useEffect, useState } from "react"
import { toast } from "sonner"
import { XIcon, RotateCcwIcon, Volume2Icon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ReviewModeSwitch } from "@/components/review-mode-switch"
import { ApiError } from "@/lib/api"
import { useLanguage } from "@/lib/language-context"
import { speak } from "@/lib/speech"
import { useRouter } from "@/lib/router"
import { useApi } from "@/hooks/use-api"
import {
  fetchReviewQueue,
  fetchReviewStats,
  submitReview,
  type ReviewGrade,
} from "@/lib/dashboard-api"

const GRADES: { grade: ReviewGrade; label: string; key: string; className: string }[] = [
  { grade: "again", label: "忘記", key: "1", className: "text-destructive" },
  { grade: "hard", label: "困難", key: "2", className: "text-warning" },
  { grade: "good", label: "一般", key: "3", className: "text-info-500" },
  { grade: "easy", label: "容易", key: "4", className: "text-success" },
]

export default function Review() {
  const { language } = useLanguage()
  const { navigate } = useRouter()
  const queue = useApi(() => fetchReviewQueue(language), [language])
  const stats = useApi(() => fetchReviewStats(language), [language])

  const [index, setIndex] = useState(0)
  const [revealed, setRevealed] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [speaking, setSpeaking] = useState(false)

  useEffect(() => {
    setIndex(0)
    setRevealed(false)
  }, [language])

  const cards = queue.status === "success" ? queue.data : []
  const total = cards.length
  const current = cards[index]

  function handleSpeak() {
    if (!current) return
    setSpeaking(true)
    speak(current.headword, current.language, () => setSpeaking(false))
  }

  // Pronounce the word once as soon as its card appears (both EN and DE).
  useEffect(() => {
    if (!current) return
    handleSpeak()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current?.id])

  async function handleGrade(grade: ReviewGrade) {
    if (!current || submitting) return
    setSubmitting(true)
    try {
      await submitReview(current.id, grade)
      setIndex((i) => i + 1)
      setRevealed(false)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "送出失敗，請重試"
      toast.error(message)
    } finally {
      setSubmitting(false)
    }
  }

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (!current) return
      if (e.key === " " && !revealed) {
        e.preventDefault()
        setRevealed(true)
        return
      }
      if (!revealed || submitting) return
      const match = GRADES.find((g) => g.key === e.key)
      if (match) handleGrade(match.grade)
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, revealed, submitting])

  const progressPct = total > 0 ? Math.min(100, (index / total) * 100) : 0

  return (
    <div className="flex min-h-screen flex-col">
      <div className="flex items-center justify-between px-6 py-4">
        <Button variant="outline" size="icon" onClick={() => navigate("/")} aria-label="離開複習">
          <XIcon />
        </Button>
        <div className="mx-6 flex-1">
          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${progressPct}%` }} />
          </div>
          {total > 0 && (
            <div className="mt-1.5 text-center text-xs text-muted-foreground">
              {Math.min(index + 1, total)} / {total}
            </div>
          )}
        </div>
        <span className="whitespace-nowrap text-xs font-medium text-primary">
          {stats.status === "success" ? `🔥 ${stats.data.streak_days}` : ""}
        </span>
      </div>

      {language === "de" && (
        <div className="flex justify-center pb-2">
          <ReviewModeSwitch mode="standard" />
        </div>
      )}

      <div className="flex flex-1 flex-col items-center justify-center gap-6 p-6">
        {queue.status === "loading" && (
          <div className="h-64 w-full max-w-md animate-pulse rounded-lg bg-muted" />
        )}

        {queue.status === "error" && (
          <div className="flex flex-col items-center gap-3 text-sm text-destructive">
            <span>讀取失敗：{queue.message}</span>
            <Button variant="outline" size="sm" onClick={queue.retry}>
              <RotateCcwIcon /> 重試
            </Button>
          </div>
        )}

        {queue.status === "success" && total === 0 && (
          <div className="flex flex-col items-center gap-4 text-center">
            <p className="text-lg font-medium">今天沒有待複習的卡片</p>
            <Button onClick={() => navigate("/")}>回 Dashboard</Button>
          </div>
        )}

        {queue.status === "success" && total > 0 && index >= total && (
          <div className="flex flex-col items-center gap-4 text-center">
            <p className="text-2xl font-semibold">今天複習完成！🎉</p>
            <p className="text-sm text-muted-foreground">共複習了 {total} 張卡片</p>
            <Button onClick={() => navigate("/")}>回 Dashboard</Button>
          </div>
        )}

        {queue.status === "success" && current && (
          <>
            <Card className="flex w-full max-w-md flex-col items-center gap-2 p-8 text-center">
              <div className="pb-5">
                <div className="flex items-center justify-center gap-2 text-4xl font-semibold">
                  {current.headword}
                  <button
                    type="button"
                    onClick={handleSpeak}
                    aria-label={`朗讀「${current.headword}」`}
                    className={`text-muted-foreground hover:text-foreground ${speaking ? "text-primary" : ""}`}
                  >
                    <Volume2Icon className="size-5" />
                  </button>
                </div>
                {(current.part_of_speech || current.de_artikel) && (
                  <div className="mt-1 text-sm text-muted-foreground">
                    {current.part_of_speech}
                    {current.part_of_speech && current.de_artikel ? " · " : ""}
                    {current.de_artikel}
                  </div>
                )}
              </div>
              {revealed && (
                <div className="flex w-full flex-col items-center gap-1 border-t border-border pt-5">
                  <div className="text-2xl font-medium text-primary">
                    {current.translation_zh ?? current.en_definition ?? "（尚無翻譯資料，之後可用「自動查詢」補上）"}
                  </div>
                  <div className="text-xs text-muted-foreground">單字仍留在畫面上方，不會被蓋掉</div>
                </div>
              )}
            </Card>

            {!revealed ? (
              <Button variant="outline" className="w-full max-w-md" onClick={() => setRevealed(true)}>
                顯示答案<span className="ml-1 text-xs text-muted-foreground">(空白鍵)</span>
              </Button>
            ) : (
              <div className="grid w-full max-w-md grid-cols-4 gap-2.5">
                {GRADES.map(({ grade, label, key, className }) => (
                  <button
                    key={grade}
                    type="button"
                    disabled={submitting}
                    onClick={() => handleGrade(grade)}
                    className={`flex h-14 flex-col items-center justify-center gap-0.5 rounded-lg border border-border bg-card font-semibold disabled:pointer-events-none disabled:opacity-50 ${className}`}
                  >
                    {label}
                    <span className="text-[11px] font-normal text-muted-foreground">{key}</span>
                  </button>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
