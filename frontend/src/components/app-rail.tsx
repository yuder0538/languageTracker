import { LayoutDashboardIcon, BookOpenIcon, ClapperboardIcon, SettingsIcon } from "lucide-react"

import { useLanguage, type AppLanguage } from "@/lib/language-context"
import { useRouter, type AppRoute } from "@/lib/router"

const NAV_ITEMS: { route: AppRoute; label: string; icon: typeof LayoutDashboardIcon }[] = [
  { route: "/", label: "Dashboard", icon: LayoutDashboardIcon },
  { route: "/vocabulary", label: "單字庫", icon: BookOpenIcon },
  { route: "/media-logs", label: "追劇紀錄", icon: ClapperboardIcon },
  { route: "/settings", label: "設定", icon: SettingsIcon },
]

export function AppRail() {
  const { language, setLanguage } = useLanguage()
  const { path, navigate } = useRouter()

  return (
    <aside className="flex w-16 shrink-0 flex-col items-center gap-5 border-r border-border bg-card py-4">
      <div className="flex size-7 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
        IT
      </div>
      <nav className="flex flex-1 flex-col gap-2">
        {NAV_ITEMS.map(({ route, label, icon: Icon }) => (
          <button
            key={route}
            type="button"
            aria-label={label}
            aria-current={path === route ? "page" : undefined}
            onClick={() => navigate(route)}
            className={`flex size-9 items-center justify-center rounded-md ${
              path === route
                ? "bg-muted text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <Icon className="size-[18px]" />
          </button>
        ))}
      </nav>
      <div className="flex flex-col gap-1">
        {(["de", "en"] as AppLanguage[]).map((lang) => (
          <button
            key={lang}
            type="button"
            onClick={() => setLanguage(lang)}
            className={`h-6 w-8 rounded-md text-[11px] font-semibold ${
              language === lang
                ? "bg-primary text-primary-foreground"
                : "bg-muted text-muted-foreground hover:text-foreground"
            }`}
          >
            {lang.toUpperCase()}
          </button>
        ))}
      </div>
    </aside>
  )
}
