import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * `date.toISOString().slice(0, 10)` gives the UTC calendar date, not the
 * user's local one — wrong for hours around local midnight (e.g. still
 * "yesterday" in UTC+8 until 8am local). Use local getters instead so this
 * always matches the date the user actually sees on their clock.
 */
export function toLocalIsoDate(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, "0")
  const day = String(date.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}
