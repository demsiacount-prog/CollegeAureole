import { useState, useRef } from 'react'
import { clsx } from 'clsx'
import { useAuth } from '@/auth/useAuth'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Trash2, Power, Lock, Shield, Users, Database, CalendarOff,
  CheckCircle, Upload, Loader2, Eye, EyeOff, Download, FileDown, ArrowRight, Sparkles,
} from 'lucide-react'
import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage, api } from '@/lib/api'
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
import type { AnneeScolaire, AnneeScolaireCreateInput } from '@/features/annees_scolaires/types'

type Tab =  'annees' | 'securite' | 'utilisateurs' | 'donnees' | 'cloture'

const tabs: { id: Tab; label: string; icon: typeof Shield }[] = [
  { id: 'annees', label: 'Années scolaires', icon: CalendarOff },
  { id: 'securite', label: 'Sécurité', icon: Shield },
  { id: 'utilisateurs', label: 'Utilisateurs', icon: Users },
  { id: 'donnees', label: 'Données', icon: Database },
  { id: 'cloture', label: "Clôture d'année", icon: Lock },
]

export default function ParametresPage() {
  const { user } = useAuth()
  const visibleTabs = tabs.filter((t) => t.id !== 'utilisateurs' || user?.role === 'admin')
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
            {activeTab === 'annees' && <AnneesTab />}
            {activeTab === 'securite' && <SecuriteTab />}
            {activeTab === 'utilisateurs' && <UtilisateursTab />}
            {activeTab === 'donnees' && <DonneesTab />}
            {activeTab === 'cloture' && <ClotureTab />}
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
        <CardBody>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[var(--color-border)]">
                  <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Libellé</th>
                  <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Période</th>
                  <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Statut</th>
                  <th className="pb-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border-soft)]">
                {annees.map((a) => (
                  <tr key={a.id} className="hover:bg-[var(--color-surface-2)]">
                    <td className="py-3 font-medium text-[var(--color-ink)]">{a.libelle}</td>
                    <td className="py-3 text-[var(--color-ink-dim)]">
                      {new Date(a.date_debut).toLocaleDateString('fr-FR')} — {new Date(a.date_fin).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="py-3">
                      <div className="flex gap-1.5">
                        {a.active && <Badge tone="success">Active</Badge>}
                        {a.cloturee && <Badge tone="neutral">Clôturée</Badge>}
                        {!a.active && !a.cloturee && <Badge tone="info">Inactive</Badge>}
                      </div>
                    </td>
                    <td className="py-3 text-right">
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
                    </td>
                  </tr>
                ))}
                {annees.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-sm text-[var(--color-ink-dim)]">
                      Aucune année scolaire enregistrée.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardBody>
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

function SecuriteTab() {
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({})

  const toggle = (field: string) => setShowPasswords((p) => ({ ...p, [field]: !p[field] }))

  const fields: [string, string][] = [
    ['Mot de passe actuel', 'password'],
    ['Nouveau mot de passe', 'newPass'],
    ['Confirmer', 'confirmPass'],
  ]

  return (
    <div className="space-y-4">
      <SectionTitle>Sécurité & Accès</SectionTitle>
      <div className="grid grid-cols-2 gap-4">
        {fields.map(([label, field]) => (
          <div key={field}>
            <label className="mb-1 block text-xs font-medium text-[var(--color-ink-dim)]">{label}</label>
            <div className="relative">
              <Input
                type={showPasswords[field] ? 'text' : 'password'}
                placeholder="••••••••"
                className="pr-10"
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
      </div>
      <div className="rounded border border-[var(--color-danger)]/20 bg-[var(--color-danger-wash)] p-4">
        <div className="text-xs font-semibold text-[var(--color-danger)]">Zone d'administration</div>
        <div className="mt-1 text-[11px] text-[var(--color-danger)]/80">
          Toutes les actions sont journalisées. L'accès est réservé au directeur et au secrétariat.
        </div>
      </div>
    </div>
  )
}

/* ─── Onglet Utilisateurs ───────────────────────────────────────── */

function UtilisateursTab() {
  return <UtilisateurListPage />
}

function downloadFile(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function toCsv(rows: Record<string, unknown>[], headers: string[]): string {
  const escape = (v: unknown) => {
    const s = v == null ? '' : String(v)
    return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s.replace(/"/g, '""')}"` : s
  }
  return [headers.join(','), ...rows.map((r) => headers.map((h) => escape(r[h])).join(','))].join('\n')
}

function DonneesTab() {
  const qc = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [importStatus, setImportStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [importMessage, setImportMessage] = useState('')
  const [exporting, setExporting] = useState<string | null>(null)
  const [purgeConfirm, setPurgeConfirm] = useState(false)

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setImportStatus('loading')
    setImportMessage('Importation en cours…')
    const reader = new FileReader()
    reader.onload = (evt) => {
      try {
        const data = JSON.parse(evt.target?.result as string)
        const count = Array.isArray(data) ? data.length : Object.keys(data).length
        setImportStatus('success')
        setImportMessage(`Fichier "${file.name}" analysé avec succès (${count} éléments).`)
        qc.invalidateQueries()
      } catch {
        setImportStatus('error')
        setImportMessage('Format invalide. Veuillez fournir un fichier JSON valide.')
      }
    }
    reader.onerror = () => {
      setImportStatus('error')
      setImportMessage('Erreur lors de la lecture du fichier.')
    }
    reader.readAsText(file)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleExportJson() {
    setExporting('json')
    try {
      const [ classes, annees, trimestres, utilisateurs] = await Promise.all([
        api.get('/api/classes/').then((r) => r.data),
        api.get('/api/anneesScolaires/').then((r) => r.data),
        api.get('/api/trimestres/').then((r) => r.data),
        api.get('/api/utilisateurs/').then((r) => r.data),
      ])
      const payload = { export_date: new Date().toISOString(), classes, annees_scolaires: annees, trimestres, utilisateurs }
      downloadFile(JSON.stringify(payload, null, 2), `aureole_export_${new Date().toISOString().slice(0, 10)}.json`, 'application/json')
      toast('Export JSON téléchargé')
    } catch (e) {
      toast(extractErrorMessage(e, "Erreur lors de l'export."), 'error')
    } finally {
      setExporting(null)
    }
  }

  async function handleExportCsv() {
    setExporting('csv')
    try {
      const { data: eleves } = await api.get('/api/eleves/', { params: { limit: 500 } })
      const csv = toCsv(
        eleves.map((e: Record<string, unknown>) => ({
          matricule: e.matricule,
          nom: e.nom,
          prenom: e.prenom,
          sexe: e.sexe,
          date_de_naissance: e.date_de_naissance,
          lieu_de_naissance: e.lieu_de_naissance,
          statut: e.statut,
        })),
        ['matricule', 'nom', 'prenom', 'sexe', 'date_de_naissance', 'lieu_de_naissance', 'statut'],
      )
      downloadFile(csv, `aureole_eleves_${new Date().toISOString().slice(0, 10)}.csv`, 'text/csv')
      toast('Export CSV téléchargé')
    } catch (e) {
      toast(extractErrorMessage(e, "Erreur lors de l'export."), 'error')
    } finally {
      setExporting(null)
    }
  }

  return (
    <div className="space-y-4">
      <SectionTitle>Gestion des données</SectionTitle>

      {/* Import */}
      <div className="rounded border border-[var(--color-brand-blue)]/20 bg-[var(--color-brand-blue)]/5 p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-[var(--color-brand-blue)]">Importer des données</div>
            <div className="mt-0.5 text-[11px] text-[var(--color-brand-blue)]">Chargez un fichier JSON exporté depuis une autre instance</div>
          </div>
          <div>
            <input ref={fileInputRef} type="file" accept=".json" onChange={handleImport} className="hidden" id="import-db-file" />
            <label
              htmlFor="import-db-file"
              className="inline-flex cursor-pointer items-center gap-2 rounded-[var(--radius-sm)] bg-[var(--color-brand)] px-4 py-2 text-xs font-medium text-white transition-colors hover:bg-[var(--color-brand-dark)]"
            >
              {importStatus === 'loading' ? (
                <><Loader2 size={14} className="animate-spin" /> Importation…</>
              ) : (
                <><Upload size={14} strokeWidth={1.75} /> Importer</>
              )}
            </label>
          </div>
        </div>
        {importStatus !== 'idle' && importStatus !== 'loading' && (
          <div
            className="mt-3 flex items-center gap-2 rounded p-2"
            style={{ background: importStatus === 'success' ? 'var(--color-success-wash)' : 'var(--color-danger-wash)' }}
          >
            <CheckCircle
              size={14}
              style={{ color: importStatus === 'success' ? 'var(--color-success)' : 'var(--color-danger)', flexShrink: 0 }}
            />
            <span className="text-xs" style={{ color: importStatus === 'success' ? 'var(--color-success)' : 'var(--color-danger)' }}>
              {importMessage}
            </span>
          </div>
        )}
      </div>

      {/* Export JSON */}
      <div className="flex items-center justify-between rounded border border-[var(--color-border-soft)] p-4">
        <div>
          <div className="text-sm font-medium text-[var(--color-ink)]">Sauvegarder toutes les données</div>
          <div className="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">Exporte l'ensemble des données (élèves, classes, années, trimestres, utilisateurs) en JSON</div>
        </div>
        <Button variant="secondary" onClick={handleExportJson} disabled={exporting === 'json'}>
          {exporting === 'json' ? <Loader2 size={14} strokeWidth={1.75} className="mr-1.5 animate-spin" /> : <Download size={14} strokeWidth={1.75} className="mr-1.5" />}
          Sauvegarder
        </Button>
      </div>

      {/* Export CSV */}
      <div className="flex items-center justify-between rounded border border-[var(--color-border-soft)] p-4">
        <div>
          <div className="text-sm font-medium text-[var(--color-ink)]">Exporter les élèves en CSV</div>
          <div className="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">Liste des élèves au format tableur (matricule, nom, prénom, sexe, dates, statut)</div>
        </div>
        <Button variant="secondary" onClick={handleExportCsv} disabled={exporting === 'csv'}>
          {exporting === 'csv' ? <Loader2 size={14} strokeWidth={1.75} className="mr-1.5 animate-spin" /> : <FileDown size={14} strokeWidth={1.75} className="mr-1.5" />}
          Exporter CSV
        </Button>
      </div>

      {/* Purge */}
      <div className="flex items-center justify-between rounded border border-[var(--color-danger)]/20 bg-[var(--color-danger-wash)] p-4">
        <div>
          <div className="text-sm font-medium text-[var(--color-danger)]">Réinitialiser la base de données</div>
          <div className="mt-0.5 text-[11px] text-[var(--color-danger)]/70">Supprime les notes, absences, bulletins et paiements. Les élèves et classes sont conservés.</div>
        </div>
        <Button variant="danger" onClick={() => setPurgeConfirm(true)}>
          <Trash2 size={14} strokeWidth={1.75} className="mr-1.5" />
          Réinitialiser
        </Button>
      </div>

      <ConfirmDialog
        open={purgeConfirm}
        onClose={() => setPurgeConfirm(false)}
        onConfirm={() => { setPurgeConfirm(false); toast('Réinitialisation : fonctionnalité à configurer côté serveur.') }}
        title="Réinitialiser la base de données ?"
        description="Cette action supprimera les notes, absences, bulletins, paiements et dépenses. Les élèves, classes, enseignants et tuteurs seront conservés."
        confirmLabel="Confirmer la réinitialisation"
        variant="danger"
      />
    </div>
  )
}

/* ─── Onglet Clôture ────────────────────────────────────────────── */

function ClotureTab() {
  return (
    <div className="space-y-4">
      <SectionTitle>Clôture de l'année scolaire</SectionTitle>
      <div className="flex items-start gap-3 rounded border border-[var(--color-brand-border)] bg-[var(--color-brand-wash)] p-5">
        <CalendarOff size={18} strokeWidth={1.75} className="mt-0.5 shrink-0 text-[var(--color-brand)]" />
        <div className="text-sm text-[var(--color-ink)]">
          <p className="font-semibold">La clôture d'année a son propre espace dédié</p>
          <p className="mt-1 text-[var(--color-ink-dim)]">
            Elle nécessite d'abord que chaque élève ait un statut de passage décidé
            (module Résultats), puis une prévisualisation complète avant confirmation —
            un onglet de paramètres n'offre pas assez de place pour ça en toute sécurité.
          </p>
          <Button
            variant="primary"
            to="/app/cloture-annee"
            className="mt-3"
          >
            Ouvrir la clôture d'année <ArrowRight size={14} strokeWidth={1.75} />
          </Button>
        </div>
      </div>
    </div>
  )
}
