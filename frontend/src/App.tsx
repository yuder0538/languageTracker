import Dashboard from "@/pages/Dashboard"
import Vocabulary from "@/pages/Vocabulary"
import Review from "@/pages/Review"
import ReviewArtikel from "@/pages/ReviewArtikel"
import MediaLog from "@/pages/MediaLog"
import Settings from "@/pages/Settings"
import { useRouter } from "@/lib/router"

function App() {
  const { path } = useRouter()
  if (path === "/vocabulary") return <Vocabulary />
  if (path === "/review/artikel") return <ReviewArtikel />
  if (path === "/review") return <Review />
  if (path === "/media-logs") return <MediaLog />
  if (path === "/settings") return <Settings />
  return <Dashboard />
}

export default App
