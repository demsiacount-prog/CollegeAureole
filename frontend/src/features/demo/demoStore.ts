export type DemoListener = (open: boolean) => void

const DEMO_STORAGE_PREFIX = 'aureole-demo-state'
const INSTALLATION_ID_KEY = 'aureole-install-id'

let isOpen = false
const listeners = new Set<DemoListener>()

function getInstallationId() {
  if (typeof window === 'undefined') return 'server'

  const existing = window.localStorage.getItem(INSTALLATION_ID_KEY)
  if (existing) return existing

  const generated = `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
  window.localStorage.setItem(INSTALLATION_ID_KEY, generated)
  return generated
}

async function getAppVersion() {
  try {
    const { getVersion } = await import('@tauri-apps/api/app')
    return await getVersion()
  } catch {
    return 'web'
  }
}

function getDemoStateKey(version: string, installationId: string) {
  return `${DEMO_STORAGE_PREFIX}-${version}-${installationId}`
}

export function startDemo() {
  isOpen = true
  listeners.forEach((l) => l(true))
}

export function stopDemo() {
  isOpen = false
  listeners.forEach((l) => l(false))
}

export function isDemoOpen() {
  return isOpen
}

export async function shouldStartDemo() {
  if (typeof window === 'undefined') return false

  const [version, installationId] = await Promise.all([getAppVersion(), Promise.resolve(getInstallationId())])
  const key = getDemoStateKey(version, installationId)
  return window.localStorage.getItem(key) !== '1'
}

export async function markDemoCompleted() {
  if (typeof window === 'undefined') return

  const [version, installationId] = await Promise.all([getAppVersion(), Promise.resolve(getInstallationId())])
  const key = getDemoStateKey(version, installationId)
  window.localStorage.setItem(key, '1')
}

export function subscribeDemo(listener: DemoListener) {
  listeners.add(listener)
  listener(isOpen)
  return () => {
    listeners.delete(listener)
  }
}
