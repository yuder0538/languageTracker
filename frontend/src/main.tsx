import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ThemeProvider } from 'next-themes'
import './index.css'
import App from './App.tsx'
import { Toaster } from '@/components/ui/sonner'
import { LanguageProvider } from '@/lib/language-context'
import { RouterProvider } from '@/lib/router'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <LanguageProvider>
        <RouterProvider>
          <App />
          <Toaster />
        </RouterProvider>
      </LanguageProvider>
    </ThemeProvider>
  </StrictMode>,
)
