import { useState } from 'react'
import { clsx } from 'clsx'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Trash2, Power, Lock, CalendarOff,
  Sparkles, Building2, Download, Users,
} from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { PageHeader } from '@/components/ui/PageHeader'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { Tooltip } from '@/components/ui/Tooltip'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { scheduleDeleteWithUndo } from '@/lib/undoDelete'
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
import UtilisateursTab from '@/features/parametres/UtilisateursTab'
import type { AnneeScolaire, AnneeScolaireCreateInput } from '@/features/annees_scolaires/types'

type Tab = 'fiche' | 'annees' | 'utilisateurs' | 'export'

const tabs: { id: Tab; label: string; icon: typeof Lock }[] = [
  { id: 'fiche', label: "Fiche établissement", icon: Building2 },
  { id: 'annees', label: 'Années scolaires', icon: CalendarOff },
  { id: 'utilisateurs', label: 'Utilisateurs', icon: Users },
  { id: 'export', label: 'Export des données', icon: Download },
]

export default function ParametresPage() {
  const [activeTab, setActiveTab] = useState<Tab>('annees')

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Paramètres"
          subtitle={
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              Configuration du système de gestion scolaire
            </p>
          }
        />

        <div className="flex gap-6">
          <div className="w-44 shrink-0 space-y-1">
            {tabs.map((t) => {
              const Icon = t.icon
              const active = activeTab === t.id
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={clsx(
                    'flex w-full items-center gap-3 rounded-[var(--radius-sm)] border border-transparent px-3 py-2.5 text-left text-sm transition-colors',
                    active
                      ? 'border-[var(--color-action-wash)] bg-[var(--color-action-wash)] text-[var(--color-action)]'
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
      <div className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger-wash)] px-4 py-3 text-sm text-[var(--color-danger)]">
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
                  <TableCell className="font-medium text-[var(--color-ink)]">{a.libelle}</TableCell>
                  <TableCell className="text-[var(--color-ink-dim)]">
                    {new Date(a.date_debut).toLocaleDateString('fr-FR')} — {new Date(a.date_fin).toLocaleDateString('fr-FR')}
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1.5">
                      {a.active && <Badge tone="success">Active</Badge>}
                      {a.cloturee && <Badge tone="neutral">Clôturée</Badge>}
                      {!a.active && !a.cloturee && <Badge tone="info">Inactive</Badge>}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-1">
                      {!a.cloturee && (
                        <Tooltip content="Générer les périodes par défaut (trimestres + compositions)">
                          <Button
                            variant="icon"
                            size="icon"
                            isLoading={genererMut.isPending}
                            disabled={genererMut.isPending}
                            onClick={() => genererMut.mutate(a.id)}
                          >
                            <Sparkles size={14} strokeWidth={1.75} />
                          </Button>
                        </Tooltip>
                      )}
                      {!a.active && !a.cloturee && (
                        <Tooltip content="Activer">
                          <Button
                            variant="icon"
                            tone="success"
                            size="icon"
                            onClick={() => activerMut.mutate(a.id)}
                          >
                            <Power size={14} strokeWidth={1.75} />
                          </Button>
                        </Tooltip>
                      )}
                      {!a.active && !a.cloturee && (
                        <Tooltip content="Verrouiller (archiver définitivement cette année déjà inactive)">
                          <Button
                            variant="icon"
                            tone="warning"
                            size="icon"
                            onClick={() => cloturerMut.mutate(a.id)}
                          >
                            <Lock size={14} strokeWidth={1.75} />
                          </Button>
                        </Tooltip>
                      )}
                      {!a.cloturee && (
                        <Tooltip content="Supprimer">
                          <Button
                            variant="icon"
                            tone="danger"
                            size="icon"
                            onClick={() => setDeleting(a)}
                          >
                            <Trash2 size={14} strokeWidth={1.75} />
                          </Button>
                        </Tooltip>
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



