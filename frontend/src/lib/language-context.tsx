import { createContext, useContext, useEffect, useState, type ReactNode } from "react"

export type AppLanguage = "en" | "de"

const STORAGE_KEY = "immersion-tracker:language"
const DEFAULT_LANGUAGE: AppLanguage = "de"

function readStoredLanguage(): AppLanguage {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return stored === "en" || stored === "de" ? stored : DEFAULT_LANGUAGE
}

const LanguageContext = createContext<{
  language: AppLanguage
  setLanguage: (language: AppLanguage) => void
} | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<AppLanguage>(readStoredLanguage)

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, language)
  }, [language])

  return (
    <LanguageContext.Provider value={{ language, setLanguage }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) throw new Error("useLanguage must be used within a LanguageProvider")
  return context
}
