import { useRouter } from "@/lib/router"

/**
 * German-only: standard review vs. der/die/das artikel quiz share the same
 * review "session" concept, so let people flip between them without leaving
 * the flow. Not rendered for English — artikel mode doesn't apply there.
 */
export function ReviewModeSwitch({ mode }: { mode: "standard" | "artikel" }) {
  const { navigate } = useRouter()

  return (
    <div className="inline-flex items-center gap-0.5 rounded-full bg-muted p-0.5 text-xs font-medium">
      <button
        type="button"
        onClick={() => navigate("/review")}
        className={`rounded-full px-3 py-1 ${
          mode === "standard" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
        }`}
      >
        標準複習
      </button>
      <button
        type="button"
        onClick={() => navigate("/review/artikel")}
        className={`rounded-full px-3 py-1 ${
          mode === "artikel" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground"
        }`}
      >
        冠詞複習
      </button>
    </div>
  )
}
