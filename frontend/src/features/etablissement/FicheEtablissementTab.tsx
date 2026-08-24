import { useEffect, useRef, useState, type ChangeEvent, type FormEvent } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Building2, Save, CalendarCheck, ImagePlus, Loader2, Trash2, CheckCircle2 } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { TableSkeleton } from '@/components/ui/TableSkeleton'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
import { urlAbsolue } from '@/lib/server'
import { fetchEtablissement, updateEtablissement, uploadLogo } from './api'
import { required, email, phone, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { EtablissementUpdate } from './types'

export default function FicheEtablissementTab() {
  const qc = useQueryClient()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['etablissement'],
    queryFn: fetchEtablissement,
    retry: false,
  })

  const [form, setForm] = useState<EtablissementUpdate | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Errors>({})

  useEffect(() => {
    if (data) {
      setForm({
        nom: data.nom,
        sigle: data.sigle ?? '',
        devise: data.devise ?? '',
        adresse: data.adresse ?? '',
        telephone: data.telephone ?? '',
        email: data.email ?? '',
        logo: data.logo ?? '',
      })
    }
  }, [data])

  const save = useMutation({
    mutationFn: (body: EtablissementUpdate) => updateEtablissement(body),
    onSuccess: (r) => {
      qc.setQueryData(['etablissement'], r)
      toast('Fiche établissement mise à jour.')
    },
    onError: (e) => toast(extractErrorMessage(e), 'error'),
  })

  async function handleLogoChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast('Veuillez choisir un fichier image (PNG, JPG, WebP ou GIF).', 'error')
      return
    }
    setUploading(true)
    try {
      const logo = await uploadLogo(file)
      setForm((f) => f && { ...f, logo })
      toast('Logo importé. Enregistrez pour confirmer.')
    } catch (err) {
      toast(extractErrorMessage(err, "Erreur lors de l'import du logo."), 'error')
    } finally {
      setUploading(false)
    }
  }

  if (isLoading) {
    return (
      <Card>
        <TableSkeleton rows={4} columns={2} />
      </Card>
    )
  }

  if (isError || !data || !form) {
    return (
      <div className="space-y-4">
        <div className="rounded-lg border border-[var(--color-danger)]/20 bg-[var(--color-danger-wash)] px-4 py-3 text-sm text-[var(--color-danger)]">
          La fiche de l’établissement n’existe pas encore. Elle est créée lors de la
          configuration initiale de l’application.
        </div>
      </div>
    )
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    const errs = validateFields({
      nom: required(form.nom, "Le nom de l'établissement"),
      email: form.email?.trim() ? email(form.email) : undefined,
      telephone: form.telephone?.trim() ? phone(form.telephone) : undefined,
    })
    setFieldErrors(errs)
    if (hasErrors(errs)) return
    save.mutate({
      nom: form.nom.trim(),
      sigle: form.sigle?.trim() || null,
      devise: form.devise?.trim() || null,
      adresse: form.adresse?.trim() || null,
      telephone: form.telephone?.trim() || null,
      email: form.email?.trim() || null,
      logo: form.logo?.trim() || null,
    })
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-2)] p-4">
        <div className="flex items-center gap-2 text-xs font-semibold text-[var(--color-ink)]">
          <Building2 size={14} strokeWidth={1.75} />
          Établissement
        </div>
        <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div>
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-ink-faint)]">Nom</div>
            <div className="mt-0.5 text-sm font-medium text-[var(--color-ink)]">{data.nom}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-ink-faint)]">Sigle</div>
            <div className="mt-0.5 text-sm font-medium text-[var(--color-ink)]">{data.sigle ?? '—'}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-ink-faint)]">Devise</div>
            <div className="mt-0.5 text-sm font-medium text-[var(--color-ink)]">{data.devise ?? '—'}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase tracking-wide text-[var(--color-ink-faint)]">Initialisé le</div>
            <div className="mt-0.5 flex items-center gap-1.5 text-sm font-medium text-[var(--color-ink)]">
              <CalendarCheck size={13} strokeWidth={1.75} className="text-[var(--color-ink-dim)]" />
              {data.date_initialisation
                ? new Date(data.date_initialisation).toLocaleDateString('fr-FR')
                : '—'}
            </div>
          </div>
         
        </div>
      </div>

      <form onSubmit={handleSubmit} className="rounded-lg border border-[var(--color-border)] p-4" noValidate>
        <div className="text-xs font-semibold text-[var(--color-ink)]">Modifier la fiche</div>
        <p className="mt-0.5 text-[11px] text-[var(--color-ink-dim)]">
          Ces informations identifient l’établissement dans l’ensemble du système.
        </p>

        <div className="mt-4 grid max-w-2xl grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            label="Nom de l'établissement"
            value={form.nom}
            onChange={(e) => {
              setForm((f) => f && { ...f, nom: e.target.value })
              if (fieldErrors.nom) setFieldErrors((p) => ({ ...p, nom: undefined }))
            }}
            required
            error={fieldErrors.nom}
          />
          <Input
            label="Sigle"
            value={form.sigle ?? ''}
            onChange={(e) => setForm((f) => f && { ...f, sigle: e.target.value })}
          />
          <Input
            label="Devise"
            value={form.devise ?? ''}
            onChange={(e) => setForm((f) => f && { ...f, devise: e.target.value })}
            hint="Affichée sous le nom de l’établissement."
          />
          <div className="sm:col-span-2">
            <Input
              label="Adresse"
              value={form.adresse ?? ''}
              onChange={(e) => setForm((f) => f && { ...f, adresse: e.target.value })}
            />
          </div>
          <Input
            label="Téléphone"
            type="tel"
            value={form.telephone ?? ''}
            onChange={(e) => {
              setForm((f) => f && { ...f, telephone: e.target.value })
              if (fieldErrors.telephone) setFieldErrors((p) => ({ ...p, telephone: undefined }))
            }}
            error={fieldErrors.telephone}
          />
          <Input
            label="E-mail de contact"
            type="email"
            value={form.email ?? ''}
            onChange={(e) => {
              setForm((f) => f && { ...f, email: e.target.value })
              if (fieldErrors.email) setFieldErrors((p) => ({ ...p, email: undefined }))
            }}
            error={fieldErrors.email}
          />
          <div className="sm:col-span-2">
            <div className="mb-1 text-xs font-medium text-[var(--color-ink-dim)]">Logo</div>
            <input
              ref={fileRef}
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              onChange={handleLogoChange}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
              className="flex w-full items-center gap-4 rounded-[var(--radius-sm)] border border-dashed border-[var(--color-border)] bg-[var(--color-surface-2)] p-4 text-left transition-colors hover:border-[var(--color-halo)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-halo)]"
            >
              {form.logo ? (
                <img
                  src={urlAbsolue(form.logo)}
                  alt="Logo de l’établissement"
                  className="h-14 w-14 shrink-0 rounded-lg bg-[var(--color-surface-3)] object-contain p-1 ring-1 ring-[var(--color-border)]"
                />
              ) : (
                <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg border border-dashed border-[var(--color-border)] bg-[var(--color-surface-3)] text-[var(--color-ink-faint)]">
                  {uploading
                    ? <Loader2 size={20} strokeWidth={1.75} className="animate-spin" />
                    : <ImagePlus size={20} strokeWidth={1.75} />}
                </span>
              )}
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium text-[var(--color-ink)]">
                  {uploading ? 'Envoi du logo…' : form.logo ? 'Modifier le logo' : 'Importer le logo de l’établissement'}
                </span>
                <span className="mt-0.5 block text-[11px] text-[var(--color-ink-faint)]">
                  PNG, JPG, WebP ou GIF — 2 Mo maximum. Affiché sur la page de connexion et dans l’application.
                </span>
              </span>
              {form.logo && !uploading && (
                <CheckCircle2 className="size-5 shrink-0 text-[var(--color-success)]" strokeWidth={1.75} />
              )}
            </button>
            {form.logo && (
              <div className="mt-2 flex justify-end">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setForm((f) => f && { ...f, logo: null })}
                >
                  <Trash2 size={14} strokeWidth={1.75} className="mr-1.5" />
                  Retirer le logo
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 flex justify-end">
          <Button type="submit" variant="primary" isLoading={save.isPending}>
            <Save size={14} strokeWidth={1.75} className="mr-1.5" />
            Enregistrer
          </Button>
        </div>
      </form>
    </div>
  )
}
