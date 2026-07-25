import { useState, type ReactNode } from "react"
import { useTheme } from "next-themes"
import { toast } from "sonner"
import {
  MoonIcon,
  SunIcon,
  PlusIcon,
  TrashIcon,
  FlameIcon,
  BookOpenIcon,
  ClapperboardIcon,
  LayoutDashboardIcon,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Field, FieldLabel, FieldDescription, FieldError } from "@/components/ui/field"
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardAction,
  CardContent,
  CardFooter,
} from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table"
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu"
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"

function Section({
  title,
  description,
  children,
}: {
  title: string
  description: string
  children: ReactNode
}) {
  return (
    <section className="flex flex-col gap-4">
      <div>
        <h2 className="font-heading text-lg font-semibold">{title}</h2>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {children}
    </section>
  )
}

function ButtonShowcase() {
  const [loading, setLoading] = useState(false)

  function handleSave() {
    setLoading(true)
    window.setTimeout(() => setLoading(false), 1500)
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="default">預設 default</Button>
        <Button variant="outline">外框 outline</Button>
        <Button variant="secondary">次要 secondary</Button>
        <Button variant="ghost">幽靈 ghost</Button>
        <Button variant="destructive">
          <TrashIcon /> 刪除 destructive
        </Button>
        <Button variant="link">連結 link</Button>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button size="xs">xs</Button>
        <Button size="sm">sm</Button>
        <Button size="default">default</Button>
        <Button size="lg">lg</Button>
        <Button size="icon" aria-label="新增">
          <PlusIcon />
        </Button>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <Button disabled>停用 disabled</Button>
        <Button loading={loading} onClick={handleSave}>
          {loading ? "儲存中" : "點擊觸發載入 loading"}
        </Button>
        <Button variant="outline">Tab 至此看 focus 態</Button>
      </div>
    </div>
  )
}

function FormShowcase() {
  const [word, setWord] = useState("")
  const [touched, setTouched] = useState(false)
  const error = touched && word.trim() === "" ? "單字為必填欄位" : ""

  return (
    <Card className="max-w-md">
      <CardHeader>
        <CardTitle>新增單字</CardTitle>
        <CardDescription>示範 Field／Input／Select／Checkbox 的整合用法</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Field>
          <FieldLabel htmlFor="word">德文單字</FieldLabel>
          <Input
            id="word"
            placeholder="例如：der Tisch"
            value={word}
            aria-invalid={!!error}
            onChange={(e) => setWord(e.target.value)}
            onBlur={() => setTouched(true)}
          />
          <FieldError>{error}</FieldError>
          {!error && <FieldDescription>含冠詞一起輸入（der／die／das）</FieldDescription>}
        </Field>

        <Field>
          <FieldLabel htmlFor="lang">語言</FieldLabel>
          <Select defaultValue="de">
            <SelectTrigger id="lang" className="w-full">
              <SelectValue placeholder="選擇語言" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="de">Deutsch</SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <Field>
          <Select disabled defaultValue="de">
            <SelectTrigger className="w-full" aria-label="停用狀態的語言選單">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="de">Deutsch（停用示範）</SelectItem>
            </SelectContent>
          </Select>
        </Field>

        <div className="flex items-center gap-2">
          <Checkbox id="known" defaultChecked />
          <Label htmlFor="known">已認識這個單字</Label>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox id="leech" disabled />
          <Label htmlFor="leech">Leech 標記（系統自動判定，不可手動勾選）</Label>
        </div>
        <div className="flex items-center gap-2">
          <Checkbox id="confirm" aria-invalid />
          <Label htmlFor="confirm">我確認這筆單字的詞性標註正確（未勾選視為錯誤）</Label>
        </div>
      </CardContent>
      <CardFooter className="justify-end gap-2">
        <Button variant="outline">取消</Button>
        <Button onClick={() => setTouched(true)}>儲存</Button>
      </CardFooter>
    </Card>
  )
}

function CardShowcase() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>der Tisch</CardTitle>
          <CardDescription>桌子 · 陽性名詞</CardDescription>
          <CardAction>
            <Badge variant="secondary">到期複習</Badge>
          </CardAction>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <p className="font-mono text-sm text-muted-foreground">/tɪʃ/</p>
          <p className="text-sm">
            複數：<span className="font-mono">die Tische</span>
          </p>
          <p className="text-sm text-muted-foreground">
            例句：Das Buch liegt auf dem <span className="text-foreground">Tisch</span>.
          </p>
        </CardContent>
        <CardFooter className="justify-between text-xs text-muted-foreground">
          <span>連續答對 4 次</span>
          <span className="font-mono">下次複習：2026-07-27</span>
        </CardFooter>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Friends</CardTitle>
          <CardDescription>S3E12 · 英文</CardDescription>
          <CardAction>
            <Badge variant="success">已完成</Badge>
          </CardAction>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <p className="text-sm text-muted-foreground">觀看時長 22 分鐘，新增 6 個單字</p>
          <div className="flex gap-1.5">
            <Badge variant="outline">Sitcom</Badge>
            <Badge variant="outline">B2</Badge>
          </div>
        </CardContent>
        <CardFooter className="justify-between text-xs text-muted-foreground">
          <span>2026-07-24</span>
          <span className="font-mono">Season 3 · Episode 12</span>
        </CardFooter>
      </Card>
    </div>
  )
}

