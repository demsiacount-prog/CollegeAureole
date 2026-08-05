import { useCallback, useEffect, useState } from 'react'

export type ToastTone = 'success' | 'error' | 'info'

export interface ToastAction {
  label: string
  onClick: () => void
}

export interface Toast {
  id: number
  message: string
  tone: ToastTone
  action?: ToastAction
  duration: number
}

let _nextId = 0
let _listeners: Array<(toasts: Toast[]) => void> = []
let _toasts: Toast[] = []

function _emit() {
  for (const fn of _listeners) fn([..._toasts])
}

function _remove(id: number) {
  _toasts = _toasts.filter((t) => t.id !== id)
  _emit()
}

export function toast(message: string, tone: ToastTone = 'success', opts?: { action?: ToastAction; duration?: number }) {
  const id = _nextId++
  const duration = opts?.duration ?? 4000
  _toasts = [..._toasts, { id, message, tone, action: opts?.action, duration }]
  _emit()
  setTimeout(() => _remove(id), duration)
}

export function toastWithAction(message: string, action: ToastAction, tone: ToastTone = 'success', duration = 5000) {
  toast(message, tone, { action, duration })
}

export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>(_toasts)

  useEffect(() => {
    _listeners.push(setToasts)
    return () => {
      _listeners = _listeners.filter((fn) => fn !== setToasts)
    }
  }, [])

  const dismiss = useCallback((id: number) => _remove(id), [])

  return { toasts, dismiss }
}
