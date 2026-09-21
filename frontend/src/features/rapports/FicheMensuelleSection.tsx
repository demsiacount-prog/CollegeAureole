import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card } from '@/components/ui/Card'
import { Select } from '@/components/ui/Select'
import { Spinner } from '@/components/ui/Spinner'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { niveauOrdre } from '@/lib/niveaux'
import { fetchTrimestres } from '@/features/trimestres/api'
import { downloadFicheNotesCompositionsPdf, fetchFicheNotesCompositionsPdf } from './api'
import { usePdfApercu } from '@/components/pdf/usePdfApercu'
import { DocumentActionRow } from '@/components/print/DocumentActionRow'

/** Fiche de notes mensuelle (doc7) : relevé individuel par période.
 *  Classes évaluées par compositions (1ère→6ème) ; inapplicable au jardin. */
export function FicheMensuelleSection({
  matricule,
  anneeId,
  niveau,
}: {
  matricule: string
  anneeId: number | null | undefined
  niveau: string | null | undefined
}) {
  const [periodeId, setPeriodeId] = useState<number | ''>('')

  const ordre = niveauOrdre(niveau)
  const eligible = ordre != null && ordre >= 1 && ordre <= 6

  const { data: periodes = [], isLoading: periodesLoading } = useQuery({
    queryKey: ['trimestres', anneeId],
    queryFn: () => fetchTrimestres(anneeId ?? undefined),
    enabled: eligible && anneeId != null,
  })

  const filterPeriodes = useMemo(() => {
    if (!eligible) return []
    if (ordre === 6) return periodes
    if ((ordre ?? 0) <= 5) return periodes.filter((t) => t.type === 'COMPOSITION')
    return []
  }, [periodes, eligible, ordre])

  const nomPeriode = useMemo(
    () => filterPeriodes.find((t) => t.id === periodeId)?.nom ?? '',
    [filterPeriodes, periodeId],
  )

  const paramsPeriode = () => ({ trimestreId: periodeId === '' ? undefined : periodeId })

  const telecharger = async () => {
    try {
      await downloadFicheNotesCompositionsPdf(matricule, paramsPeriode())
    } catch (err) {
      toast(extractErrorMessage(err), 'error')
    }
  }

  const { chargement, element, ouvrirApercu, ouvrirImprimer } = usePdfApercu({
    titre: 'Fiche de notes mensuelle',
    chargeur: () => fetchFicheNotesCompositionsPdf(matricule, paramsPeriode()),
    onTelecharger: telecharger,
  })

  if (!eligible) return null

  return (
    <Card className="mb-4 w-full p-4">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-medium text-[var(--ink)]">Fiche de notes mensuelle</p>
        <Select
          label="Période"
          value={periodeId}
          onChange={(e) => setPeriodeId(e.target.value ? Number(e.target.value) : '')}
          options={[
            { value: '', label: 'Dernière période' },
            ...filterPeriodes.map((t) => ({ value: t.id, label: t.nom })),
          ]}
          className="w-56"
          disabled={periodesLoading}
        />
      </div>
      <div className="space-y-2">
        <DocumentActionRow
          label={`Relevé par matière · ${nomPeriode || 'Dernière période'}`}
          onApercu={ouvrirApercu}
          onImprimer={ouvrirImprimer}
          onTelecharger={telecharger}
        />
        {chargement && (
          <div className="flex justify-center py-3">
            <Spinner label="Génération du PDF…" />
          </div>
        )}
      </div>
      {element}
    </Card>
  )
}