import { useEffect, useState } from 'react'

let _count = 0
let _listeners: Array<(count: number) => void> = []

function _emit() {
  for (const fn of _listeners) fn(_count)
}

/** Suivre le nombre total de modales ouvertes (Drawer, ConfirmDialog, etc.). */
export function useModalStackCount(): number {
  const [count, setCount] = useState(_count)

  useEffect(() => {
    _listeners.push(setCount)
    return () => {
      _listeners = _listeners.filter((fn) => fn !== setCount)
    }
  }, [])

  return count
}

/** Incrémente le compteur global tant que `open` est vrai. */
export function useModalStack(open: boolean) {
  useEffect(() => {
    if (!open) return
    _count++
    _emit()
    return () => {
      _count = Math.max(0, _count - 1)
      _emit()
    }
  }, [open])
}
