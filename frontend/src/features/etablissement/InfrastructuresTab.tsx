import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Save, Warehouse } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { Badge } from '@/components/ui/Badge'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { fetchAnneesScolaires } from '@/features/annees_scolaires/api'
import { fetchInfrastructures, saveInfrastructures } from './api'
import type { EtablissementInfrastructures } from './types'

const CHAMPS: { groupe: string; champs: { field: keyof EtablissementInfrastructures; label: string }[] }[] = [
  {
    groupe: 'Salles construites',
    champs: [
      { field: 'salles_dur', label: 'En dur' },
      { field: 'salles_semi_dur', label: 'Semi-dur' },
      { field: 'salles_banco', label: 'En banco' },
      { field: 'salles_autres', label: 'Autres' },
    ],
  },
  {
    groupe: 'Directions',
    champs: [
      { field: 'direction_dur', label: 'En dur' },
      { field: 'direction_banco', label: 'En banco' },
      { field: 'direction_autres', label: 'Autres' },
      { field: 'logement_direction', label: 'Logement direction' },
    ],
  },
  {
    groupe: 'Mobiliers',
    champs: [
      { field: 'tables_bancs', label: 'Tables-bancs' },
      { field: 'chaises', label: 'Chaises' },
      { field: 'armoires', label: 'Armoires' },
      { field: 'tableaux', label: 'Tableaux' },
      { field: 'mobilier_divers', label: 'Divers' },
    ],
  },
]

const VALEURS_PAR_DEFAUT: Record<keyof EtablissementInfrastructures, number | null> = {
  id: null,
  id_annee_scolaire: null,
  salles_dur: null,
  salles_semi_dur: null,
  salles_banco: null,
  salles_autres: null,
  direction_dur: null,
  direction_banco: null,
  direction_autres: null,
  logement_direction: null,
  tables_bancs: null,
  chaises: null,
  armoires: null,
  tableaux: null,
  mobilier_divers: null,
}

export default function InfrastructuresTab() {
  const qc = useQueryClient()
  const { data: annees = [], isLoading: annualLoading } = useQuery({
    queryKey: ['annees-scolaires'],
    queryFn: fetchAnneesScolaires,
  })
  const anneeActive = annees.find((a) => a.active) ?? annees[0] ?? null

  const { data: infra, isLoading: infraLoading, isError: infraError } = useQuery({
    queryKey: ['etablissement-infrastructures', anneeActive?.id],
    queryFn: () => fetchInfrastructures(anneeActive!.id),
    enabled: !!anneeActive,
    retry: false,
  })

  const [form, setForm] = useState<Record<keyof EtablissementInfrastructures, number | null>>(VALEURS_PAR_DEFAUT)

  useEffect(() => {
    if (!anneeActive) return
    if (infra) {
      const valeurs: Record<keyof EtablissementInfrastructures, number | null> = { ...VALEURS_PAR_DEFAUT }
      for (const groupe of CHAMPS) {
        for (const { field } of groupe.champs) {
          valeurs[field] = (infra[field] as number | null | undefined) ?? null
        }
      }
      valeurs.id = infra.id ?? null
      valeurs.id_annee_scolaire = infra.id_annee_scolaire ?? anneeActive.id
      setForm(valeurs)
    } else {
      setForm({ ...VALEURS_PAR_DEFAUT, id_annee_scolaire: anneeActive.id })
    }
  }, [infra, anneeActive])

  const save = useMutation({
    mutationFn: () => {
      const corps: Record<string, number | null> = {}
      for (const groupe of CHAMPS) {
        for (const { field } of groupe.champs) {
          corps[field] = form[field]
        }
      }
      return saveInfrastructures({ ...corps, id_annee_scolaire: form.id_annee_scolaire ?? anneeActive?.id })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['etablissement-infrastructures'] })
      toast('Infrastructures enregistrées.')
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  if (annualLoading || infraLoading) {
    return (
      <Card>
        <TableSkeleton rows={4} columns={2} />
      </Card>
    )
  }

  if (!anneeActive) {
    return (
      <div className="rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface-2)] px-4 py-3 text-sm text-[var(--ink-dim)]">
        Aucune année scolaire active : créez et activez une année scolaire avant de renseigner les infrastructures.
      </div>
    )
  }

  const setChamp = (field: keyof EtablissementInfrastructures) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value === '' ? null : Math.max(0, Number(e.target.value)) }))

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface-2)] p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-[var(--ink)]">
            <Warehouse size={14} strokeWidth={1.75} />
            Infrastructures et mobiliers
          </div>
          
        </div>
        <Badge tone="success">Année : {anneeActive.libelle}</Badge>
      </div>

      {infraError && (
        <div className="rounded-[var(--radius-sm)] border border-[var(--info)]/20 bg-[var(--info-w)] px-4 py-3 text-sm text-[var(--ink-dim)]">
          Aucune donnée enregistrée pour cette année : les champs ci-dessous sont vierges.
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {CHAMPS.map(({ groupe, champs }) => (
          <div key={groupe} className="rounded-[var(--radius-sm)] border border-[var(--border)] p-3">
            <p className="mb-2 font-medium">{groupe}</p>
            <div className="grid grid-cols-1 gap-3">
              {champs.map(({ field, label }) => (
                <Input
                  key={field}
                  label={label}
                  type="number"
                  min={0}
                  value={form[field] ?? ''}
                  onChange={setChamp(field)}
                />
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end">
        <Button type="button" variant="primary" isLoading={save.isPending} onClick={() => save.mutate()}>
          <Save size={14} strokeWidth={1.75} className="mr-1.5" />
          Enregistrer
        </Button>
      </div>
    </div>
  )
}