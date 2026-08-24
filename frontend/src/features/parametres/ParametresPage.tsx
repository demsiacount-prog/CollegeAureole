import { useState } from 'react'
import { clsx } from 'clsx'
import { useAuth } from '@/auth/useAuth'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Trash2, Power, Lock, Shield, Users, CalendarOff,
  Eye, EyeOff, Sparkles, Building2, Download,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage, api } from '@/lib/api'
import { required, minLength, hasErrors, type Errors } from '@/lib/validation'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
import UtilisateurListPage from '@/features/utilisateurs/UtilisateurListPage'
import {
  fetchAnneesScolaires,
  createAnneeScolaire,
  deleteAnneeScolaire,
  activerAnneeScolaire,
  cloturerAnneeScolaire,
} from '@/features/annees_scolaires/api'
import AnneeScolaireFormDrawer from '@/features/annees_scolaires/AnneeScolaireFormDrawer'
import { genererPeriodesParDefaut } from '@/features/trimestres/api'
import FicheEtablissementTab from '@/features/etablissement/FicheEtablissementTab'
import ExportTab from '@/features/parametres/ExportTab'
import type { AnneeScolaire, AnneeScolaireCreateInput } from '@/features/annees_scolaires/types'

type Tab = 'fiche' | 'annees' | 'securite' | 'utilisateurs' | 'export'

const tabs: { id: Tab; label: string; icon: typeof Shield }[] = [
  { id: 'fiche', label: "Fiche établissement", icon: Building2 },
  { id: 'annees', label: 'Années scolaires', icon: CalendarOff },
  { id: 'securite', label: 'Sécurité', icon: Shield },
  { id: 'utilisateurs', label: 'Utilisateurs', icon: Users },
  { id: 'export', label: 'Export des données', icon: Download },
]

export default function ParametresPage() {
  const { user } = useAuth()
  const visibleTabs = tabs.filter((t) => {
    if (t.id === 'utilisateurs') return user?.role === 'admin'
    if (t.id === 'fiche') return user?.role === 'admin' || user?.role === 'directeur'
    if (t.id === 'export') return user?.role === 'admin'
    return true
  })
  const [activeTab, setActiveTab] = useState<Tab>('annees')

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
            Paramètres
          </h2>
          <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
            Configuration du système de gestion scolaire
          </p>
        </div>

        <div className="flex gap-6">
          <div className="w-44 shrink-0 space-y-1">
            {visibleTabs.map((t) => {
              const Icon = t.icon
              const active = activeTab === t.id
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={clsx(
                    'flex w-full items-center gap-3 rounded-[var(--radius-sm)] border border-transparent px-3 py-2.5 text-left text-sm transition-colors',
                    active
                      ? 'border-[var(--color-brand-wash)] bg-[var(--color-brand-wash)] text-[var(--color-brand)]'
                      : 'text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]',
                  )}
                >
                  <Icon size={14} strokeWidth={1.75} />
                  {t.label}
                </button>
              )
            })}
          </div>

          <div className="flex-1 rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
            {activeTab === 'fiche' && <FicheEtablissementTab />}
            {activeTab === 'annees' && <AnneesTab />}
            {activeTab === 'securite' && <SecuriteTab />}
            {activeTab === 'utilisateurs' && <UtilisateursTab />}
            {activeTab === 'export' && <ExportTab />}
            
          </div>
        </div>
      </div>
    </div>
  )
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="mb-4 border-b border-[var(--color-border-soft)] pb-2 text-sm font-semibold text-[var(--color-ink)]">
      {children}
    </h3>
  )
}

/* ─── Onglet Élèves ─────────────────────────────────────────────── */


/* ─── Onglet Années scolaires ───────────────────────────────────── */

