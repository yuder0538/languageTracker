import { useEffect, useState } from "react"
import { toast } from "sonner"
import { PlusIcon, RotateCcwIcon, SearchIcon, Loader2Icon, Volume2Icon, PencilIcon } from "lucide-react"

import { AppRail } from "@/components/app-rail"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Field, FieldLabel, FieldDescription, FieldError } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table"
import { ApiError } from "@/lib/api"
import { useLanguage } from "@/lib/language-context"
import { useApi } from "@/hooks/use-api"
import {
  createVocabulary,
  enrichDeTranslation,
  enrichEnDictionary,
  fetchMediaLogs,
  fetchVocabulary,
  updateVocabulary,
  type VocabularyRead,
} from "@/lib/dashboard-api"

const PART_OF_SPEECH_OPTIONS = ["名詞", "動詞", "形容詞", "副詞", "介係詞", "其他"]
const DE_ARTIKEL_OPTIONS = ["der", "die", "das"] as const

function formatDateTime(iso: string) {
  return iso.slice(0, 10)
}

/**
 * Browser-native TTS (Web Speech API) — no backend call, no new dependency.
 * Machine-synthesized, not a real recording; good enough for a quick check,
 * revisit with a real dictionary-audio source later if that matters more.
 */
function speak(text: string, language: "en" | "de", onEnd: () => void) {
  if (!("speechSynthesis" in window)) {
    toast.error("這個瀏覽器不支援語音朗讀")
    return
  }
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = language === "de" ? "de-DE" : "en-US"
  utterance.onend = onEnd
  utterance.onerror = onEnd
  window.speechSynthesis.speak(utterance)
}

