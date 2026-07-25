import Dashboard from "@/pages/Dashboard"
import Vocabulary from "@/pages/Vocabulary"
import Review from "@/pages/Review"
import MediaLog from "@/pages/MediaLog"
import { useRouter } from "@/lib/router"

function App() {
  const { path } = useRouter()
  if (path === "/vocabulary") return <Vocabulary />
  if (path === "/review") return <Review />
  if (path === "/media-logs") return <MediaLog />
  return <Dashboard />
}

export default App
