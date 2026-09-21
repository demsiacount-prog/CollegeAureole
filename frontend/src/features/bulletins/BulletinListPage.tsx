import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Download, Search, FileText, Loader2 } from 'lucide-react'
import { Card } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { PageHeader } from '@/components/ui/PageHeader'
import { Select } from '@/components/ui/Select'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '@/components/ui/Table'
import { EmptyState } from '@/components/ui/EmptyState'
import { Avatar } from '@/components/ui/Avatar'
import { Tooltip } from '@/components/ui/Tooltip'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { formatMoyenne } from '@/lib/format'
import { baremeNiveau } from '@/lib/bareme'
import { estNiveauJardin } from '@/lib/niveaux'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchClasses } from '@/features/classes/api'
import { fetchEleves } from '@/features/eleves/api'
import { fetchTrimestres } from '@/features/trimestres/api'
import {
  fetchBulletins,
  genererBulletinClasse,
  publierBulletins,
  depublierBulletins,
  downloadBulletinPdf,
  downloadBulletinsClassePdf,
  fetchBulletinPdf,
} from './api'
import { PdfViewerModal } from '@/components/pdf/PdfViewerModal'

function noteColor(n: number | null, bareme: number = 20): string {
  if (n == null) return 'var(--ink-dim)'
  const pct = n / bareme
  if (pct >= 0.7) return 'var(--success)'
  if (pct >= 0.5) return 'var(--ink)'
  return 'var(--danger)'
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
  const canWrite = true
  const qc = useQueryClient()
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses })
  const { data: annees = [] } = useQuery({ queryKey: ['annees'], queryFn: () => fetchAnneesScolaires() })
  const activeAnnee = annees.find((a) => a.active)

  const [anneeId, setAnneeId] = useState('')
  const [classeId, setClasseId] = useState('')
  const [trimestreId, setTrimestreId] = useState('')
  const [search, setSearch] = useState('')

  const selectedAnnee = annees.find((a) => String(a.id) === anneeId)
  const anneeCloturee = selectedAnnee?.cloturee ?? false

  const prevClasseRef = useRef(classeId)

  useEffect(() => {
    if (activeAnnee) {
      setAnneeId(String(activeAnnee.id))
    }
  }, [activeAnnee])

  useEffect(() => {
    setClasseId('')
    setTrimestreId('')
  }, [anneeId])

  const { data: trimestres = [] } = useQuery({
    queryKey: ['trimestres', anneeId],
    queryFn: () => fetchTrimestres(anneeId ? Number(anneeId) : undefined),
    enabled: !!anneeId,
  })

