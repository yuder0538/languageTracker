import { toast } from "sonner"

/**
 * Browser-native TTS (Web Speech API) — no backend call, no new dependency.
 * Machine-synthesized, not a real recording; good enough for a quick check,
 * revisit with a real dictionary-audio source later if that matters more.
 */
export function speak(text: string, language: "en" | "de", onEnd: () => void) {
  if (!("speechSynthesis" in window)) {
    toast.error("這個瀏覽器不支援語音朗讀")
    return
  }
  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = language === "de" ? "de-DE" : "en-US"
  utterance.onend = onEnd
  utterance.onerror = onEnd
  window.speechSynthesis.speak(utterance)
}
