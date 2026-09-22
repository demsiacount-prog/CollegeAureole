import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'

const UNDO_WINDOW_MS = 5000

export function scheduleDeleteWithUndo(
  performDelete: () => unknown,
  message: string,
  undoLabel = 'Annuler',
  cancelledMessage = 'Suppression annulée.',
) {
  let cancelled = false
  const timer = setTimeout(() => {
    if (cancelled) return
    // Exécute la suppression au délai. Si elle est asynchrone (promesse) ou
    // lève une erreur synchrone, une erreur visible est affichée au lieu d'un
    // échec silencieux alors que la ligne a déjà disparu de l'écran.
    Promise.resolve()
      .then(performDelete)
      .catch((err) => {
        toast(extractErrorMessage(err, 'La suppression a échoué.'), 'error')
      })
  }, UNDO_WINDOW_MS)

  toast(message, 'warning', {
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