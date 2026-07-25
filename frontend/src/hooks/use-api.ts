import { useCallback, useEffect, useState } from "react"

export type ApiState<T> =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: T }

export function useApi<T>(
  fetcher: () => Promise<T>,
  deps: unknown[]
): ApiState<T> & { retry: () => void } {
  const [state, setState] = useState<ApiState<T>>({ status: "loading" })
  const [tick, setTick] = useState(0)

  const load = useCallback(() => {
    setState({ status: "loading" })
    fetcher()
      .then((data) => setState({ status: "success", data }))
      .catch((err) =>
        setState({
          status: "error",
          message: err instanceof Error ? err.message : "讀取失敗，請重試",
        })
      )
    // fetcher is rebuilt each render from `deps`; re-running on `deps` change
    // (not `fetcher` identity) is the point of this hook.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  useEffect(() => {
    load()
  }, [load, tick])

  return { ...state, retry: () => setTick((t) => t + 1) } as ApiState<T> & {
    retry: () => void
  }
}
