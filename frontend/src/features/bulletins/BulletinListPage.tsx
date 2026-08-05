import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Printer, Search, FileText, Loader2 } from 'lucide-react'
import { Card, CardBody } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Spinner } from '@/components/ui/Spinner'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { Avatar } from '@/components/ui/Avatar'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { formatMoyenne } from '@/lib/format'
import { baremeNiveau } from '@/lib/bareme'
import { useAuth } from '@/auth/useAuth'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchClasses } from '@/features/classes/api'
import { fetchTrimestres } from '@/features/trimestres/api'
import {
  fetchBulletins,
  fetchBulletinDetail,
  genererBulletinClasse,
  publierBulletins,
  depublierBulletins,
} from './api'
import type { BulletinDetailFull } from './types'

function noteColor(n: number | null, bareme: number = 20): string {
  if (n == null) return 'var(--color-ink-dim)'
  const pct = n / bareme
  if (pct >= 0.7) return 'var(--color-success)'
  if (pct >= 0.5) return 'var(--color-ink)'
  return 'var(--color-danger)'
}

function getNiveauNumber(niveau: string): number {
  const cleaned = niveau.replace(/[èe]re?/, '').trim()
  const n = parseInt(cleaned, 10)
  if (isNaN(n)) return 0
  return n
}

const PERIOD_TYPE = {
  TRIMESTRE: 'TRIMESTRE',
  COMPOSITION: 'COMPOSITION',
} as const

