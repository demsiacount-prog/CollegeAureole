import { useState, useEffect } from 'react'

const DESKTOP_DEV_URL = 'http://localhost:3000'

function isTauri(): boolean {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window
}

export function useBackendUrl(): { backendUrl: string; ready: boolean } {
  const [backendUrl, setBackendUrl] = useState(
    isTauri() ? DESKTOP_DEV_URL : window.location.origin,
  )
  const [ready, setReady] = useState(!isTauri())

  useEffect(() => {
    if (!isTauri()) return

    let cancelled = false

    async function init() {
      try {
        const { invoke } = await import('@tauri-apps/api/core')
        const { listen } = await import('@tauri-apps/api/event')

        listen<number>('backend-ready', (event) => {
          if (cancelled) return
          setBackendUrl(`http://127.0.0.1:${event.payload}`)
          setReady(true)
        })

        const url = await invoke<string>('get_backend_url')
        if (url && !url.endsWith(':0')) {
          setBackendUrl(url)
          setReady(true)
        }
      } catch {
        setReady(true)
      }
    }

    init()
    return () => { cancelled = true }
  }, [])

  return { backendUrl, ready }
}
