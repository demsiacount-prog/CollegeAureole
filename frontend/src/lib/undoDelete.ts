import { toast } from '@/components/ui/toast'

const UNDO_WINDOW_MS = 5000

export function scheduleDeleteWithUndo(
  performDelete: () => void,
  message: string,
  undoLabel = 'Annuler',
  cancelledMessage = 'Suppression annulée.',
) {
  let cancelled = false
  const timer = setTimeout(() => {
    if (!cancelled) performDelete()
  }, UNDO_WINDOW_MS)

  toast(message, 'success', {
    duration: UNDO_WINDOW_MS,
    action: {
      label: undoLabel,
      onClick: () => {
        cancelled = true
        clearTimeout(timer)
        toast(cancelledMessage, 'info')
      },
    },
  })
}