export default function BulletinListPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'admin' || user?.role === 'directeur'
  const qc = useQueryClient()
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: annees = [] } = useQuery({ queryKey: ['annees'], queryFn: () => fetchAnneesScolaires() })
  const activeAnnee = annees.find((a) => a.active)

  const [anneeId, setAnneeId] = useState('')
  const [classeId, setClasseId] = useState('')
  const [trimestreId, setTrimestreId] = useState('')
  const [search, setSearch] = useState('')

  const prevClasseRef = useRef(classeId)

  useEffect(() => {
    if (activeAnnee && !anneeId) {
      setAnneeId(String(activeAnnee.id))
    }
  }, [activeAnnee, anneeId])

  const { data: trimestres = [] } = useQuery({
    queryKey: ['trimestres', anneeId],
    queryFn: () => fetchTrimestres(anneeId ? Number(anneeId) : undefined),
    enabled: !!anneeId,
  })

  const selectedClasse = classes.find((c) => c.id === Number(classeId))
  const classeNiveau = selectedClasse?.niveau ?? ''
  const bareme = baremeNiveau(classeNiveau)

  const filteredTrimestres = useMemo(() => {
    if (!classeNiveau || !trimestres.length) return trimestres
    const niveauNum = getNiveauNumber(classeNiveau)
    const expectedType = niveauNum <= 6 ? PERIOD_TYPE.COMPOSITION : PERIOD_TYPE.TRIMESTRE
    return trimestres.filter((t) => t.type === expectedType)
  }, [classeNiveau, trimestres])

  useEffect(() => {
    if (prevClasseRef.current !== classeId && classeId) {
      setTrimestreId('')
    }
    prevClasseRef.current = classeId
  }, [classeId])

  const [previewId, setPreviewId] = useState<number | null>(null)

  const { data: bulletins = [], isLoading } = useQuery({
    queryKey: ['bulletins', classeId, trimestreId],
    queryFn: () => fetchBulletins({
      ...(classeId ? { id_classe: Number(classeId) } : {}),
      ...(trimestreId ? { id_trimestre: Number(trimestreId) } : {}),
    }),
    enabled: !!classeId && !!trimestreId,
  })

  const { data: bulletinDetail, isLoading: loadingDetail } = useQuery({
    queryKey: ['bulletin-detail', previewId],
    queryFn: () => fetchBulletinDetail(previewId!),
    enabled: !!previewId,
  })

  const genererMut = useMutation({
    mutationFn: genererBulletinClasse,
    onSuccess: (data) => {
      toast(`${data.length} bulletin(s) généré(s)`)
      qc.invalidateQueries({ queryKey: ['bulletins'] })
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const publierMut = useMutation({
    mutationFn: publierBulletins,
    onSuccess: (data) => {
      toast(`${data.length} bulletin(s) publié(s)`)
      qc.invalidateQueries({ queryKey: ['bulletins'] })
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const depublierMut = useMutation({
    mutationFn: depublierBulletins,
    onSuccess: () => {
      toast('Bulletins dépubliés')
      qc.invalidateQueries({ queryKey: ['bulletins'] })
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    if (!q) return bulletins
    return bulletins.filter((b) => b.matricule_eleve.toLowerCase().includes(q))
  }, [bulletins, search])

  const classeLabel = classes.find((c) => String(c.id) === classeId)
  const trimestreLabel = filteredTrimestres.find((t) => String(t.id) === trimestreId)

  const handlePrint = () => window.print()

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
              Bulletins scolaires
            </h2>
            <p className="mt-1 text-sm text-[var(--color-ink-dim)]">
              Moyennes, rangs et appréciations calculés à partir des notes saisies
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-end gap-3">
          <Select label="Année" value={anneeId} onChange={(e) => setAnneeId(e.target.value)}>
            <option value="">— Choisir une année —</option>
            {annees.map((a) => (
              <option key={a.id} value={a.id}>{a.libelle}</option>
            ))}
          </Select>
          <Select label="Classe" value={classeId} onChange={(e) => setClasseId(e.target.value)}>
            <option value="">— Choisir une classe —</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.niveau} — {c.nom}</option>
            ))}
          </Select>
          <Select label="Période" value={trimestreId} onChange={(e) => setTrimestreId(e.target.value)}>
            <option value="">— Choisir une période —</option>
            {filteredTrimestres.map((t) => (
              <option key={t.id} value={t.id}>{t.nom}</option>
            ))}
          </Select>
          {canWrite && (
            <Button
              variant="primary"
              disabled={!classeId || !trimestreId}
              onClick={() => genererMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
            >
              {genererMut.isPending ? (
                <Loader2 size={14} strokeWidth={1.75} className="mr-1.5 animate-spin" />
              ) : null}
              Générer pour la classe
            </Button>
          )}
          {canWrite && classeId && trimestreId && (
            <>
              <Button
                variant="secondary"
                onClick={() => publierMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
              >
                Publier
              </Button>
              <Button
                variant="ghost"
                onClick={() => depublierMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
              >
                Dépublier
              </Button>
            </>
          )}
        </div>

        {classes.length === 0 && (
          <div className="rounded-lg border border-[var(--color-warning)]/20 bg-[var(--color-warning-wash)] px-4 py-3 text-sm text-[var(--color-warning)]">
            Aucune classe n'est encore créée.
          </div>
        )}

        {classes.length > 0 && (!classeId || !trimestreId) && (
          <EmptyState message="Veuillez sélectionner une classe et une période." />
        )}

        {classeId && trimestreId && (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative max-w-sm flex-1">
                <Search strokeWidth={1.75} className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--color-ink-faint)]" />
                <Input
                  placeholder="Rechercher par matricule…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
              <span className="text-xs text-[var(--color-ink-dim)]">{filtered.length} élève(s)</span>
            </div>

            {isLoading ? (
              <TableSkeleton rows={8} />
            ) : filtered.length === 0 ? (
              <div className="py-16">
                <EmptyState message={search ? 'Aucun élève trouvé.' : 'Aucun bulletin pour cette classe / période.'} />
              </div>
            ) : (
              <Card>
                <div className="border-b border-[var(--color-border-soft)] px-5 py-3">
                  <span className="text-sm font-semibold text-[var(--color-ink)]">
                    {classeLabel?.niveau} {classeLabel?.nom} — {trimestreLabel?.nom}
                  </span>
                </div>
                <CardBody>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-[var(--color-border)]">
                          <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Élève</th>
                          <th className="pb-3 text-center font-medium text-[var(--color-ink-dim)]">Rang</th>
                          <th className="pb-3 text-center font-medium text-[var(--color-ink-dim)]">Moyenne</th>
                          <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Appréciation</th>
                          <th className="pb-3 text-left font-medium text-[var(--color-ink-dim)]">Statut</th>
                          <th className="pb-3 text-right font-medium text-[var(--color-ink-dim)]">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[var(--color-border-soft)]">
                        {filtered.map((b) => (
                          <tr key={b.id} className="hover:bg-[var(--color-surface-2)]">
                            <td className="py-3">
                              <div className="flex items-center gap-3">
                                {b.eleve ? (
                                  <>
                                    <Avatar nom={b.eleve.nom} prenom={b.eleve.prenom} photo={b.eleve.photo} size="sm" />
                                    <span className="font-medium text-[var(--color-ink)]">
                                      {b.eleve.prenom} {b.eleve.nom}
                                    </span>
                                  </>
                                ) : (
                                  <span className="text-[var(--color-ink-dim)]">—</span>
                                )}
                              </div>
                            </td>
                            <td className="py-3 text-center">
                              <span className="text-sm font-medium" style={{ color: b.rang != null && b.rang <= 3 ? 'var(--color-brand-bright)' : 'var(--color-ink)' }}>
                                {b.rang != null ? `${b.rang}${b.rang === 1 ? 'er' : 'e'}` : '—'}
                              </span>
                            </td>
                            <td className="py-3 text-center">
                              <span className="text-sm font-medium" style={{ color: noteColor(b.moyenne_generale, bareme) }}>
                                {formatMoyenne(b.moyenne_generale, bareme)}
                              </span>
                            </td>
                            <td className="py-3 text-xs text-[var(--color-ink-dim)]">
                              {b.appreciation ?? '—'}
                            </td>
                            <td className="py-3">
                              <Badge tone={b.statut === 'PUBLIE' ? 'success' : 'neutral'}>
                                {b.statut === 'PUBLIE' ? 'Publié' : 'Brouillon'}
                              </Badge>
                            </td>
                            <td className="py-3 text-right">
                              <button
                                onClick={() => setPreviewId(b.id)}
                                className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                              >
                                <FileText size={14} strokeWidth={1.75} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardBody>
              </Card>
            )}
          </>
        )}
      </div>

      {previewId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 no-print">
          <div className="mx-4 max-h-[90vh] w-[700px] overflow-y-auto rounded-lg bg-white shadow-2xl print-area">
            {loadingDetail ? (
              <div className="flex items-center justify-center py-20">
                <Spinner label="Chargement du bulletin…" />
              </div>
            ) : bulletinDetail ? (
              <>
                <BulletinHeader bulletin={bulletinDetail} />
                <BulletinStudentInfo bulletin={bulletinDetail} bareme={baremeNiveau(bulletinDetail.classe.niveau)} />
                <BulletinGradesTable bulletin={bulletinDetail} bareme={baremeNiveau(bulletinDetail.classe.niveau)} />
                <BulletinAppreciation bulletin={bulletinDetail} />
                <BulletinSignatures />
                <div className="flex justify-end gap-2 border-t border-[var(--color-border-soft)] px-8 py-4 no-print">
                  <Button variant="secondary" onClick={() => setPreviewId(null)}>
                    Fermer
                  </Button>
                  <Button variant="primary" onClick={handlePrint}>
                    <Printer size={14} strokeWidth={1.75} className="mr-1.5" />
                    Imprimer / PDF
                  </Button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}

function BulletinHeader({ bulletin }: { bulletin: BulletinDetailFull }) {
  return (
    <div className="flex items-center gap-4 bg-[var(--color-base)] px-8 py-5 text-[var(--color-ink)]">
      <div className="flex size-12 shrink-0 items-center justify-center rounded-lg bg-white/20 text-lg font-semibold">
        A
      </div>
      <div className="flex-1">
        <div className="text-[11px] uppercase tracking-widest opacity-70">Collège Auréole</div>
        <h2 className="mt-1 text-lg font-semibold">Bulletin scolaire</h2>
        <div className="text-xs opacity-80">
          {bulletin.trimestre.nom} · {bulletin.classe.niveau} {bulletin.classe.nom}
        </div>
      </div>
      <Link to={`/app/eleves/${bulletin.eleve.matricule}`} className="shrink-0">
        <Avatar nom={bulletin.eleve.nom} prenom={bulletin.eleve.prenom} photo={bulletin.eleve.photo} size="lg" />
      </Link>
    </div>
  )
}

function BulletinStudentInfo({ bulletin, bareme }: { bulletin: BulletinDetailFull; bareme: number }) {
  const info: [string, string | number | null | React.ReactNode][] = [
    ['Nom & Prénom', <Link key="link" to={`/app/eleves/${bulletin.eleve.matricule}`} className="hover:text-[var(--color-brand-bright)]">{bulletin.eleve.nom} {bulletin.eleve.prenom}</Link>],
    ['Classe', `${bulletin.classe.niveau} ${bulletin.classe.nom}`],
    ['Rang', bulletin.rang ? `${bulletin.rang}e` : '—'],
    ['Moyenne générale', bulletin.moyenne_generale != null ? `${bulletin.moyenne_generale}/${bareme}` : '—'],
    ['Matricule', bulletin.eleve.matricule],
  ]

  return (
    <div className="border-b border-[var(--color-border-soft)] bg-[var(--color-surface-2)] px-8 py-4">
      <div className="grid grid-cols-3 gap-4">
        {info.map(([label, value]) => (
          <div key={label}>
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-ink-faint)]">{label}</div>
            <div className="mt-0.5 text-sm font-semibold text-[var(--color-ink)]">{value ?? '—'}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function BulletinGradesTable({ bulletin, bareme }: { bulletin: BulletinDetailFull; bareme: number }) {
  return (
    <div className="px-8 py-4">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-[var(--color-border-soft)]">
            {['Matière', 'Moyenne', 'Coeff'].map((h) => (
              <th key={h} className="py-2 text-left font-semibold uppercase tracking-wide text-[var(--color-ink-faint)]">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bulletin.details.map((d) => (
            <tr key={d.id} className="border-b border-[var(--color-surface-2)]">
              <td className="py-2 font-medium text-[var(--color-ink)]">{d.cours_nom}</td>
              <td className="py-2 font-medium" style={{ color: noteColor(d.moyenne, bareme) }}>
                {d.moyenne != null ? `${d.moyenne}/${bareme}` : '—'}
              </td>
              <td className="py-2 text-[var(--color-ink-dim)]">{d.coefficient}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function BulletinAppreciation({ bulletin }: { bulletin: BulletinDetailFull }) {
  if (!bulletin.appreciation) return null
  return (
    <div className="mx-8 mb-4 rounded border border-[var(--color-brand-blue)]/20 bg-[var(--color-brand-blue)]/5 px-5 py-3">
      <div className="mb-1 text-[11px] font-medium uppercase tracking-wide text-[var(--color-brand-blue)]">
        Appréciation générale
      </div>
      <p className="text-xs italic text-[var(--color-ink-dim)]" style={{ lineHeight: 1.6 }}>
        {bulletin.appreciation}
      </p>
    </div>
  )
}

function BulletinSignatures() {
  const roles = ["Chef d'établissement", "Professeur principal", "Signature des parents"]
  return (
    <div className="grid grid-cols-3 gap-6 px-8 pb-6">
      {roles.map((r) => (
        <div key={r} className="text-center">
          <div className="mb-5 text-[10px] text-[var(--color-ink-faint)]">{r}</div>
          <div className="border-b border-[var(--color-border)]" style={{ height: 40 }} />
        </div>
      ))}
    </div>
  )
}
