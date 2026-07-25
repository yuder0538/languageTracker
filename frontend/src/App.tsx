import Dashboard from "@/pages/Dashboard"
import Vocabulary from "@/pages/Vocabulary"
import { useRouter } from "@/lib/router"

function App() {
  const { path } = useRouter()
  return path === "/vocabulary" ? <Vocabulary /> : <Dashboard />
}

export default App
