import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Plus, Search, Trash2, Lock, Unlock } from 'lucide-react'
import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { useAuth } from '@/auth/useAuth'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchTrimestres, createTrimestre, deleteTrimestre, verrouillerTrimestre, deverrouillerTrimestre } from './api'
import TrimestreFormDrawer from './TrimestreFormDrawer'
import { TYPE_PERIODE_LABELS, type TypePeriode } from './types'
import type { Trimestre, TrimestreCreateInput } from './types'

export default function TrimestreListPage() {
  const { user } = useAuth()
  const canCreate = user?.role === 'admin'
  const canLock = user?.role === 'admin' || user?.role === 'directeur'
  const canDelete = user?.role === 'admin'
  const qc = useQueryClient()
  const { data: annees = [] } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })
  const [filterAnnee, setFilterAnnee] = useState('')
  const [filterType, setFilterType] = useState('')

  const { data: trimestres = [], isLoading, isError } = useQuery({
    queryKey: ['trimestres', filterAnnee],
    queryFn: () => fetchTrimestres(filterAnnee ? Number(filterAnnee) : undefined),
  })

  const [search, setSearch] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [deleting, setDeleting] = useState<Trimestre | null>(null)

  const createMut = useMutation({
    mutationFn: (data: TrimestreCreateInput) => createTrimestre(data),
    onSuccess: () => { toast('Période créée'); qc.invalidateQueries({ queryKey: ['trimestres'] }); setDrawerOpen(false) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteTrimestre,
    onSuccess: () => { toast('Période supprimée'); qc.invalidateQueries({ queryKey: ['trimestres'] }); setDeleting(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const verrouillerMut = useMutation({
    mutationFn: verrouillerTrimestre,
    onSuccess: () => { toast('Période verrouillée'); qc.invalidateQueries({ queryKey: ['trimestres'] }) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deverrouillerMut = useMutation({
    mutationFn: deverrouillerTrimestre,
    onSuccess: () => { toast('Période déverrouillée'); qc.invalidateQueries({ queryKey: ['trimestres'] }) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const filtered = trimestres.filter((t) => {
    const matchSearch = t.nom.toLowerCase().includes(search.toLowerCase())
    const matchType = !filterType || t.type === filterType
    return matchSearch && matchType
  })

  const getAnneeLabel = (id: number) => annees.find((a) => a.id === id)?.libelle ?? '—'

  const nbCompositions = trimestres.filter((t) => t.type === 'COMPOSITION').length
  const nbTrimestres = trimestres.filter((t) => t.type === 'TRIMESTRE').length

  return (
    <>
    <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Périodes scolaires
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              {nbTrimestres > 0 && `${nbTrimestres} trimestre${nbTrimestres > 1 ? 's' : ''}`}
              {nbTrimestres > 0 && nbCompositions > 0 && ' · '}
              {nbCompositions > 0 && `${nbCompositions} composition${nbCompositions > 1 ? 's' : ''}`}
              {!nbTrimestres && !nbCompositions && 'Aucune période enregistrée'}
            </p>
          </div>
          {canCreate && <Button variant="primary" onClick={() => setDrawerOpen(true)}>
            <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
            Nouvelle période
          </Button>}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="relative max-w-sm flex-1">
            <Search strokeWidth={1.75} className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--color-ink-faint)]" />
            <Input
              placeholder="Rechercher une période…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select label="" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="">Tous les types</option>
            <option value="TRIMESTRE">Trimestres</option>
            <option value="COMPOSITION">Compositions</option>
          </Select>
          <Select label="" value={filterAnnee} onChange={(e) => setFilterAnnee(e.target.value)}>
            <option value="">Toutes les années</option>
            {annees.map((a) => (
              <option key={a.id} value={a.id}>{a.libelle}</option>
            ))}
          </Select>
        </div>

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger la liste des périodes." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState message={search ? 'Aucune période ne correspond à cette recherche.' : 'Aucune période enregistrée.'} />
          </div>
        ) : (
          <Card>
            <CardBody>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[var(--color-border)]">
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Nom</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Type</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Période</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Année scolaire</th>
                      <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Statut</th>
                      <th className="pb-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[var(--color-border-soft)]">
                    {filtered.map((t) => (
                      <tr key={t.id} className="hover:bg-[var(--color-surface-2)]">
                        <td className="py-3 text-[var(--color-ink)] font-medium">{t.nom}</td>
                        <td className="py-3">
                          <Badge tone={t.type === 'COMPOSITION' ? 'warning' : 'info'}>
                            {TYPE_PERIODE_LABELS[t.type as TypePeriode]}
                          </Badge>
                        </td>
                        <td className="py-3 text-[var(--color-ink-dim)]">
                          {new Date(t.date_debut).toLocaleDateString('fr-FR')} — {new Date(t.date_fin).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="py-3 text-[var(--color-ink-dim)]">{getAnneeLabel(t.annee_scolaire_id)}</td>
                        <td className="py-3">
                          {t.verrouille ? (
                            <span className="text-xs text-[var(--color-ink-dim)]">Verrouillé</span>
                          ) : (
                            <span className="text-xs font-medium text-[var(--color-success)]">Ouvert</span>
                          )}
                        </td>
                        <td className="py-3 text-right">
                          <div className="flex justify-end gap-1">
                            {canLock && (t.verrouille ? (
                              <button
                                onClick={() => deverrouillerMut.mutate(t.id)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-success-wash)] hover:text-[var(--color-success)]"
                                aria-label={`Déverrouiller ${t.nom}`}
                                title="Déverrouiller"
                              >
                                <Unlock size={14} strokeWidth={1.75} />
                              </button>
                            ) : (
                              <button
                                onClick={() => verrouillerMut.mutate(t.id)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-warning-wash)] hover:text-[var(--color-warning)]"
                                aria-label={`Verrouiller ${t.nom}`}
                                title="Verrouiller"
                              >
                                <Lock size={14} strokeWidth={1.75} />
                              </button>
                            ))}
                            {canDelete && (
                              <button
                                onClick={() => setDeleting(t)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                                aria-label={`Supprimer ${t.nom}`}
                              >
                                <Trash2 size={14} strokeWidth={1.75} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardBody>
          </Card>
        )}
      </div>

      <TrimestreFormDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onSubmit={(data) => createMut.mutate(data)}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), `Trimestre « ${deleting.nom} » supprimé.`)
          }
        }}
        title={`Supprimer cette ${deleting?.type === 'COMPOSITION' ? 'composition' : 'période'} ?`}
        description={`Êtes-vous sûr de vouloir supprimer « ${deleting?.nom} » ? Toutes les notes et bulletins associés seront supprimés.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </>
  )
}
