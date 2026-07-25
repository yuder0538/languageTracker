import Dashboard from "@/pages/Dashboard"
import Vocabulary from "@/pages/Vocabulary"
import Review from "@/pages/Review"
import { useRouter } from "@/lib/router"

function App() {
  const { path } = useRouter()
  if (path === "/vocabulary") return <Vocabulary />
  if (path === "/review") return <Review />
  return <Dashboard />
}

export default App
