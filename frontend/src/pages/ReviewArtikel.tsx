import { useEffect, useState } from "react"
import { toast } from "sonner"
import { XIcon, RotateCcwIcon, CheckIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { ReviewModeSwitch } from "@/components/review-mode-switch"
import { ApiError } from "@/lib/api"
import { useLanguage } from "@/lib/language-context"
import { useRouter } from "@/lib/router"
import { useApi } from "@/hooks/use-api"
import { fetchReviewQueue, submitArtikelQuiz } from "@/lib/dashboard-api"

type Artikel = "der" | "die" | "das"

const ARTIKEL_OPTIONS: Artikel[] = ["der", "die", "das"]

function stripArtikel(headword: string) {
  return headword.replace(/^(der|die|das)\s+/i, "")
}

interface Feedback {
  picked: Artikel
  correct: boolean
  correctAnswer: Artikel
}

export default function ReviewArtikel() {
  const { language, setLanguage } = useLanguage()
  const { navigate } = useRouter()
  const queue = useApi(() => fetchReviewQueue(language, "artikel"), [language])

  const [index, setIndex] = useState(0)
  const [feedback, setFeedback] = useState<Feedback | null>(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    setIndex(0)
    setFeedback(null)
  }, [language])

  // Artikel quiz is German-only (backend rejects it for English); land here
  // via nav/back-button with language=en and switch to German automatically
  // rather than showing a dead end.
  useEffect(() => {
    if (language !== "de") setLanguage("de")
  }, [language, setLanguage])

  const cards = queue.status === "success" ? queue.data : []
  const total = cards.length
  const current = cards[index]

  async function handleAnswer(answer: Artikel) {
    if (!current || submitting || feedback) return
    setSubmitting(true)
    try {
      const result = await submitArtikelQuiz(current.id, answer)
      setFeedback({ picked: answer, correct: result.correct, correctAnswer: result.correct_answer })
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "送出失敗，請重試"
      toast.error(message)
    } finally {
      setSubmitting(false)
    }
  }

  function handleNext() {
    setIndex((i) => i + 1)
    setFeedback(null)
  }

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (!current) return
      if (feedback) {
        if (e.key === " " || e.key === "Enter") {
          e.preventDefault()
          handleNext()
        }
        return
      }
      if (submitting) return
      const optionIndex = ["1", "2", "3"].indexOf(e.key)
      if (optionIndex >= 0) handleAnswer(ARTIKEL_OPTIONS[optionIndex])
    }
    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [current, feedback, submitting])

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
        <span className="w-10" />
      </div>

      <div className="flex justify-center pb-2">
        <ReviewModeSwitch mode="artikel" />
      </div>

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
            <p className="text-lg font-medium">今天沒有待複習的冠詞卡片</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              只有標注了冠詞（der／die／das）的德文名詞才會出現在這裡。
            </p>
            <Button onClick={() => navigate("/")}>回 Dashboard</Button>
          </div>
        )}

        {queue.status === "success" && total > 0 && index >= total && (
          <div className="flex flex-col items-center gap-4 text-center">
            <p className="text-2xl font-semibold">冠詞複習完成！🎉</p>
            <p className="text-sm text-muted-foreground">共複習了 {total} 張卡片</p>
            <Button onClick={() => navigate("/")}>回 Dashboard</Button>
          </div>
        )}

        {queue.status === "success" && current && (
          <>
            <Card className="flex w-full max-w-md flex-col items-center gap-2 p-8 text-center">
              <div className="text-4xl font-semibold">{stripArtikel(current.headword)}</div>
              {current.part_of_speech && (
                <div className="mt-1 text-sm text-muted-foreground">{current.part_of_speech}</div>
              )}
              {feedback && (
                <div
                  className={`mt-4 flex items-center gap-1.5 text-sm font-medium ${
                    feedback.correct ? "text-success" : "text-destructive"
                  }`}
                >
                  {feedback.correct ? <CheckIcon className="size-4" /> : <XIcon className="size-4" />}
                  {feedback.correct ? "答對了！" : `答錯了，正確答案是 ${feedback.correctAnswer}`}
                </div>
              )}
            </Card>

            {!feedback ? (
              <div className="grid w-full max-w-md grid-cols-3 gap-2.5">
                {ARTIKEL_OPTIONS.map((option, i) => (
                  <button
                    key={option}
                    type="button"
                    disabled={submitting}
                    onClick={() => handleAnswer(option)}
                    className="flex h-14 flex-col items-center justify-center gap-0.5 rounded-lg border border-border bg-card font-semibold disabled:pointer-events-none disabled:opacity-50"
                  >
                    {option}
                    <span className="text-[11px] font-normal text-muted-foreground">{i + 1}</span>
                  </button>
                ))}
              </div>
            ) : (
              <div className="grid w-full max-w-md grid-cols-3 gap-2.5">
                {ARTIKEL_OPTIONS.map((option) => {
                  const isCorrectAnswer = option === feedback.correctAnswer
                  const isPicked = option === feedback.picked
                  return (
                    <div
                      key={option}
                      className={`flex h-14 flex-col items-center justify-center rounded-lg border font-semibold ${
                        isCorrectAnswer
                          ? "border-success bg-success/10 text-success"
                          : isPicked
                            ? "border-destructive bg-destructive/10 text-destructive"
                            : "border-border bg-card text-muted-foreground opacity-50"
                      }`}
                    >
                      {option}
                    </div>
                  )
                })}
              </div>
            )}

            {feedback && (
              <Button className="w-full max-w-md" onClick={handleNext}>
                下一張<span className="ml-1 text-xs text-muted-foreground">(空白鍵)</span>
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  )
}