function AnneesTab() {
  const qc = useQueryClient()
  const { data: annees = [], isLoading, isError } = useQuery({ queryKey: ['annees-scolaires'], queryFn: fetchAnneesScolaires })

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [deleting, setDeleting] = useState<AnneeScolaire | null>(null)

  const createMut = useMutation({
    mutationFn: (data: AnneeScolaireCreateInput) => createAnneeScolaire(data),
    onSuccess: () => { toast('Année scolaire créée'); qc.invalidateQueries({ queryKey: ['annees-scolaires'] }); setDrawerOpen(false) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const deleteMut = useMutation({
    mutationFn: deleteAnneeScolaire,
    onSuccess: () => { toast('Année scolaire supprimée'); qc.invalidateQueries({ queryKey: ['annees-scolaires'] }); setDeleting(null) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const activerMut = useMutation({
    mutationFn: activerAnneeScolaire,
    onSuccess: () => { toast('Année scolaire activée'); qc.invalidateQueries({ queryKey: ['annees-scolaires'] }) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const cloturerMut = useMutation({
    mutationFn: cloturerAnneeScolaire,
    onSuccess: () => { toast('Année scolaire clôturée'); qc.invalidateQueries({ queryKey: ['annees-scolaires'] }) },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const genererMut = useMutation({
    mutationFn: (anneeId: number) => genererPeriodesParDefaut(anneeId),
    onSuccess: (r) => {
      toast(r.cree > 0 ? `${r.cree} périodes générées` : 'Les périodes par défaut existent déjà pour cette année')
      qc.invalidateQueries({ queryKey: ['annees-scolaires'] })
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  if (isLoading) {
    return (
      <Card>
        <TableSkeleton rows={6} columns={4} />
      </Card>
    )
  }

  if (isError) {
    return (
      <div className="rounded border border-[var(--color-danger)]/20 bg-[var(--color-danger-wash)] px-4 py-3 text-sm text-[var(--color-danger)]">
        Impossible de charger les années scolaires.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <SectionTitle>Années scolaires</SectionTitle>
        <Button variant="primary" onClick={() => setDrawerOpen(true)}>
          <Plus size={16} strokeWidth={1.75} className="mr-1.5" />
          Nouvelle année
        </Button>
      </div>

      <Card>
        {annees.length === 0 ? (
          <div className="p-5">
            <EmptyState message="Aucune année scolaire enregistrée." />
          </div>
        ) : (
          <TableContainer className="rounded-none border-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Libellé</TableHead>
                  <TableHead>Période</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {annees.map((a) => (
                <TableRow key={a.id}>
                  <TableCell className="py-3 font-medium text-[var(--color-ink)]">{a.libelle}</TableCell>
                  <TableCell className="py-3 text-[var(--color-ink-dim)]">
                    {new Date(a.date_debut).toLocaleDateString('fr-FR')} — {new Date(a.date_fin).toLocaleDateString('fr-FR')}
                  </TableCell>
                  <TableCell className="py-3">
                    <div className="flex gap-1.5">
                      {a.active && <Badge tone="success">Active</Badge>}
                      {a.cloturee && <Badge tone="neutral">Clôturée</Badge>}
                      {!a.active && !a.cloturee && <Badge tone="info">Inactive</Badge>}
                    </div>
                  </TableCell>
                  <TableCell className="py-3 text-right">
                    <div className="flex justify-end gap-1">
                      {!a.cloturee && (
                        <Button
                          variant="icon"
                          size="icon"
                          isLoading={genererMut.isPending}
                          disabled={genererMut.isPending}
                          onClick={() => genererMut.mutate(a.id)}
                          title="Générer les périodes par défaut (trimestres + compositions)"
                        >
                          <Sparkles size={14} strokeWidth={1.75} />
                        </Button>
                      )}
                      {!a.active && !a.cloturee && (
                        <Button
                          variant="icon"
                          tone="success"
                          size="icon"
                          onClick={() => activerMut.mutate(a.id)}
                          title="Activer"
                        >
                          <Power size={14} strokeWidth={1.75} />
                        </Button>
                      )}
                      {!a.active && !a.cloturee && (
                        <Button
                          variant="icon"
                          tone="warning"
                          size="icon"
                          onClick={() => cloturerMut.mutate(a.id)}
                          title="Verrouiller (archiver définitivement cette année déjà inactive)"
                        >
                          <Lock size={14} strokeWidth={1.75} />
                        </Button>
                      )}
                      {!a.cloturee && (
                        <Button
                          variant="icon"
                          tone="danger"
                          size="icon"
                          onClick={() => setDeleting(a)}
                          title="Supprimer"
                        >
                          <Trash2 size={14} strokeWidth={1.75} />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>

      <AnneeScolaireFormDrawer
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
            scheduleDeleteWithUndo(() => deleteMut.mutate(deleting.id), `Année scolaire « ${deleting.libelle} » supprimée.`)
          }
        }}
        title="Supprimer cette année scolaire ?"
        description={`Supprimer "${deleting?.libelle}" supprimera aussi tous les trimestres associés.`}
        confirmLabel="Supprimer"
        variant="danger"
      />
    </div>
  )
}

/* ─── Onglet Sécurité ───────────────────────────────────────────── */

const ROLE_LABELS: Record<string, string> = {
  admin: 'Administrateur',
  directeur: 'Directeur',
  comptable: 'Comptable',
}

function SecuriteTab() {
  const { user } = useAuth()
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})
  const [ancien, setAncien] = useState('')
  const [nouveau, setNouveau] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Errors>({})

  const toggle = (field: string) => setShowPasswords((p) => ({ ...p, [field]: !p[field] }))

  const changerMotDePasse = useMutation({
    mutationFn: async () => {
      await api.put(`/api/auth/utilisateurs/${user?.id}/mot-de-passe`, {
        ancien_mot_de_passe: ancien,
        nouveau_mot_de_passe: nouveau,
      })
    },
    onSuccess: () => {
      toast('Mot de passe modifié avec succès.')
      setAncien('')
      setNouveau('')
      setConfirmation('')
      setFieldErrors({})
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const errs: Errors = {}
    const ancienErr = required(ancien, 'Le mot de passe actuel')
    const nouveauErr = required(nouveau, 'Le nouveau mot de passe') ?? minLength(nouveau, 8, 'Le nouveau mot de passe')
    const confirmErr = required(confirmation, 'La confirmation')
    if (ancienErr) errs.ancien = ancienErr
    if (nouveauErr) errs.nouveau = nouveauErr
    if (confirmErr) errs.confirmation = confirmErr
    if (!nouveauErr && !confirmErr && nouveau !== confirmation) {
      errs.confirmation = 'Les deux mots de passe ne correspondent pas.'
    }
    setFieldErrors(errs)
    if (hasErrors(errs)) return
    changerMotDePasse.mutate()
  }

  const passwordFields: [string, string, string][] = [
    ['Mot de passe actuel', 'ancien', ancien],
    ['Nouveau mot de passe', 'nouveau', nouveau],
    ['Confirmer le nouveau', 'confirmation', confirmation],
  ]

  return (
    <div className="space-y-5">
      <SectionTitle>Sécurité & Accès</SectionTitle>

      {/* Compte connecté */}
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] p-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-ink)]">
          <Lock size={14} strokeWidth={1.75} />
          Compte connecté
        </div>
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-ink-faint)]">Nom complet</div>
            <div className="mt-0.5 text-sm font-medium text-[var(--color-ink)]">
              {user?.prenom} {user?.nom}
            </div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-ink-faint)]">E-mail</div>
            <div className="mt-0.5 text-sm font-medium text-[var(--color-ink)]">{user?.email}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-ink-faint)]">Rôle</div>
            <div className="mt-0.5">
              <Badge tone="neutral">{user?.role ? ROLE_LABELS[user.role] ?? user.role : '—'}</Badge>
            </div>
          </div>
        </div>
      </div>

      {/* Changement de mot de passe */}
      <form onSubmit={handleSubmit} className="rounded-lg border border-[var(--color-border)] p-4" noValidate>
        <div className="text-xs font-semibold text-[var(--color-ink)]">Changer mon mot de passe</div>
        <p className="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">
          Utilisez au moins 8 caractères. Vous devrez confirmer votre ancien mot de passe.
        </p>

        <div className="mt-4 flex max-w-md flex-col gap-4">
          {passwordFields.map(([label, field, value]) => (
            <div key={field}>
              <label className="mb-1 block text-xs font-medium text-[var(--color-ink-dim)]">{label}</label>
              <div className="relative">
                <Input
                  type={showPasswords[field] ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={value}
                  onChange={(e) => {
                    const v = e.target.value
                    if (field === 'ancien') setAncien(v)
                    else if (field === 'nouveau') setNouveau(v)
                    else setConfirmation(v)
                    if (fieldErrors[field]) setFieldErrors((p) => ({ ...p, [field]: undefined }))
                  }}
                  autoComplete={field === 'ancien' ? 'current-password' : 'new-password'}
                  className="pr-10"
                  error={fieldErrors[field]}
                />
                <button
                  type="button"
                  onClick={() => toggle(field)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--color-ink-faint)] hover:text-[var(--color-ink-dim)]"
                >
                  {showPasswords[field] ? <EyeOff size={14} strokeWidth={1.75} /> : <Eye size={14} strokeWidth={1.75} />}
                </button>
              </div>
            </div>
          ))}

          <div className="flex justify-end">
            <Button type="submit" variant="primary" isLoading={changerMotDePasse.isPending}>
              Mettre à jour le mot de passe
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}

/* ─── Onglet Utilisateurs ───────────────────────────────────────── */

function UtilisateursTab() {
  return <UtilisateurListPage />
}



