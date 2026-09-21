import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Power, Trash2, KeyRound } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Tooltip } from '@/components/ui/Tooltip'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import { useAuth } from '@/auth/useAuth'
import {
  fetchUtilisateurs,
  creerUtilisateur,
  modifierStatutUtilisateur,
  reinitialiserMotDePasse,
  supprimerUtilisateur,
} from '@/features/utilisateurs/api'
import type { Utilisateur, UtilisateurCreateInput } from '@/features/utilisateurs/types'
import { ROLE_LABELS } from '@/features/utilisateurs/types'
import UtilisateurFormDrawer from '@/features/utilisateurs/UtilisateurFormDrawer'
import ReinitialiserMotDePasseDrawer from '@/features/utilisateurs/ReinitialiserMotDePasseDrawer'

const ROLE_BADGE_TONE: Record<string, 'success' | 'info' | 'neutral'> = {
  ADMIN: 'success',
  DIRECTEUR: 'info',
  SECRETAIRE: 'neutral',
  ENSEIGNANT: 'neutral',
  COMPTABLE: 'neutral',
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="mb-4 border-b border-[var(--border-soft)] pb-2 text-sm font-semibold text-[var(--ink)]">
      {children}
    </h3>
  )
}

export default function UtilisateursTab() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const { data: utilisateurs = [], isLoading, isError } = useQuery({
    queryKey: ['utilisateurs'],
    queryFn: fetchUtilisateurs,
  })

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [resetUser, setResetUser] = useState<Utilisateur | null>(null)
  const [deleting, setDeleting] = useState<Utilisateur | null>(null)

  const createMut = useMutation({
    mutationFn: (data: UtilisateurCreateInput) => creerUtilisateur(data),
    onSuccess: () => { toast('Utilisateur créé'); qc.invalidateQueries({ queryKey: ['utilisateurs'] }); setDrawerOpen(false) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const statutMut = useMutation({
    mutationFn: ({ id, actif }: { id: number; actif: boolean }) => modifierStatutUtilisateur(id, actif),
    onSuccess: (u) => { toast(`Compte ${u.actif ? 'activé' : 'désactivé'}`); qc.invalidateQueries({ queryKey: ['utilisateurs'] }) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const resetMut = useMutation({
    mutationFn: ({ id, mdp }: { id: number; mdp: string }) => reinitialiserMotDePasse(id, mdp),
    onSuccess: () => { toast('Mot de passe réinitialisé'); qc.invalidateQueries({ queryKey: ['utilisateurs'] }); setResetUser(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: supprimerUtilisateur,
    onSuccess: () => { toast('Utilisateur supprimé'); qc.invalidateQueries({ queryKey: ['utilisateurs'] }); setDeleting(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  if (isLoading) {
    return (
      <Card>
        <TableSkeleton rows={5} columns={4} />
      </Card>
    )
  }

  if (isError) {
    return (
      <div className="rounded-[var(--radius-sm)] border border-[var(--danger)]/20 bg-[var(--danger-w)] px-4 py-3 text-sm text-[var(--danger)]">
        Impossible de charger les utilisateurs.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <SectionTitle>Comptes utilisateurs</SectionTitle>
        <Button variant="primary" onClick={() => setDrawerOpen(true)}>
          <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
          Nouvel utilisateur
        </Button>
      </div>

      <Card>
        {utilisateurs.length === 0 ? (
          <div className="p-5">
            <EmptyState message="Aucun utilisateur enregistré." />
          </div>
        ) : (
          <TableContainer className="rounded-none border-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Nom complet</TableHead>
                  <TableHead>E-mail</TableHead>
                  <TableHead>Rôle</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead>Créé le</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {utilisateurs.map((u) => {
                  const estMoi = u.id === user?.id
                  return (
                    <TableRow key={u.id}>
                      <TableCell className="font-medium text-[var(--ink)]">
                        {u.prenom} {u.nom}
                        {estMoi && <span className="ml-2 text-xs font-normal text-[var(--ink-faint)]">(vous)</span>}
                      </TableCell>
                      <TableCell className="text-[var(--ink-dim)]">{u.email}</TableCell>
                      <TableCell>
                        <Badge tone={ROLE_BADGE_TONE[u.role] ?? 'neutral'}>
                          {ROLE_LABELS[u.role] ?? u.role}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {u.actif ? <Badge tone="success">Actif</Badge> : <Badge tone="danger">Désactivé</Badge>}
                      </TableCell>
                      <TableCell className="text-[var(--ink-dim)]">
                        {new Date(u.created_at).toLocaleDateString('fr-FR')}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Tooltip content={u.actif ? 'Désactiver' : 'Activer'}>
                            <Button
                              variant="icon"
                              size="icon"
                              onClick={() => statutMut.mutate({ id: u.id, actif: !u.actif })}
                              disabled={estMoi || statutMut.isPending}
                            >
                              <Power size={14} strokeWidth={1.75} />
                            </Button>
                          </Tooltip>
                          <Tooltip content="Réinitialiser le mot de passe">
                            <Button
                              variant="icon"
                              size="icon"
                              onClick={() => setResetUser(u)}
                            >
                              <KeyRound size={14} strokeWidth={1.75} />
                            </Button>
                          </Tooltip>
                          <Tooltip content="Supprimer">
                            <Button
                              variant="icon"
                              tone="danger"
                              size="icon"
                              onClick={() => setDeleting(u)}
                              disabled={estMoi}
                            >
                              <Trash2 size={14} strokeWidth={1.75} />
                            </Button>
                          </Tooltip>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>

      <UtilisateurFormDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onSubmit={(data) => createMut.mutate(data)}
      />

      <ReinitialiserMotDePasseDrawer
        utilisateur={resetUser}
        onClose={() => setResetUser(null)}
        onSubmit={(mdp) => resetMut.mutate({ id: resetUser!.id, mdp })}
      />

      <ConfirmDialog
        open={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => {
          if (deleting) {
            setDeleting(null)
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), `Utilisateur « ${deleting.prenom} ${deleting.nom} » supprimé.`)
          }
        }}
        title="Supprimer cet utilisateur ?"
        description={`Supprimer le compte de "${deleting?.prenom} ${deleting?.nom}" ? Il ne pourra plus se connecter.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}