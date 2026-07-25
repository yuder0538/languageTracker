import { useState } from "react"
import { toast } from "sonner"
import { PlusIcon, RotateCcwIcon } from "lucide-react"

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
  fetchMediaLogs,
  fetchVocabulary,
  type VocabularyRead,
} from "@/lib/dashboard-api"

const PART_OF_SPEECH_OPTIONS = ["名詞", "動詞", "形容詞", "副詞", "介係詞", "其他"]
const DE_ARTIKEL_OPTIONS = ["der", "die", "das"] as const

function formatDateTime(iso: string) {
  return iso.slice(0, 10)
}

function AddWordDialog({
  open,
  onOpenChange,
  onCreated,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: () => void
}) {
  const { language } = useLanguage()
  const mediaLogs = useApi(() => fetchMediaLogs(language), [language])

  const [headword, setHeadword] = useState("")
  const [headwordTouched, setHeadwordTouched] = useState(false)
  const [partOfSpeech, setPartOfSpeech] = useState<string>("")
  const [deArtikel, setDeArtikel] = useState<string>("")
  const [translationZh, setTranslationZh] = useState("")
  const [mediaLogId, setMediaLogId] = useState<string>("")
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const headwordError = headwordTouched && headword.trim() === "" ? "單字為必填欄位" : ""

  function reset() {
    setHeadword("")
    setHeadwordTouched(false)
    setPartOfSpeech("")
    setDeArtikel("")
    setTranslationZh("")
    setMediaLogId("")
    setNotes("")
  }

  async function handleSubmit() {
    setHeadwordTouched(true)
    if (headword.trim() === "") return

    setSubmitting(true)
    try {
      await createVocabulary({
        language,
        headword: headword.trim(),
        part_of_speech: partOfSpeech || null,
        de_artikel: language === "de" && deArtikel ? (deArtikel as "der" | "die" | "das") : null,
        translation_zh: translationZh.trim() || null,
        media_log_id: mediaLogId ? Number(mediaLogId) : null,
        notes: notes.trim() || null,
      })
      toast.success(`已新增「${headword.trim()}」`)
      reset()
      onOpenChange(false)
      onCreated()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "新增失敗，請重試"
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
          <DialogTitle>新增單字</DialogTitle>
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
            <FieldDescription>例句與音標之後可用「自動查字典」功能補上（尚未實作）。</FieldDescription>
          </Field>
        </div>

        <DialogFooter>
          <DialogClose render={<Button variant="outline" disabled={submitting}>取消</Button>} />
          <Button loading={submitting} onClick={handleSubmit}>
            新增
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

  const list: VocabularyRead[] = vocabulary.status === "success" ? vocabulary.data : []

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
          <Button onClick={() => setDialogOpen(true)}>
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
            <Button onClick={() => setDialogOpen(true)}>
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
                  <TableHead className="text-right">建立時間</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {list.map((word) => (
                  <TableRow key={word.id}>
                    <TableCell className="font-medium">{word.headword}</TableCell>
                    <TableCell className="text-muted-foreground">{word.part_of_speech ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">{word.translation_zh ?? "—"}</TableCell>
                    <TableCell>
                      {word.de_artikel ? <Badge variant="secondary">{word.de_artikel}</Badge> : "—"}
                    </TableCell>
                    <TableCell className="text-right font-mono text-muted-foreground">
                      {formatDateTime(word.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </main>

      <AddWordDialog open={dialogOpen} onOpenChange={setDialogOpen} onCreated={vocabulary.retry} />
    </div>
  )
}
