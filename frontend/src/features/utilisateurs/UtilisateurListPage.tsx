import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { PageHeader } from '@/components/ui/PageHeader'
import { SearchInput } from '@/components/ui/SearchInput'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { fetchUtilisateurs, deleteUtilisateur } from './api'
import { ROLE_LABELS, type Utilisateur } from './types'
import UtilisateurFormDrawer from './UtilisateurFormDrawer'

const ROLE_COLORS: Record<string, string> = {
  admin: 'danger',
  directeur: 'info',
  comptable: 'success',
}

export default function UtilisateurListPage() {
  const qc = useQueryClient()

  const { data: utilisateurs = [], isLoading, isError } = useQuery({
    queryKey: ['utilisateurs'],
    queryFn: fetchUtilisateurs,
  })

  const [search, setSearch] = useState('')
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editing, setEditing] = useState<Utilisateur | null>(null)
  const [deleting, setDeleting] = useState<Utilisateur | null>(null)

  const deleteMut = useMutation({
    mutationFn: deleteUtilisateur,
    onSuccess: () => { toast('Compte supprimé.'); qc.invalidateQueries({ queryKey: ['utilisateurs'] }); setDeleting(null) },
    onError: (err) => toast(extractErrorMessage(err), 'error'),
  })

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return utilisateurs
    return utilisateurs.filter((u) =>
      [u.nom, u.prenom, u.email, u.role].some((v) => v.toLowerCase().includes(q)),
    )
  }, [utilisateurs, search])

  return (
    <>
    <div className="flex flex-col gap-5">
        <PageHeader
          title="Comptes utilisateurs"
          count={utilisateurs.length}
          countLabel={`compte${utilisateurs.length > 1 ? 's' : ''} enregistré${utilisateurs.length > 1 ? 's' : ''}`}
          actionLabel="Nouveau compte"
          onAction={() => { setEditing(null); setDrawerOpen(true) }}
        />

        <SearchInput
          placeholder="Rechercher par nom, email, rôle…"
          value={search}
          onChange={setSearch}
        />

        {isLoading ? (
          <TableSkeleton rows={8} />
        ) : isError ? (
          <div className="py-16">
            <EmptyState message="Impossible de charger la liste des utilisateurs." />
          </div>
        ) : filtered.length === 0 ? (
          <div className="py-16">
            <EmptyState message={search ? 'Aucun compte ne correspond à cette recherche.' : 'Aucun compte utilisateur enregistré.'} />
          </div>
        ) : (
          <TableContainer>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Utilisateur</TableHead>
                  <TableHead>Rôle</TableHead>
                  <TableHead className="text-center">Statut</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar nom={u.nom} prenom={u.prenom} size="sm" />
                        <div>
                          <p className="font-medium text-[var(--color-ink)]">{u.prenom} {u.nom}</p>
                          <p className="text-xs text-[var(--color-ink-faint)]">{u.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge tone={(ROLE_COLORS[u.role] as 'danger' | 'info' | 'success') ?? 'neutral'}>
                        {ROLE_LABELS[u.role]}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="text-sm text-[var(--color-ink-dim)]">
                        {u.actif ? 'Actif' : 'Inactif'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="icon"
                          size="icon"
                          onClick={() => { setEditing(u); setDrawerOpen(true) }}
                          aria-label={`Modifier ${u.prenom} ${u.nom}`}
                        >
                          <Pencil strokeWidth={1.75} className="size-4" />
                        </Button>
                        <Button
                          variant="icon"
                          tone="danger"
                          size="icon"
                          onClick={() => setDeleting(u)}
                          aria-label={`Supprimer ${u.prenom} ${u.nom}`}
                        >
                          <Trash2 strokeWidth={1.75} className="size-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </div>

      <UtilisateurFormDrawer
        open={drawerOpen}
        onClose={() => { setDrawerOpen(false); setEditing(null) }}
        utilisateur={editing}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), 'Utilisateur supprimé.')
          }
        }}
        title="Supprimer ce compte ?"
        description={`Êtes-vous sûr de vouloir supprimer le compte de « ${deleting?.prenom} ${deleting?.nom} » ? Cette action est irréversible.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </>
  )
}