function TableShowcase() {
  const rows = [
    { word: "der Tisch", type: "名詞", due: "2026-07-27", status: "到期", variant: "warning" as const },
    { word: "laufen", type: "動詞", due: "2026-07-30", status: "排程中", variant: "secondary" as const },
    { word: "die Freiheit", type: "名詞", due: "2026-07-20", status: "Leech", variant: "destructive" as const },
    { word: "schnell", type: "形容詞", due: "2026-08-02", status: "已學會", variant: "success" as const },
  ]

  return (
    <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>單字</TableHead>
            <TableHead>詞性</TableHead>
            <TableHead>下次複習</TableHead>
            <TableHead className="text-right">狀態</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.word}>
              <TableCell className="font-medium">{row.word}</TableCell>
              <TableCell className="text-muted-foreground">{row.type}</TableCell>
              <TableCell className="font-mono text-muted-foreground">{row.due}</TableCell>
              <TableCell className="text-right">
                <Badge variant={row.variant}>{row.status}</Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function NavShowcase() {
  const items = [
    { label: "Dashboard", icon: LayoutDashboardIcon, active: true },
    { label: "單字庫", icon: BookOpenIcon, active: false },
    { label: "追劇紀錄", icon: ClapperboardIcon, active: false },
  ]

  return (
    <NavigationMenu className="max-w-none justify-start">
      <NavigationMenuList className="justify-start gap-1">
        {items.map(({ label, icon: Icon, active }) => (
          <NavigationMenuItem key={label}>
            <NavigationMenuLink data-active={active || undefined} href="#">
              <Icon />
              {label}
            </NavigationMenuLink>
          </NavigationMenuItem>
        ))}
      </NavigationMenuList>
    </NavigationMenu>
  )
}

function DialogShowcase() {
  return (
    <Dialog>
      <DialogTrigger render={<Button variant="destructive" />}>
        <TrashIcon /> 刪除單字
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>確定要刪除「der Tisch」？</DialogTitle>
          <DialogDescription>
            這筆單字與它的複習排程紀錄會被永久刪除，無法復原。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <DialogClose render={<Button variant="outline">取消</Button>} />
          <Button variant="destructive">確定刪除</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ToastShowcase() {
  return (
    <div className="flex flex-wrap gap-3">
      <Button variant="outline" onClick={() => toast.success("已儲存「der Tisch」")}>
        觸發成功 toast
      </Button>
      <Button variant="outline" onClick={() => toast.error("儲存失敗，請重試")}>
        觸發錯誤 toast
      </Button>
      <Button variant="outline" onClick={() => toast.info("今日還有 12 張卡片待複習")}>
        觸發資訊 toast
      </Button>
    </div>
  )
}

function AlertShowcase() {
  return (
    <div className="flex flex-col gap-3">
      <Alert>
        <FlameIcon />
        <AlertTitle>連續複習 12 天</AlertTitle>
        <AlertDescription>保持下去，今天完成後就是 13 天了。</AlertDescription>
      </Alert>
      <Alert variant="destructive">
        <TrashIcon />
        <AlertTitle>還原資料庫會覆蓋目前資料</AlertTitle>
        <AlertDescription>還原前建議先手動備份現有的 SQLite 檔案。</AlertDescription>
      </Alert>
    </div>
  )
}

/**
 * UI 設計系統 S4 元件庫展示頁（見 ai/context/design-system.md 的元件庫 inventory）。
 * 目前尚未掛在任何路由上（本 Epic 還沒有路由器，見「Epic 架構基礎」任務卡的範圍決策）；
 * 之後若要在瀏覽器直接開啟，需等路由器導入時補一條 /dev/components 之類的路徑。
 */
export default function ComponentShowcase() {
  const { resolvedTheme, setTheme } = useTheme()

  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-6 py-8">
      <header className="flex items-center justify-between gap-4">
        <div>
          <h1 className="font-heading text-2xl font-semibold">
            Multilingual Immersion Tracker
          </h1>
          <p className="text-sm text-muted-foreground">
            UI 設計系統 S4 — 核心元件庫（字幕夜場 Subtitle Room）
          </p>
        </div>
        <Button
          variant="outline"
          size="icon"
          aria-label="切換亮／暗模式"
          onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
        >
          {resolvedTheme === "dark" ? <SunIcon /> : <MoonIcon />}
        </Button>
      </header>

      <Separator />

      <Section title="Nav" description="頂層導覽，active 狀態使用 accent 底色標示目前頁面。">
        <NavShowcase />
      </Section>

      <Section
        title="Button"
        description="6 種 variant × 5 種 size，涵蓋 hover／focus／disabled／loading 狀態。"
      >
        <ButtonShowcase />
      </Section>

      <Section
        title="Form（Field / Input / Select / Checkbox）"
        description="以「新增單字」為例，示範 label、必填錯誤（error）、disabled 狀態的整合用法。"
      >
        <FormShowcase />
      </Section>

      <Section title="Card" description="以真實資料呈現單字卡與追劇紀錄兩種內容密度。">
        <CardShowcase />
      </Section>

      <Section title="Table" description="單字庫列表，狀態欄位複用 Badge 的語意色。">
        <TableShowcase />
      </Section>

      <Section title="Modal（Dialog）" description="刪除確認情境，遮罩＋置中彈窗。">
        <DialogShowcase />
      </Section>

      <Section title="Toast" description="透過 sonner 呈現的成功／錯誤／資訊三種語意提示。">
        <ToastShowcase />
      </Section>

      <Section title="Alert / Badge" description="頁面內常駐提示，與 toast 的短暫通知互補。">
        <AlertShowcase />
      </Section>
    </div>
  )
}
