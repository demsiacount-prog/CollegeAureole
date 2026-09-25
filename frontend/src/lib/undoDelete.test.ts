import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { scheduleDeleteWithUndo } from './undoDelete'
import { toast } from '@/components/ui/toast'

vi.mock('@/components/ui/toast', () => ({ toast: vi.fn() }))

describe('scheduleDeleteWithUndo', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.mocked(toast).mockClear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('affiche un toast d’avertissement immédiatement, avec une action Annuler', () => {
    scheduleDeleteWithUndo(() => {}, 'Élève supprimé.')

    expect(toast).toHaveBeenCalledWith(
      'Élève supprimé.',
      'warning',
      expect.objectContaining({ action: expect.objectContaining({ label: 'Annuler' }) }),
    )
  })

  it('exécute la suppression seulement après le délai, pas immédiatement', async () => {
    const performDelete = vi.fn()
    scheduleDeleteWithUndo(performDelete, 'Supprimé.')

    expect(performDelete).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(4999)
    expect(performDelete).not.toHaveBeenCalled()
    // performDelete est appelé via une microtâche (Promise.resolve().then(...))
    // après le timer : il faut laisser le temps à cette microtâche de s'exécuter.
    await vi.advanceTimersByTimeAsync(1)
    expect(performDelete).toHaveBeenCalledTimes(1)
  })

  it('annuler avant l’échéance empêche la suppression et affiche le message d’annulation', () => {
    const performDelete = vi.fn()
    scheduleDeleteWithUndo(performDelete, 'Supprimé.', 'Annuler', 'Annulé.')

    const appelToast = vi.mocked(toast).mock.calls[0]
    const onClick = appelToast[2]?.action?.onClick
    onClick?.()

    vi.advanceTimersByTime(5000)
    expect(performDelete).not.toHaveBeenCalled()
    expect(toast).toHaveBeenCalledWith('Annulé.', 'info')
  })

  it('accepte un libellé et un message d’annulation personnalisés', () => {
    scheduleDeleteWithUndo(() => {}, 'Supprimé.', 'Restaurer', 'Restauré.')
    expect(toast).toHaveBeenCalledWith(
      'Supprimé.',
      'warning',
      expect.objectContaining({ action: expect.objectContaining({ label: 'Restaurer' }) }),
    )
  })

  it('une erreur (synchrone ou promesse rejetée) pendant la suppression affiche un toast d’erreur au lieu d’échouer silencieusement', async () => {
    const performDelete = vi.fn(() => {
      throw new Error('échec réseau')
    })
    scheduleDeleteWithUndo(performDelete, 'Supprimé.')

    await vi.advanceTimersByTimeAsync(5000)

    expect(toast).toHaveBeenCalledWith('La suppression a échoué.', 'error')
  })

  it('une suppression asynchrone qui rejette est aussi rattrapée', async () => {
    const performDelete = vi.fn(() => Promise.reject(new Error('échec')))
    scheduleDeleteWithUndo(performDelete, 'Supprimé.')

    await vi.advanceTimersByTimeAsync(5000)

    expect(toast).toHaveBeenCalledWith('La suppression a échoué.', 'error')
  })
})
