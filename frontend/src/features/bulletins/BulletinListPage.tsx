import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Printer, Search, FileText, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Spinner } from '@/components/ui/Spinner'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { EmptyState } from '@/components/ui/EmptyState'
import { Avatar } from '@/components/ui/Avatar'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { formatMoyenne } from '@/lib/format'
import { baremeNiveau } from '@/lib/bareme'
import { useAuth } from '@/auth/useAuth'
import { useEtablissement } from '@/features/etablissement/useEtablissement'
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
import { BulletinDocument } from './BulletinDocument'
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

  const { data: bulletins = [], isLoading, isError } = useQuery({
    queryKey: ['bulletins', classeId, trimestreId],
    queryFn: () => fetchBulletins({
      ...(classeId ? { id_classe: Number(classeId) } : {}),
      ...(trimestreId ? { id_trimestre: Number(trimestreId) } : {}),
    }),
    enabled: !!classeId && !!trimestreId,
  })

  const hasBulletins = bulletins.length > 0
  const hasPublished = bulletins.some((b) => b.statut === 'PUBLIE')

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
  const anneeLabel = annees.find((a) => String(a.id) === anneeId)?.libelle
  const { data: etab } = useEtablissement()

  const handlePrint = () => window.print()

  /* ── Impression de toute la classe ──────────────────────────────────── */
  const [batchOpen, setBatchOpen] = useState(false)
  const [batchDetails, setBatchDetails] = useState<BulletinDetailFull[] | null>(null)

  const ouvrirImpressionClasse = async () => {
    setBatchOpen(true)
    setBatchDetails(null)
    try {
      const details = await Promise.all(bulletins.map((b) => fetchBulletinDetail(b.id)))
      details.sort((a, b) => (a.rang ?? Number.MAX_SAFE_INTEGER) - (b.rang ?? Number.MAX_SAFE_INTEGER))
      setBatchDetails(details)
    } catch (e) {
      toast(extractErrorMessage(e, 'Impossible de préparer les bulletins.'), 'error')
      setBatchOpen(false)
    }
  }

  useEffect(() => {
    if (!batchOpen || !batchDetails) return
    // Laisse le temps au navigateur de peindre les documents (et charger les logos).
    const t = setTimeout(() => window.print(), 400)
    return () => clearTimeout(t)
  }, [batchOpen, batchDetails])

  useEffect(() => {
    if (!batchOpen) return
    const fermer = () => setBatchOpen(false)
    window.addEventListener('afterprint', fermer)
    return () => window.removeEventListener('afterprint', fermer)
  }, [batchOpen])

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
              disabled={!classeId || !trimestreId || isLoading || hasPublished}
              title={hasPublished ? 'Bulletins publiés — dépublié pour régénérer' : undefined}
              onClick={() => genererMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
            >
              {genererMut.isPending ? (
                <Loader2 size={14} strokeWidth={1.75} className="mr-1.5 animate-spin" />
              ) : null}
              {hasPublished ? 'Bulletins publiés' : 'Générer pour la classe'}
            </Button>
          )}
          {canWrite && classeId && trimestreId && (
            <>
              <Button
                variant="secondary"
                disabled={!hasBulletins || hasPublished || publierMut.isPending}
                title={hasPublished ? 'Déjà publiés' : !hasBulletins ? 'Aucun bulletin à publier' : undefined}
                onClick={() => publierMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
              >
                Publier
              </Button>
              <Button
                variant="ghost"
                disabled={!hasPublished || depublierMut.isPending}
                title={!hasPublished ? 'Aucun bulletin publié' : undefined}
                onClick={() => depublierMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
              >
                Dépublier
              </Button>
            </>
          )}
        </div>

        {classes.length === 0 && (
          <div className="py-16">
            <EmptyState message="Aucune classe n'est encore créée." />
          </div>
        )}

        {classes.length > 0 && (!classeId || !trimestreId) && (
          <div className="py-16">
            <EmptyState message="Veuillez sélectionner une classe et une période." />
          </div>
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
              <Button
                variant="secondary"
                className="ml-auto"
                disabled={!hasBulletins}
                isLoading={batchOpen && !batchDetails}
                onClick={ouvrirImpressionClasse}
              >
                <Printer size={14} strokeWidth={1.75} className="mr-1.5" />
                Imprimer toute la classe
              </Button>
            </div>

            {isLoading ? (
              <TableSkeleton rows={8} />
            ) : isError ? (
              <div className="py-16">
                <EmptyState message="Impossible de charger les bulletins." />
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-16">
                <EmptyState message={search ? 'Aucun élève trouvé.' : 'Aucun bulletin pour cette classe / période.'} />
              </div>
            ) : (
              <Card className="overflow-hidden">
                <div className="border-b border-[var(--color-border-soft)] px-5 py-3">
                  <span className="text-sm font-semibold text-[var(--color-ink)]">
                    {classeLabel?.niveau} {classeLabel?.nom} — {trimestreLabel?.nom}
                  </span>
                </div>
                <TableContainer className="rounded-none border-0">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Élève</TableHead>
                        <TableHead className="text-center">Rang</TableHead>
                        <TableHead className="text-center">Moyenne</TableHead>
                        <TableHead>Appréciation</TableHead>
                        <TableHead>Statut</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filtered.map((b) => (
                        <TableRow key={b.id}>
                          <TableCell>
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
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="text-sm font-medium" style={{ color: b.rang != null && b.rang <= 3 ? 'var(--color-brand-bright)' : 'var(--color-ink)' }}>
                              {b.rang != null ? `${b.rang}${b.rang === 1 ? 'er' : 'e'}` : '—'}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="text-sm font-medium" style={{ color: noteColor(b.moyenne_generale, bareme) }}>
                              {formatMoyenne(b.moyenne_generale, bareme)}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-[var(--color-ink-dim)]">
                            {b.appreciation ?? '—'}
                          </TableCell>
                          <TableCell>
                            <Badge tone={b.statut === 'PUBLIE' ? 'success' : 'neutral'}>
                              {b.statut === 'PUBLIE' ? 'Publié' : 'Brouillon'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right">
                            <button
                              onClick={() => setPreviewId(b.id)}
                              className="rounded-[var(--radius-sm)] p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]"
                            >
                              <FileText size={14} strokeWidth={1.75} />
                            </button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Card>
            )}
          </>
        )}
      </div>

      {(previewId || batchOpen) && (
        <div className="print-root fixed inset-0 z-50 overflow-y-auto bg-black/50 px-4 py-6">
          <div className="mx-auto mb-5 flex w-fit gap-2 no-print">
            <Button variant="secondary" onClick={() => { setPreviewId(null); setBatchOpen(false) }}>
              Fermer
            </Button>
            <Button variant="primary" onClick={handlePrint} disabled={batchOpen && !batchDetails}>
              <Printer size={14} strokeWidth={1.75} className="mr-1.5" />
              Imprimer / PDF
            </Button>
          </div>

          {previewId && !batchOpen ? (
            loadingDetail ? (
              <div className="flex justify-center py-20 no-print">
                <Spinner label="Chargement du bulletin…" />
              </div>
            ) : bulletinDetail ? (
              <BulletinDocument
                detail={bulletinDetail}
                bareme={baremeNiveau(bulletinDetail.classe.niveau)}
                effectif={bulletins.length}
                anneeLabel={anneeLabel}
                etab={etab}
              />
            ) : null
          ) : batchDetails ? (
            batchDetails.map((d) => (
              <BulletinDocument
                key={d.id}
                detail={d}
                bareme={baremeNiveau(d.classe.niveau)}
                effectif={batchDetails.length}
                anneeLabel={anneeLabel}
                etab={etab}
              />
            ))
          ) : (
            <div className="flex justify-center py-20">
              <Spinner label="Préparation des bulletins…" />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
