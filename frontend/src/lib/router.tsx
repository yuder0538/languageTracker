import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

export type AppRoute = "/" | "/vocabulary" | "/review" | "/review/artikel" | "/media-logs"

const KNOWN_ROUTES: AppRoute[] = ["/vocabulary", "/review", "/review/artikel", "/media-logs"]

function normalize(pathname: string): AppRoute {
  return KNOWN_ROUTES.includes(pathname as AppRoute) ? (pathname as AppRoute) : "/"
}

const RouterContext = createContext<{
  path: AppRoute
  navigate: (path: AppRoute) => void
} | null>(null)

/**
 * Minimal hand-rolled router (History API pushState/popstate) instead of a
 * routing library — a handful of flat routes so far, and this environment has
 * no Node.js to verify a new npm dependency actually installs/builds cleanly.
 * Revisit with a real router once route count/nesting grows.
 */
export function RouterProvider({ children }: { children: ReactNode }) {
  const [path, setPath] = useState<AppRoute>(() => normalize(window.location.pathname))

  useEffect(() => {
    function onPopState() {
      setPath(normalize(window.location.pathname))
    }
    window.addEventListener("popstate", onPopState)
    return () => window.removeEventListener("popstate", onPopState)
  }, [])

  function navigate(next: AppRoute) {
    if (next !== window.location.pathname) {
      window.history.pushState({}, "", next)
    }
    setPath(next)
  }

  return <RouterContext.Provider value={{ path, navigate }}>{children}</RouterContext.Provider>
}

export function useRouter() {
  const context = useContext(RouterContext)
  if (!context) throw new Error("useRouter must be used within a RouterProvider")
  return context
}
