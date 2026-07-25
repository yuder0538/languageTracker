import { useEffect, useState } from "react"
import { toast } from "sonner"
import { PlusIcon, RotateCcwIcon, PencilIcon, TrashIcon } from "lucide-react"

import { AppRail } from "@/components/app-rail"
import { Button } from "@/components/ui/button"
import { Field, FieldLabel, FieldError } from "@/components/ui/field"
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
  createMediaLog,
  deleteMediaLog,
  fetchMediaLogs,
  updateMediaLog,
  type MediaLogRead,
} from "@/lib/dashboard-api"

const MEDIA_TYPE_OPTIONS = ["影集", "電影", "紀錄片", "其他"]

function todayIso() {
  return new Date().toISOString().slice(0, 10)
}

function MediaLogDialog({
  open,
  onOpenChange,
  onSaved,
  editingLog,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved: () => void
  editingLog: MediaLogRead | null
}) {
  const { language } = useLanguage()
  const isEditing = editingLog !== null

  const [title, setTitle] = useState("")
  const [titleTouched, setTitleTouched] = useState(false)
  const [mediaType, setMediaType] = useState(MEDIA_TYPE_OPTIONS[0])
  const [watchedDate, setWatchedDate] = useState(todayIso())
  const [durationMinutes, setDurationMinutes] = useState("")
  const [notes, setNotes] = useState("")
  const [submitting, setSubmitting] = useState(false)

  const titleError = titleTouched && title.trim() === "" ? "劇名為必填欄位" : ""
  const durationError =
    titleTouched && (durationMinutes === "" || Number(durationMinutes) < 0)
      ? "觀看時長為必填，且不能是負數"
      : ""

  useEffect(() => {
    if (!open) return
    setTitle(editingLog?.title ?? "")
    setTitleTouched(false)
    setMediaType(editingLog?.media_type ?? MEDIA_TYPE_OPTIONS[0])
    setWatchedDate(editingLog?.watched_date ?? todayIso())
    setDurationMinutes(editingLog ? String(editingLog.duration_minutes) : "")
    setNotes(editingLog?.notes ?? "")
  }, [open, editingLog])

  async function handleSubmit() {
    setTitleTouched(true)
    if (title.trim() === "" || durationMinutes === "" || Number(durationMinutes) < 0) return

    setSubmitting(true)
    try {
      const fields = {
        title: title.trim(),
        media_type: mediaType,
        watched_date: watchedDate,
        duration_minutes: Number(durationMinutes),
        notes: notes.trim() || null,
      }
      if (isEditing) {
        await updateMediaLog(editingLog.id, fields)
        toast.success(`已更新「${title.trim()}」`)
      } else {
        await createMediaLog({ language, ...fields })
        toast.success(`已新增「${title.trim()}」`)
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
          <DialogTitle>{isEditing ? "編輯追劇紀錄" : "新增追劇紀錄"}</DialogTitle>
          <DialogDescription>目前語言視角：{language === "de" ? "Deutsch" : "English"}</DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <Field>
            <FieldLabel htmlFor="title">劇名 *</FieldLabel>
            <Input
              id="title"
              placeholder={language === "de" ? "例如：Dark" : "e.g. Friends"}
              value={title}
              aria-invalid={!!titleError}
              onChange={(e) => setTitle(e.target.value)}
              onBlur={() => setTitleTouched(true)}
              disabled={submitting}
            />
            <FieldError>{titleError}</FieldError>
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field>
              <FieldLabel htmlFor="media-type">類型</FieldLabel>
              <Select value={mediaType} onValueChange={setMediaType} disabled={submitting}>
                <SelectTrigger id="media-type" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {MEDIA_TYPE_OPTIONS.map((opt) => (
                    <SelectItem key={opt} value={opt}>{opt}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field>
              <FieldLabel htmlFor="watched-date">觀看日期</FieldLabel>
              <Input
                id="watched-date"
                type="date"
                value={watchedDate}
                onChange={(e) => setWatchedDate(e.target.value)}
                disabled={submitting}
              />
            </Field>
          </div>

          <Field>
            <FieldLabel htmlFor="duration">觀看時長（分鐘） *</FieldLabel>
            <Input
              id="duration"
              type="number"
              min={0}
              placeholder="例如：22"
              value={durationMinutes}
              aria-invalid={!!durationError}
              onChange={(e) => setDurationMinutes(e.target.value)}
              onBlur={() => setTitleTouched(true)}
              disabled={submitting}
            />
            <FieldError>{durationError}</FieldError>
          </Field>

          <Field>
            <FieldLabel htmlFor="notes">備註</FieldLabel>
            <Input
              id="notes"
              placeholder="選填，例如集數"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              disabled={submitting}
            />
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

function DeleteConfirmDialog({
  log,
  onOpenChange,
  onDeleted,
}: {
  log: MediaLogRead | null
  onOpenChange: (open: boolean) => void
  onDeleted: () => void
}) {
  const [deleting, setDeleting] = useState(false)

  async function handleConfirm() {
    if (!log) return
    setDeleting(true)
    try {
      await deleteMediaLog(log.id)
      toast.success(`已刪除「${log.title}」`)
      onOpenChange(false)
      onDeleted()
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "刪除失敗，請重試"
      toast.error(message)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Dialog open={log !== null} onOpenChange={(next) => { if (!deleting) onOpenChange(next) }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>確定要刪除「{log?.title}」？</DialogTitle>
          <DialogDescription>這個動作無法復原，關聯的字幕資料也會一併刪除。</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose render={<Button variant="outline" disabled={deleting}>取消</Button>} />
          <Button variant="destructive" loading={deleting} onClick={handleConfirm}>
            確定刪除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function MediaLog() {
  const { language } = useLanguage()
  const mediaLogs = useApi(() => fetchMediaLogs(language), [language])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingLog, setEditingLog] = useState<MediaLogRead | null>(null)
  const [deletingLog, setDeletingLog] = useState<MediaLogRead | null>(null)

  const list: MediaLogRead[] = mediaLogs.status === "success" ? mediaLogs.data : []

  function openCreateDialog() {
    setEditingLog(null)
    setDialogOpen(true)
  }

  function openEditDialog(log: MediaLogRead) {
    setEditingLog(log)
    setDialogOpen(true)
  }

  return (
    <div className="flex min-h-screen">
      <AppRail />
      <main className="flex flex-1 flex-col gap-5 p-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="font-heading text-2xl font-semibold">追劇紀錄</h1>
            <p className="text-sm text-muted-foreground">
              {language === "de" ? "Deutsch" : "English"}
              {mediaLogs.status === "success" && ` · 共 ${list.length} 筆紀錄`}
            </p>
          </div>
          <Button onClick={openCreateDialog}>
            <PlusIcon /> 新增追劇紀錄
          </Button>
        </div>

        {mediaLogs.status === "loading" && (
          <div className="flex flex-col gap-2">
            <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
            <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
            <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
          </div>
        )}

        {mediaLogs.status === "error" && (
          <div className="flex flex-col items-start gap-2 text-sm text-destructive">
            <span>讀取失敗：{mediaLogs.message}</span>
            <Button variant="outline" size="sm" onClick={mediaLogs.retry}>
              <RotateCcwIcon /> 重試
            </Button>
          </div>
        )}

        {mediaLogs.status === "success" && list.length === 0 && (
          <div className="flex flex-col items-start gap-3 rounded-xl border border-dashed border-border p-8 text-sm text-muted-foreground">
            還沒有追劇紀錄，新增第一筆吧。
            <Button onClick={openCreateDialog}>
              <PlusIcon /> 新增追劇紀錄
            </Button>
          </div>
        )}

        {mediaLogs.status === "success" && list.length > 0 && (
          <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>劇名</TableHead>
                  <TableHead>類型</TableHead>
                  <TableHead>觀看日期</TableHead>
                  <TableHead>時長</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {list.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium">{log.title}</TableCell>
                    <TableCell className="text-muted-foreground">{log.media_type}</TableCell>
                    <TableCell className="font-mono text-muted-foreground">{log.watched_date}</TableCell>
                    <TableCell className="font-mono text-muted-foreground">{log.duration_minutes} 分鐘</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => openEditDialog(log)}
                        aria-label={`編輯「${log.title}」`}
                      >
                        <PencilIcon />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        onClick={() => setDeletingLog(log)}
                        aria-label={`刪除「${log.title}」`}
                      >
                        <TrashIcon className="text-destructive" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </main>

      <MediaLogDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onSaved={mediaLogs.retry}
        editingLog={editingLog}
      />
      <DeleteConfirmDialog
        log={deletingLog}
        onOpenChange={(open) => { if (!open) setDeletingLog(null) }}
        onDeleted={mediaLogs.retry}
      />
    </div>
  )
}