const selectedClasse = classes.find((c) => c.id === Number(classeId))
  const classeNiveau = selectedClasse?.niveau ?? ''
  const bareme = baremeNiveau(classeNiveau)
  const estJardin = estNiveauJardin(classeNiveau)

  const filteredTrimestres = useMemo(() => {
    if (!classeId || !classeNiveau || !trimestres.length) return []
    const niveauNum = getNiveauNumber(classeNiveau)
    // 1ère-5ème : compositions ; 7ème-9ème+lycée : trimestres.
    // 6ème (classe spéciale) : trimestres + compositions intermédiaires.
    if (niveauNum === 6) return trimestres
    const expectedType = niveauNum <= 5 ? PERIOD_TYPE.COMPOSITION : PERIOD_TYPE.TRIMESTRE
    return trimestres.filter((t) => t.type === expectedType)
  }, [classeId, classeNiveau, trimestres])

  useEffect(() => {
    if (prevClasseRef.current !== classeId && classeId) {
      setTrimestreId('')
    }
    prevClasseRef.current = classeId
  }, [classeId])

  const [downloading, setDownloading] = useState<'classe' | number | null>(null)
  const [apercuPdf, setApercuPdf] = useState<{
    data: ArrayBuffer
    titre: string
    imprim: boolean
    onDownload: () => void
  } | null>(null)
  const [apercuLoading, setApercuLoading] = useState<string | null>(null)

  const { data: bulletins = [], isLoading, isError } = useQuery({
    queryKey: ['bulletins', anneeId, classeId, trimestreId],
    queryFn: () => fetchBulletins({
      ...(anneeId ? { annee_id: Number(anneeId) } : {}),
      ...(classeId ? { id_classe: Number(classeId) } : {}),
      ...(trimestreId ? { id_trimestre: Number(trimestreId) } : {}),
    }),
    enabled: !!classeId && !!trimestreId,
  })

  const { data: effectifEleves = [], isLoading: loadingEleves } = useQuery({
    queryKey: ['eleves', 'classe', anneeId, classeId],
    queryFn: () => fetchEleves({
      classe_id: Number(classeId),
      id_annee_scolaire: Number(anneeId),
      limit: 500,
    }),
    enabled: !!classeId && !!anneeId,
  })

  const rows = useMemo(() => {
    const byMatricule = new Map(bulletins.map((b) => [b.matricule_eleve, b]))
    const lignes = effectifEleves.map((e) => ({ eleve: e, bulletin: byMatricule.get(e.matricule) ?? null }))
    lignes.sort((a, b) => {
      const ra = a.bulletin?.rang ?? Infinity
      const rb = b.bulletin?.rang ?? Infinity
      if (ra !== rb) return ra - rb
      return a.eleve.matricule.localeCompare(b.eleve.matricule)
    })
    return lignes
  }, [effectifEleves, bulletins])

  const hasBulletins = bulletins.length > 0
  const hasPublished = bulletins.some((b) => b.statut === 'PUBLIE')

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
    if (!q) return rows
    return rows.filter((r) => r.eleve.matricule.toLowerCase().includes(q))
  }, [rows, search])

  const classeLabel = classes.find((c) => String(c.id) === classeId)
  const trimestreLabel = filteredTrimestres.find((t) => String(t.id) === trimestreId)

  const ouvrirPdf = async (
    cle: string,
    titre: string,
    fetchPdf: () => Promise<ArrayBuffer>,
    onDownload: () => void,
    imprim = false,
  ) => {
    if (apercuLoading) return
    setApercuLoading(cle)
    try {
      const data = await fetchPdf()
      setApercuPdf({ data, titre, imprim, onDownload })
    } catch (err) {
      toast(extractErrorMessage(err, "Impossible d'afficher ce document."), 'error')
    } finally {
      setApercuLoading(null)
    }
  }

  const telechargerClasse = async () => {
    if (!classeId || !trimestreId) return
    setDownloading('classe')
    try {
      await downloadBulletinsClassePdf(Number(classeId), Number(trimestreId))
      toast('Bulletins de la classe téléchargés.')
    } catch (e) {
      toast(extractErrorMessage(e, 'Impossible de télécharger les bulletins.'), 'error')
    } finally {
      setDownloading(null)
    }
  }

  const telechargerUn = async (id: number) => {
    setDownloading(id)
    try {
      await downloadBulletinPdf(id)
      toast('Bulletin téléchargé.')
    } catch (e) {
      toast(extractErrorMessage(e, 'Impossible de télécharger le bulletin.'), 'error')
    } finally {
      setDownloading(null)
    }
  }

  return (
    <div className="w-full">
      <div className="flex flex-col gap-5">
        <PageHeader
          title="Bulletins scolaires"
          subtitle={<p className="mt-1 text-sm text-[var(--ink-dim)]">Moyennes, rangs et appréciations calculés à partir des notes saisies</p>}
        />

        <div className="flex flex-wrap items-end gap-3">
          <Select label="Année" value={anneeId} onChange={(e) => setAnneeId(e.target.value)} disabled={!annees.length}>
            <option value="">— Choisir une année —</option>
            {annees.map((a) => (
              <option key={a.id} value={a.id}>{a.libelle}{a.cloturee ? ' (archivée)' : ''}</option>
            ))}
          </Select>
          <Select label="Classe" value={classeId} onChange={(e) => setClasseId(e.target.value)} disabled={!classes.length}>
            <option value="">— Choisir une classe —</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>{c.niveau} — {c.nom}</option>
            ))}
          </Select>
          <Select label="Période" value={trimestreId} onChange={(e) => setTrimestreId(e.target.value)} disabled={!classeId || !filteredTrimestres.length}>
            <option value="">— Choisir une période —</option>
            {filteredTrimestres.map((t) => (
              <option key={t.id} value={t.id}>{t.nom}</option>
            ))}
          </Select>
          {canWrite && !estJardin && (
            <Button
              variant="primary"
              disabled={!classeId || !trimestreId || isLoading || hasPublished || anneeCloturee}
              title={hasPublished ? 'Bulletins publiés — dépublier pour régénérer' : anneeCloturee ? 'Année archivée — lecture seule' : undefined}
              onClick={() => genererMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
            >
              {genererMut.isPending ? (
                <Loader2 size={14} strokeWidth={1.75} className="mr-1.5 animate-spin" />
              ) : null}
              {hasPublished ? 'Bulletins publiés' : 'Générer pour la classe'}
            </Button>
          )}
          {canWrite && !estJardin && classeId && trimestreId && (
            <>
              <Button
                variant="secondary"
                disabled={!hasBulletins || hasPublished || publierMut.isPending || anneeCloturee}
                title={hasPublished ? 'Déjà publiés' : !hasBulletins ? 'Aucun bulletin à publier' : anneeCloturee ? 'Année archivée — lecture seule' : undefined}
                onClick={() => publierMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
              >
                Publier
              </Button>
              <Button
                variant="ghost"
                disabled={!hasPublished || depublierMut.isPending || anneeCloturee}
                title={!hasPublished ? 'Aucun bulletin publié' : anneeCloturee ? 'Année archivée — lecture seule' : undefined}
                onClick={() => depublierMut.mutate({ id_classe: Number(classeId), id_trimestre: Number(trimestreId) })}
              >
                Dépublier
              </Button>
            </>
          )}
        </div>

        {anneeCloturee && (
          <div className="flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-soft)] bg-[var(--surface-2)] px-4 py-3 text-sm text-[var(--ink-dim)]">
            <Badge tone="neutral">Archivée</Badge>
            {selectedAnnee?.libelle} : consultation en lecture seule — la génération et la publication sont désactivées.
          </div>
        )}

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

        {estJardin && (
          <div className="py-16">
            <EmptyState
              title="Pas de bulletin pour le jardin d'enfants"
              message={`${classeNiveau} est évalué par appréciation : le bulletin chiffré ne s'applique pas à cette section.`}
            />
          </div>
        )}

        {!estJardin && classeId && trimestreId && (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <div className="relative max-w-sm flex-1">
                <Search strokeWidth={1.75} className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--ink-faint)]" />
                <Input
                  placeholder="Rechercher par matricule…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
              <span className="text-xs text-[var(--ink-dim)]">{filtered.length} élève(s)</span>
              <Button
                variant="secondary"
                className="ml-auto"
                disabled={!hasBulletins}
                isLoading={downloading === 'classe'}
                onClick={telechargerClasse}
              >
                <Download size={14} strokeWidth={1.75} className="mr-1.5" />
                Télécharger toute la classe (PDF)
              </Button>
            </div>

            {isLoading || loadingEleves ? (
              <TableSkeleton rows={8} />
            ) : isError ? (
              <div className="py-16">
                <EmptyState title="Erreur" message="Impossible de charger les bulletins." />
              </div>
            ) : filtered.length === 0 ? (
              <div className="py-16">
                <EmptyState message={search ? 'Aucun élève trouvé.' : "Aucun élève inscrit pour cette classe / cette année."} />
              </div>
            ) : (
              <Card className="overflow-hidden">
                <div className="border-b border-[var(--border-soft)] px-5 py-3">
                  <span className="text-sm font-semibold text-[var(--ink)]">
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
                      {filtered.map(({ eleve, bulletin }) => (
                        <TableRow key={eleve.matricule}>
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Avatar nom={eleve.nom} prenom={eleve.prenom} photo={eleve.photo} size="sm" />
                              <span className="font-medium text-[var(--ink)]">
                                {eleve.prenom} {eleve.nom}
                              </span>
                            </div>
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="text-sm font-medium" style={{ color: bulletin?.rang != null && bulletin.rang <= 3 ? 'var(--action-bright)' : 'var(--ink)' }}>
                              {bulletin?.rang != null ? `${bulletin.rang}${bulletin.rang === 1 ? 'er' : 'e'}` : '—'}
                            </span>
                          </TableCell>
                          <TableCell className="text-center">
                            <span className="text-sm font-medium" style={{ color: noteColor(bulletin?.moyenne_generale ?? null, bareme) }}>
                              {bulletin ? formatMoyenne(bulletin.moyenne_generale, bareme) : '—'}
                            </span>
                          </TableCell>
                          <TableCell className="text-xs text-[var(--ink-dim)]">
                            {bulletin?.appreciation ?? '—'}
                          </TableCell>
                          <TableCell>
                            {bulletin ? (
                              <Badge tone={bulletin.statut === 'PUBLIE' ? 'success' : 'neutral'}>
                                {bulletin.statut === 'PUBLIE' ? 'Publié' : 'Brouillon'}
                              </Badge>
                            ) : (
                              <Badge tone="info">Non généré</Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            {bulletin ? (
                              <div className="flex items-center justify-end gap-1">
                                <Tooltip content="Télécharger ce bulletin en PDF">
                                <button
                                  disabled={downloading === bulletin.id}
                                  onClick={() => telechargerUn(bulletin.id)}
                                  aria-label="Télécharger ce bulletin en PDF"
                                  className="rounded-[var(--radius-sm)] p-1.5 text-[var(--ink-faint)] transition-colors hover:bg-[var(--surface-3)] hover:text-[var(--ink)]"
                                >
                                  {downloading === bulletin.id ? (
                                    <Loader2 size={14} strokeWidth={1.75} className="animate-spin" />
                                  ) : (
                                    <Download size={14} strokeWidth={1.75} />
                                  )}
                                </button>
                                </Tooltip>
                                <Tooltip content="Aperçu">
                                <button
                                  disabled={apercuLoading === `b-${bulletin.id}`}
                                  onClick={() => void ouvrirPdf(
                                    `b-${bulletin.id}`,
                                    `Bulletin · ${eleve.prenom} ${eleve.nom} · ${trimestreLabel?.nom ?? ''}`,
                                    () => fetchBulletinPdf(bulletin.id),
                                    () => void telechargerUn(bulletin.id),
                                  )}
                                  aria-label="Aperçu"
                                  className="rounded-[var(--radius-sm)] p-1.5 text-[var(--ink-faint)] transition-colors hover:bg-[var(--surface-3)] hover:text-[var(--ink)]"
                                >
                                  {apercuLoading === `b-${bulletin.id}` ? (
                                    <Loader2 size={14} strokeWidth={1.75} className="animate-spin" />
                                  ) : (
                                    <FileText size={14} strokeWidth={1.75} />
                                  )}
                                </button>
                                </Tooltip>
                              </div>
                            ) : (
                              <span className="text-[var(--ink-faint)]">—</span>
                            )}
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

      {apercuPdf && (
        <PdfViewerModal
          data={apercuPdf.data}
          filename={apercuPdf.titre}
          impressionAuto={apercuPdf.imprim}
          onImpressionAutoFini={() => setApercuPdf((a) => a && { ...a, imprim: false })}
          onClose={() => setApercuPdf(null)}
          onDownload={apercuPdf.onDownload}
        />
      )}
    </div>
  )
}