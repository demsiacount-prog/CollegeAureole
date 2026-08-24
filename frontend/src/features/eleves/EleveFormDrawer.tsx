import { useEffect, useState, type FormEvent } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle, FileText, Users, UserPlus, Upload } from 'lucide-react'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { SearchableSelect } from '@/components/ui/SearchableSelect'
import { Button } from '@/components/ui/Button'
import { PhotoPicker } from '@/components/ui/PhotoPicker'
import { uploadDocument } from '@/features/documents/api'
import { fetchTuteurs, createTuteur } from '@/features/tuteurs/api'
import { fetchClasses } from '@/features/classes/api'
import { extractErrorMessage } from '@/lib/api'
import { required, email, phone, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { Eleve, EleveCreateInput, EleveUpdateInput } from './types'

interface EleveFormDrawerProps {
  open: boolean
  onClose: () => void
  eleve: Eleve | null // null = création
  onCreate: (payload: EleveCreateInput) => Promise<unknown>
  onUpdate: (matricule: string, payload: EleveUpdateInput) => Promise<unknown>
  canImport?: boolean
}

const emptyForm = {
  nom: '',
  prenom: '',
  photo: null as string | null,
  date_de_naissance: '',
  lieu_de_naissance: '',
  sexe: 'M',
  adresse: '',
  statut: 'actif',
  acte_naissance: false,
  carnet_sante: false,
  tuteur_id: '',
  classe_id: '',
  tuteur_mode: 'create' as 'create' | 'select',
  tuteur_prenom: '',
  tuteur_nom: '',
  tuteur_telephone: '',
  tuteur_email: '',
  tuteur_profession: '',
  tuteur_adresse: '',
}

const DOCS_LABELS: Record<string, string> = {
  acte_naissance: 'Acte de naissance',
  carnet_sante: 'Carnet de santé',
}

const DOCS_FIELDS = ['acte_naissance', 'carnet_sante'] as const

export function EleveFormDrawer({ open, onClose, eleve, onCreate, onUpdate, canImport = true }: EleveFormDrawerProps) {
  const isEdit = !!eleve
  const [form, setForm] = useState(emptyForm)
  const [error, setError] = useState<string | null>(null)
  const [errors, setErrors] = useState<Errors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [docFiles, setDocFiles] = useState<Record<string, File | null>>({})
  const [uploadProgress, setUploadProgress] = useState<string | null>(null)

  const { data: tuteurs = [] } = useQuery({ queryKey: ['tuteurs'], queryFn: () => fetchTuteurs(), enabled: open })
  const { data: classes = [] } = useQuery({ queryKey: ['classes'], queryFn: fetchClasses, enabled: open })

  useEffect(() => {
    if (!open) return
    if (eleve) {
      setForm({
        ...emptyForm,
        nom: eleve.nom,
        prenom: eleve.prenom,
        photo: eleve.photo ?? null,
        date_de_naissance: eleve.date_de_naissance,
        lieu_de_naissance: eleve.lieu_de_naissance,
        sexe: eleve.sexe,
        adresse: eleve.adresse ?? '',
        statut: eleve.statut,
        acte_naissance: eleve.acte_naissance,
        carnet_sante: eleve.carnet_sante,
        tuteur_id: String(eleve.tuteur.id),
        classe_id: eleve.classe ? String(eleve.classe.id) : '',
        tuteur_mode: 'select',
      })
    } else {
      setForm(emptyForm)
    }
    setError(null)
    setErrors({})
    setDocFiles({})
    setUploadProgress(null)
  }, [open, eleve])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const rules: Record<string, string | undefined> = {
      prenom: required(form.prenom, 'Le prénom'),
      nom: required(form.nom, 'Le nom'),
      lieu_de_naissance: required(form.lieu_de_naissance, 'Le lieu de naissance'),
    }
    if (!isEdit) {
      rules.date_de_naissance = required(form.date_de_naissance, 'La date de naissance')
    }
    if (form.tuteur_mode === 'create') {
      rules.tuteur_prenom = required(form.tuteur_prenom, 'Le prénom du tuteur')
      rules.tuteur_nom = required(form.tuteur_nom, 'Le nom du tuteur')
      rules.tuteur_telephone = required(form.tuteur_telephone, 'Le téléphone du tuteur') ?? phone(form.tuteur_telephone)
      rules.tuteur_email = required(form.tuteur_email, "L'e-mail du tuteur") ?? email(form.tuteur_email)
    } else {
      rules.tuteur_id = required(form.tuteur_id, 'Le tuteur')
    }
    const errs = validateFields(rules)
    setErrors(errs)
    if (hasErrors(errs)) return
    setIsSubmitting(true)
    try {
      let matricule: string | undefined
      if (isEdit && eleve) {
        await onUpdate(eleve.matricule, {
          nom: form.nom,
          prenom: form.prenom,
          photo: form.photo,
          lieu_de_naissance: form.lieu_de_naissance,
          adresse: form.adresse || null,
          statut: form.statut,
          acte_naissance: form.acte_naissance,
          carnet_sante: form.carnet_sante,
          classe_id: form.classe_id ? Number(form.classe_id) : null,
        })
        matricule = eleve.matricule
      } else {
        let tuteurId: number
        if (form.tuteur_mode === 'create') {
          const created = await createTuteur({
            prenom: form.tuteur_prenom.trim(),
            nom: form.tuteur_nom.trim(),
            telephone: form.tuteur_telephone.trim(),
            email: form.tuteur_email.trim(),
            adresse: form.tuteur_adresse.trim() || 'Non renseignée',
            profession: form.tuteur_profession.trim() || 'Non renseignée',
          })
          tuteurId = created.id
        } else {
          tuteurId = Number(form.tuteur_id)
        }
        const createdEleve = await onCreate({
          nom: form.nom,
          prenom: form.prenom,
          photo: form.photo,
          date_de_naissance: form.date_de_naissance,
          lieu_de_naissance: form.lieu_de_naissance,
          sexe: form.sexe,
          adresse: form.adresse || null,
          statut: form.statut,
          acte_naissance: form.acte_naissance,
          carnet_sante: form.carnet_sante,
          tuteur_id: tuteurId,
          classe_id: form.classe_id ? Number(form.classe_id) : null,
        })
        matricule = (createdEleve as Eleve)?.matricule
      }

      if (matricule) {
        for (const field of DOCS_FIELDS) {
          const file = docFiles[field]
          if (!file) continue
          setUploadProgress(`Import de ${DOCS_LABELS[field]}…`)
          await uploadDocument(matricule, field, file)
        }
        setUploadProgress(null)
      }
      onClose()
    } catch (err) {
      setError(extractErrorMessage(err, "L'enregistrement a échoué."))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={isEdit ? `Modifier ${eleve?.prenom} ${eleve?.nom}` : 'Nouvel élève'}
      description={isEdit ? `Matricule ${eleve?.matricule}` : 'Créer un dossier élève et l’associer à un tuteur.'}
    >
      <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
        <PhotoPicker nom={form.nom} prenom={form.prenom} value={form.photo} onChange={(photo) => setForm({ ...form, photo })} />

        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Prénom"
            placeholder="ex. Aminata"
            value={form.prenom}
            onChange={(e) => {
              setForm({ ...form, prenom: e.target.value })
              if (errors.prenom) setErrors((prev) => ({ ...prev, prenom: undefined }))
            }}
            required
            error={errors.prenom}
          />
          <Input
            label="Nom"
            placeholder="ex. Diallo"
            value={form.nom}
            onChange={(e) => {
              setForm({ ...form, nom: e.target.value })
              if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
            }}
            required
            error={errors.nom}
          />
        </div>

        {!isEdit && (
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Date de naissance"
              type="date"
              max={new Date().toISOString().split('T')[0]}
              value={form.date_de_naissance}
              onChange={(e) => {
                setForm({ ...form, date_de_naissance: e.target.value })
                if (errors.date_de_naissance) setErrors((prev) => ({ ...prev, date_de_naissance: undefined }))
              }}
              required
              error={errors.date_de_naissance}
            />
            <Select label="Sexe" value={form.sexe} onChange={(e) => setForm({ ...form, sexe: e.target.value })}>
              <option value="M">Masculin</option>
              <option value="F">Féminin</option>
            </Select>
          </div>
        )}

        <Input
          label="Lieu de naissance"
          placeholder="ex. Bamako"
          value={form.lieu_de_naissance}
          onChange={(e) => {
            setForm({ ...form, lieu_de_naissance: e.target.value })
            if (errors.lieu_de_naissance) setErrors((prev) => ({ ...prev, lieu_de_naissance: undefined }))
          }}
          required
          error={errors.lieu_de_naissance}
        />
        <Input label="Adresse" placeholder="ex. Badalabougou, Bamako" value={form.adresse} onChange={(e) => setForm({ ...form, adresse: e.target.value })} />

        <div className="grid grid-cols-2 gap-3">
          <Select label="Classe" value={form.classe_id} onChange={(e) => setForm({ ...form, classe_id: e.target.value })}>
            <option value="">Non affecté</option>
            {classes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.niveau} —{c.nom}
              </option>
            ))}
          </Select>
          <Select label="Statut" value={form.statut} onChange={(e) => setForm({ ...form, statut: e.target.value })}>
            <option value="actif">Actif</option>
            <option value="inactif">Inactif</option>
          </Select>
        </div>

        <div className="border-t border-[var(--color-border-soft)] pt-4">
          <p className="mb-2 text-xs font-semibold text-[var(--color-ink)]">Documents fournis</p>
          <div className="space-y-2">
            {DOCS_FIELDS.map((field) => (
              <div
                key={field}
                className="rounded-[var(--radius-sm)] border p-3 transition-all"
                style={{
                  borderColor: form[field] ? 'var(--color-success)' : 'var(--color-border)',
                  background: form[field] ? 'var(--color-success-wash)' : 'var(--color-surface)',
                }}
              >
                <div className="flex items-center justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => setForm((f) => ({ ...f, [field]: !f[field] }))}
                    className="flex items-center gap-2 text-xs transition-all"
                  >
                    {form[field] ? (
                      <CheckCircle size={14} className="text-[var(--color-success)] shrink-0" />
                    ) : (
                      <FileText size={14} className="text-[var(--color-ink-faint)] shrink-0" />
                    )}
                    <span className="font-medium" style={{ color: form[field] ? 'var(--color-success)' : 'var(--color-ink-dim)' }}>
                      {DOCS_LABELS[field]}
                    </span>
                  </button>
                  {canImport && (
                    <label className="flex cursor-pointer items-center gap-1.5 rounded-[var(--radius-sm)] border border-[var(--color-border)] px-2.5 py-1.5 text-xs text-[var(--color-ink-dim)] transition-colors hover:bg-[var(--color-surface-2)]">
                      <Upload size={13} strokeWidth={1.75} />
                      <span className="max-w-[140px] truncate">
                        {docFiles[field] ? docFiles[field]!.name : 'Importer…'}
                      </span>
                      <input
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        className="hidden"
                        onChange={(e) => {
                          const f = e.target.files?.[0] ?? null
                          setDocFiles((prev) => ({ ...prev, [field]: f }))
                          if (f) setForm((prev) => ({ ...prev, [field]: true }))
                        }}
                      />
                    </label>
                  )}
                </div>
                {docFiles[field] && (
                  <div className="mt-2 flex items-center justify-between gap-2">
                    <span className="truncate text-[11px] text-[var(--color-ink-faint)]">
                      Fichier importé : {docFiles[field]!.name}
                    </span>
                    <button
                      type="button"
                      onClick={() => setDocFiles((prev) => ({ ...prev, [field]: null }))}
                      className="shrink-0 text-[11px] text-[var(--color-danger)] hover:underline"
                    >
                      Retirer
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
          {uploadProgress && (
            <p className="mt-2 flex items-center gap-2 text-xs text-[var(--color-info)]">
              <Upload size={13} strokeWidth={1.75} className="animate-pulse" />
              {uploadProgress}
            </p>
          )}
        </div>

        {!isEdit && (
          <div className="rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-2)] p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-sm font-medium text-[var(--color-ink)]">Tuteur</p>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setForm((f) => ({
                  ...f,
                  tuteur_mode: f.tuteur_mode === 'create' ? 'select' : 'create',
                  tuteur_id: '',
                  tuteur_prenom: '',
                  tuteur_nom: '',
                  tuteur_telephone: '',
                }))}
              >
                {form.tuteur_mode === 'create' ? (
                  <><Users strokeWidth={1.75} className="size-4" /> Tuteur existant</>
                ) : (
                  <><UserPlus strokeWidth={1.75} className="size-4" /> Nouveau tuteur</>
                )}
              </Button>
            </div>

            {form.tuteur_mode === 'create' ? (
              <div className="flex flex-col gap-3">
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Prénom du tuteur"
                    placeholder="ex. Amadou"
                    value={form.tuteur_prenom}
                    onChange={(e) => {
                      setForm({ ...form, tuteur_prenom: e.target.value })
                      if (errors.tuteur_prenom) setErrors((prev) => ({ ...prev, tuteur_prenom: undefined }))
                    }}
                    required
                    error={errors.tuteur_prenom}
                  />
                  <Input
                    label="Nom du tuteur"
                    placeholder="ex. Touré"
                    value={form.tuteur_nom}
                    onChange={(e) => {
                      setForm({ ...form, tuteur_nom: e.target.value })
                      if (errors.tuteur_nom) setErrors((prev) => ({ ...prev, tuteur_nom: undefined }))
                    }}
                    required
                    error={errors.tuteur_nom}
                  />
                </div>
                <Input
                  label="Téléphone du tuteur"
                  placeholder="+223 XX XX XX XX"
                  value={form.tuteur_telephone}
                  onChange={(e) => {
                    setForm({ ...form, tuteur_telephone: e.target.value })
                    if (errors.tuteur_telephone) setErrors((prev) => ({ ...prev, tuteur_telephone: undefined }))
                  }}
                  required
                  error={errors.tuteur_telephone}
                />
                <Input
                  label="E-mail du tuteur"
                  type="email"
                  placeholder="ex. amadou@email.com"
                  value={form.tuteur_email}
                  onChange={(e) => {
                    setForm({ ...form, tuteur_email: e.target.value })
                    if (errors.tuteur_email) setErrors((prev) => ({ ...prev, tuteur_email: undefined }))
                  }}
                  required
                  error={errors.tuteur_email}
                />
                <div className="grid grid-cols-2 gap-3">
                  <Input
                    label="Profession"
                    placeholder="ex. Commerçant"
                    value={form.tuteur_profession}
                    onChange={(e) => setForm({ ...form, tuteur_profession: e.target.value })}
                  />
                  <Input
                    label="Adresse"
                    placeholder="ex. Badalabougou, Bamako"
                    value={form.tuteur_adresse}
                    onChange={(e) => setForm({ ...form, tuteur_adresse: e.target.value })}
                  />
                </div>
              </div>
            ) : (
              <SearchableSelect
                label="Sélectionner un tuteur"
                value={form.tuteur_id}
                onChange={(v) => {
                  setForm({ ...form, tuteur_id: v })
                  if (errors.tuteur_id) setErrors((prev) => ({ ...prev, tuteur_id: undefined }))
                }}
                options={tuteurs.map((t) => ({
                  value: String(t.id),
                  label: `${t.prenom} ${t.nom}`.trim(),
                  
                }))}
                placeholder="Rechercher un tuteur…"
                emptyMessage="Aucun tuteur trouvé"
                error={errors.tuteur_id}
              />
            )}
          </div>
        )}

        {error && (
          <p role="alert" className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/30 bg-[var(--color-danger-wash)] px-3 py-2 text-sm text-[var(--color-danger)]">
            {error}
          </p>
        )}

        <div className="mt-2 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button type="submit" variant="primary" isLoading={isSubmitting}>
            {isEdit ? 'Enregistrer' : 'Créer l’élève'}
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
