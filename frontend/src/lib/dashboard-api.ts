import { apiGet, apiPost } from "@/lib/api"
import type { AppLanguage } from "@/lib/language-context"

export interface VocabularyRead {
  id: number
  language: AppLanguage
  headword: string
  part_of_speech: string | null
  translation_zh: string | null
  example_sentence: string | null
  media_log_id: number | null
  ipa: string | null
  en_definition: string | null
  de_artikel: "der" | "die" | "das" | null
  de_plural: string | null
  de_conjugation: string | null
  notes: string | null
  created_at: string
  updated_at: string
}

export interface MediaLogRead {
  id: number
  language: AppLanguage
  title: string
  media_type: string
  watched_date: string
  duration_minutes: number
  notes: string | null
  created_at: string
  updated_at: string
}

export interface ReviewStats {
  reviewed_today: number
  accuracy_today: number | null
  streak_days: number
}

export interface ReviewHistoryDay {
  date: string
  reviewed_count: number
  correct_count: number
}

export interface VocabularyCreate {
  language: AppLanguage
  headword: string
  part_of_speech?: string | null
  translation_zh?: string | null
  media_log_id?: number | null
  de_artikel?: "der" | "die" | "das" | null
  notes?: string | null
}

export function fetchVocabulary(language: AppLanguage) {
  return apiGet<VocabularyRead[]>("/vocabulary", { language })
}

export function fetchMediaLogs(language: AppLanguage) {
  return apiGet<MediaLogRead[]>("/media-logs", { language })
}

export function fetchReviewQueue(language: AppLanguage) {
  return apiGet<VocabularyRead[]>("/reviews/queue", { language })
}

export function fetchReviewStats(language: AppLanguage) {
  return apiGet<ReviewStats>("/reviews/stats", { language })
}

export function fetchReviewHistory(language: AppLanguage, days = 35) {
  return apiGet<ReviewHistoryDay[]>("/reviews/history", { language, days })
}

export function createVocabulary(payload: VocabularyCreate) {
  return apiPost<VocabularyRead>("/vocabulary", payload)
}

export function enrichEnDictionary(id: number) {
  return apiPost<VocabularyRead>(`/vocabulary/${id}/enrich/en-dictionary`, {})
}

export function enrichDeTranslation(id: number) {
  return apiPost<VocabularyRead>(`/vocabulary/${id}/enrich/de-translation`, {})
}
