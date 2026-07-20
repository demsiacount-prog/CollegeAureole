import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Search, UserCheck, UserX, Pencil } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Avatar } from '@/components/ui/Avatar'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { activerEleve, createEleve, desactiverEleve, fetchEleves, updateEleve } from './api'
import { EleveFormDrawer } from './EleveFormDrawer'
import type { Eleve } from './types'

export function EleveListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const queryClient = useQueryClient()

  const { data: eleves = [], isLoading, isError } = useQuery({ queryKey: ['eleves'], queryFn: fetchEleves })

  const [search, setSearch] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Eleve | null>(null)

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['eleves'] })

  const createMutation = useMutation({ mutationFn: createEleve, onSuccess: invalidate })
  const updateMutation = useMutation({
    mutationFn: ({ matricule, payload }: { matricule: string; payload: Parameters<typeof updateEleve>[1] }) =>
      updateEleve(matricule, payload),
    onSuccess: invalidate,
  })
  const activerMutation = useMutation({ mutationFn: activerEleve, onSuccess: invalidate })
  const desactiverMutation = useMutation({ mutationFn: desactiverEleve, onSuccess: invalidate })

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return eleves
    return eleves.filter((e) =>
      [e.matricule, e.nom, e.prenom, e.classe?.nom, e.classe?.niveau].filter(Boolean).some((v) => v!.toLowerCase().includes(q)),
    )
  }, [eleves, search])

  function openCreate() {
    setEditing(null)
    setDrawerOpen(true)
  }

  function openEdit(eleve: Eleve) {
    setEditing(eleve)
    setDrawerOpen(true)
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
        <div>
          <h2 className="font-[var(--font-display)] text-2xl font-medium tracking-tight text-[var(--color-ink)]">
            Élèves
          </h2>
          <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
            {eleves.length} élève{eleves.length > 1 ? 's' : ''} enregistré{eleves.length > 1 ? 's' : ''}
          </p>
        </div>
        {canWrite && (
          <Button variant="primary" onClick={openCreate}>
            <Plus className="size-4" />
            Nouvel élève
          </Button>
        )}
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--color-ink-faint)]" />
        <Input
          placeholder="Rechercher par nom, matricule, classe…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      <div className="overflow-hidden rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)]">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner label="Chargement des élèves…" />
          </div>
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger la liste des élèves." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState message={search ? 'Aucun élève ne correspond à cette recherche.' : 'Aucun élève enregistré pour le moment.'} />
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--color-border-soft)] text-xs uppercase tracking-wide text-[var(--color-ink-faint)]">
                <th className="px-5 py-3 font-medium">Élève</th>
                <th className="px-5 py-3 font-medium">Matricule</th>
                <th className="px-5 py-3 font-medium">Classe</th>
                <th className="px-5 py-3 font-medium">Tuteur</th>
                <th className="px-5 py-3 font-medium">Statut</th>
                <th className="px-5 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((eleve) => (
                <tr key={eleve.matricule} className="border-b border-[var(--color-border-soft)] last:border-0 hover:bg-[var(--color-surface-2)]">
                  <td className="px-5 py-3">
                    <Link to={`/app/eleves/${eleve.matricule}`} className="flex items-center gap-3 group">
                      <Avatar nom={eleve.nom} prenom={eleve.prenom} size="sm" />
                      <span className="font-medium text-[var(--color-ink)] group-hover:text-[var(--color-halo-bright)]">
                        {eleve.prenom} {eleve.nom}
                      </span>
                    </Link>
                  </td>
                  <td className="px-5 py-3 font-[var(--font-mono)] text-xs text-[var(--color-ink-dim)]">{eleve.matricule}</td>
                  <td className="px-5 py-3 text-[var(--color-ink-dim)]">
                    {eleve.classe ? `${eleve.classe.niveau} — ${eleve.classe.nom}` : <span className="text-[var(--color-ink-faint)]">Non affecté</span>}
                  </td>
                  <td className="px-5 py-3 text-[var(--color-ink-dim)]">
                    {eleve.tuteur.prenom} {eleve.tuteur.nom}
                  </td>
                  <td className="px-5 py-3">
                    <Badge tone={eleve.statut === 'actif' ? 'success' : 'neutral'}>
                      {eleve.statut === 'actif' ? 'Actif' : 'Inactif'}
                    </Badge>
                  </td>
                  <td className="px-5 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {canWrite && (
                        <>
                          <button
                            title="Modifier"
                            onClick={() => openEdit(eleve)}
                            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                          >
                            <Pencil className="size-4" />
                          </button>
                          {eleve.statut === 'actif' ? (
                            <button
                              title="Désactiver"
                              onClick={() => desactiverMutation.mutate(eleve.matricule)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
                            >
                              <UserX className="size-4" />
                            </button>
                          ) : (
                            <button
                              title="Activer"
                              onClick={() => activerMutation.mutate(eleve.matricule)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-success-wash)] hover:text-[var(--color-success)]"
                            >
                              <UserCheck className="size-4" />
                            </button>
                          )}
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <EleveFormDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        eleve={editing}
        onCreate={(payload) => createMutation.mutateAsync(payload)}
        onUpdate={(matricule, payload) => updateMutation.mutateAsync({ matricule, payload })}
      />
    </div>
  )
}