function WordDialog({
  open,
  onOpenChange,
  onSaved,
  editingWord,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved: () => void
  editingWord: VocabularyRead | null
}) {
  const { language } = useLanguage()
  const mediaLogs = useApi(() => fetchMediaLogs(language), [language])
  const isEditing = editingWord !== null

  const [headword, setHeadword] = useState("")
  const [headwordTouched, setHeadwordTouched] = useState(false)
  const [partOfSpeech, setPartOfSpeech] = useState<string>("")
  const [deArtikel, setDeArtikel] = useState<string>("")
  const [translationZh, setTranslationZh] = useState("")
  const [mediaLogId, setMediaLogId] = useState<string>("")
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const headwordError = headwordTouched && headword.trim() === "" ? "單字為必填欄位" : ""

  // Reset (create) or prefill (edit) the form every time the dialog opens.
  useEffect(() => {
    if (!open) return
    setHeadword(editingWord?.headword ?? "")
    setHeadwordTouched(false)
    setPartOfSpeech(editingWord?.part_of_speech ?? "")
    setDeArtikel(editingWord?.de_artikel ?? "")
    setTranslationZh(editingWord?.translation_zh ?? "")
    setMediaLogId(editingWord?.media_log_id ? String(editingWord.media_log_id) : "")
    setNotes(editingWord?.notes ?? "")
  }, [open, editingWord])

  async function handleSubmit() {
    setHeadwordTouched(true)
    if (headword.trim() === "") return

    setSubmitting(true)
    try {
      const fields = {
        headword: headword.trim(),
        part_of_speech: partOfSpeech || null,
        de_artikel: language === "de" && deArtikel ? (deArtikel as "der" | "die" | "das") : null,
        translation_zh: translationZh.trim() || null,
        media_log_id: mediaLogId ? Number(mediaLogId) : null,
        notes: notes.trim() || null,
      }
      if (isEditing) {
        await updateVocabulary(editingWord.id, fields)
        toast.success(`已更新「${headword.trim()}」`)
      } else {
        await createVocabulary({ language, ...fields })
        toast.success(`已新增「${headword.trim()}」`)
      }
      onOpenChange(false)
      onSaved()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : isEditing ? "更新失敗，請重試" : "新增失敗，請重試"
      toast.error(message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!submitting) onOpenChange(next)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEditing ? "編輯單字" : "新增單字"}</DialogTitle>
          <DialogDescription>目前語言視角：{language === "de" ? "Deutsch" : "English"}</DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <Field>
            <FieldLabel htmlFor="headword">單字 *</FieldLabel>
            <Input
              id="headword"
              placeholder={language === "de" ? "例如：das Fenster" : "e.g. window"}
              value={headword}
              aria-invalid={!!headwordError}
              onChange={(e) => setHeadword(e.target.value)}
              onBlur={() => setHeadwordTouched(true)}
              disabled={submitting}
            />
            <FieldError>{headwordError}</FieldError>
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field>
              <FieldLabel htmlFor="pos">詞性</FieldLabel>
              <Select value={partOfSpeech} onValueChange={setPartOfSpeech} disabled={submitting}>
                <SelectTrigger id="pos" className="w-full">
                  <SelectValue placeholder="不指定" />
                </SelectTrigger>
                <SelectContent>
                  {PART_OF_SPEECH_OPTIONS.map((opt) => (
                    <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            {language === "de" && (
              <Field>
                <FieldLabel htmlFor="artikel">冠詞</FieldLabel>
                <Select value={deArtikel} onValueChange={setDeArtikel} disabled={submitting}>
                  <SelectTrigger id="artikel" className="w-full">
                    <SelectValue placeholder="不指定" />
                  </SelectTrigger>
                  <SelectContent>
                    {DE_ARTIKEL_OPTIONS.map((opt) => (
                      <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Field>
            )}
          </div>

          <Field>
            <FieldLabel htmlFor="translation">翻譯</FieldLabel>
            <Input
              id="translation"
              placeholder="中文翻譯（選填，之後可用自動翻譯補上）"
              value={translationZh}
              onChange={(e) => setTranslationZh(e.target.value)}
              disabled={submitting}
            />
          </Field>

          <Field>
            <FieldLabel htmlFor="media-log">來源劇集（選填）</FieldLabel>
            {mediaLogs.status === "success" && mediaLogs.data.length === 0 ? (
              <Select disabled>
                <SelectTrigger id="media-log" className="w-full">
                  <SelectValue placeholder="尚無追劇紀錄" />
                </SelectTrigger>
                <SelectContent />
              </Select>
            ) : (
              <Select
                value={mediaLogId}
                onValueChange={setMediaLogId}
                disabled={submitting || mediaLogs.status !== "success"}
              >
                <SelectTrigger id="media-log" className="w-full">
                  <SelectValue placeholder="不指定" />
                </SelectTrigger>
                <SelectContent>
                  {mediaLogs.status === "success" &&
                    mediaLogs.data.map((log) => (
                      <SelectItem key={log.id} value={String(log.id)}>
                        {log.title}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            )}
          </Field>

          <Field>
            <FieldLabel htmlFor="notes">備註</FieldLabel>
            <Input
              id="notes"
              placeholder="選填"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={submitting}
            />
            <FieldDescription>可在列表點「自動查詢」圖示，回填音標/解釋（英文）或翻譯（德文），翻錯了也能回來這裡手動修正。</FieldDescription>
          </Field>
        </div>

        <DialogFooter>
          <DialogClose render={<Button variant="outline" disabled={submitting}>取消</Button>} />
          <Button loading={submitting} onClick={handleSubmit}>
            {isEditing ? "儲存" : "新增"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function Vocabulary() {
  const { language } = useLanguage()
  const vocabulary = useApi(() => fetchVocabulary(language), [language])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingWord, setEditingWord] = useState<VocabularyRead | null>(null)
  const [enrichingIds, setEnrichingIds] = useState<Set<number>>(new Set())
  const [speakingId, setSpeakingId] = useState<number | null>(null)

  const list: VocabularyRead[] = vocabulary.status === "success" ? vocabulary.data : []

  function openCreateDialog() {
    setEditingWord(null)
    setDialogOpen(true)
  }

  function openEditDialog(word: VocabularyRead) {
    setEditingWord(word)
    setDialogOpen(true)
  }

  function handleSpeak(word: VocabularyRead) {
    setSpeakingId(word.id)
    speak(word.headword, word.language, () => setSpeakingId(null))
  }

  async function handleEnrich(word: VocabularyRead) {
    setEnrichingIds((prev) => new Set(prev).add(word.id))
    try {
      await (language === "de" ? enrichDeTranslation(word.id) : enrichEnDictionary(word.id))
      toast.success(`已更新「${word.headword}」`)
      vocabulary.retry()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "自動查詢失敗，請重試"
      toast.error(message)
    } finally {
      setEnrichingIds((prev) => {
        const next = new Set(prev)
        next.delete(word.id)
        return next
      })
    }
  }

  return (
    <div className="flex min-h-screen">
      <AppRail />
      <main className="flex flex-1 flex-col gap-5 p-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading text-2xl font-semibold">單字庫</h1>
            <p className="text-sm text-muted-foreground">
              {language === "de" ? "Deutsch" : "English"}
              {vocabulary.status === "success" && ` · 共 ${list.length} 個單字`}
            </p>
          </div>
          <Button onClick={openCreateDialog}>
            <PlusIcon /> 新增單字
          </Button>
        </div>

        {vocabulary.status === "loading" && (
          <div className="flex flex-col gap-2">
            <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
            <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
            <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
          </div>
        )}

        {vocabulary.status === "error" && (
          <div className="flex flex-col items-start gap-2 text-sm text-destructive">
            <span>讀取失敗：{vocabulary.message}</span>
            <Button variant="outline" size="sm" onClick={vocabulary.retry}>
              <RotateCcwIcon /> 重試
            </Button>
          </div>
        )}

        {vocabulary.status === "success" && list.length === 0 && (
          <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-border p-8 text-sm text-muted-foreground">
            還沒有任何單字，新增第一個吧。
            <Button onClick={openCreateDialog}>
              <PlusIcon /> 新增單字
            </Button>
          </div>
        )}

        {vocabulary.status === "success" && list.length > 0 && (
          <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>單字</TableHead>
                  <TableHead>詞性</TableHead>
                  <TableHead>翻譯</TableHead>
                  <TableHead>冠詞</TableHead>
                  <TableHead>建立時間</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {list.map((word) => {
                  const isEnriching = enrichingIds.has(word.id)
                  return (
                    <TableRow key={word.id}>
                      <TableCell className="font-medium">
                        <span className="inline-flex items-center gap-1.5">
                          {word.headword}
                          <button
                            type="button"
                            onClick={() => handleSpeak(word)}
                            aria-label={`朗讀「${word.headword}」`}
                            className={`text-muted-foreground hover:text-foreground ${
                              speakingId === word.id ? "text-primary" : ""
                            }`}
                          >
                            <Volume2Icon className="size-3.5" />
                          </button>
                        </span>
                        {word.ipa && (
                          <span className="ml-2 font-mono text-xs text-muted-foreground">/{word.ipa}/</span>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">{word.part_of_speech ?? "—"}</TableCell>
                      <TableCell
                        className="max-w-[256px] truncate text-muted-foreground"
                        title={word.translation_zh ?? word.en_definition ?? undefined}
                      >
                        {word.translation_zh ?? "—"}
                      </TableCell>
                      <TableCell>
                        {word.de_artikel ? <Badge variant="secondary">{word.de_artikel}</Badge> : "—"}
                      </TableCell>
                      <TableCell className="font-mono text-muted-foreground">
                        {formatDateTime(word.created_at)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          onClick={() => openEditDialog(word)}
                          aria-label={`編輯「${word.headword}」`}
                        >
                          <PencilIcon />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon-sm"
                          disabled={isEnriching}
                          onClick={() => handleEnrich(word)}
                          aria-label={`自動查詢「${word.headword}」`}
                        >
                          {isEnriching ? (
                            <Loader2Icon className="animate-spin" />
                          ) : (
                            <SearchIcon />
                          )}
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </main>

      <WordDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSaved={vocabulary.retry}
        editingWord={editingWord}
      />
    </div>
  )
}
