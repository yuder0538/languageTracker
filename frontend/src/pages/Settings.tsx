import { useEffect, useState } from "react"
import { toast } from "sonner"
import { RotateCcwIcon } from "lucide-react"

import { AppRail } from "@/components/app-rail"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Field, FieldLabel, FieldDescription, FieldError } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { ApiError } from "@/lib/api"
import { useApi } from "@/hooks/use-api"
import { fetchSettings, updateSettings } from "@/lib/dashboard-api"

function parseLimit(value: string): number | null {
  if (!/^\d+$/.test(value.trim())) return null
  const n = Number(value)
  return n >= 1 && n <= 500 ? n : null
}

export default function Settings() {
  const settings = useApi(() => fetchSettings(), [])

  const [inputValue, setInputValue] = useState("")
  const [touched, setTouched] = useState(false)
  const [saving, setSaving] = useState(false)

  const fetchedLimit = settings.status === "success" ? settings.data.daily_new_card_limit : null
  useEffect(() => {
    if (fetchedLimit !== null) setInputValue(String(fetchedLimit))
  }, [fetchedLimit])

  const validationError = touched && parseLimit(inputValue) === null ? "請輸入 1～500 之間的整數" : ""

  async function handleSave() {
    setTouched(true)
    const limit = parseLimit(inputValue)
    if (limit === null) return

    setSaving(true)
    try {
      const updated = await updateSettings({ daily_new_card_limit: limit })
      setInputValue(String(updated.daily_new_card_limit))
      toast.success("已儲存")
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "儲存失敗，請重試")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-screen">
      <AppRail />

      <main className="flex flex-1 flex-col items-center gap-6 p-8">
        <div className="w-full max-w-[480px]">
          <div className="text-xs tracking-wide text-muted-foreground uppercase">設定</div>
          <h1 className="text-2xl font-semibold">設定與偏好</h1>
          <p className="mt-2 text-sm text-muted-foreground">調整複習與系統行為，目前只有一個項目，之後會陸續加入更多設定。</p>
        </div>

        {settings.status === "loading" && (
          <Card className="w-full max-w-[480px] p-6">
            <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
          </Card>
        )}

        {settings.status === "error" && (
          <Card className="w-full max-w-[480px] p-6">
            <div className="flex flex-col items-start gap-2 text-sm text-destructive">
              <span>讀取失敗：{settings.message}</span>
              <Button variant="outline" size="sm" onClick={settings.retry}>
                <RotateCcwIcon /> 重試
              </Button>
            </div>
          </Card>
        )}

        {settings.status === "success" && (
          <Card className="w-full max-w-[480px] gap-5 p-6">
            <Field>
              <FieldLabel htmlFor="daily-new-card-limit">每日新卡引入上限</FieldLabel>
              <FieldDescription>複習佇列每天最多引入幾張全新單字（不影響已到期需複習的舊卡）。</FieldDescription>
              <Input
                id="daily-new-card-limit"
                inputMode="numeric"
                className="w-32 font-mono"
                value={inputValue}
                aria-invalid={!!validationError}
                onChange={(e) => setInputValue(e.target.value)}
                onBlur={() => setTouched(true)}
                disabled={saving}
              />
              <FieldError>{validationError}</FieldError>
            </Field>

            <Button onClick={handleSave} disabled={saving} className="self-start">
              {saving ? "儲存中…" : "儲存"}
            </Button>
          </Card>
        )}
      </main>
    </div>
  )
}
