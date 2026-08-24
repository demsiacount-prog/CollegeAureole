import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Drawer } from '@/components/ui/Drawer'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { extractErrorMessage } from '@/lib/api'
import { toast } from '@/components/ui/toast'
import { createUtilisateur, updateUtilisateur } from './api'
import { required, email as validEmail, minLength, validateFields, hasErrors, type Errors } from '@/lib/validation'
import type { Role } from '@/types'
import { ROLES, type Utilisateur } from './types'

interface Props {
  open: boolean
  onClose: () => void
  utilisateur?: Utilisateur | null
}

export default function UtilisateurFormDrawer({ open, onClose, utilisateur }: Props) {
  const qc = useQueryClient()
  const isEdit = !!utilisateur

  const [nom, setNom] = useState('')
  const [prenom, setPrenom] = useState('')
  const [email, setEmail] = useState('')
  const [motDePasse, setMotDePasse] = useState('')
  const [role, setRole] = useState<Role>('comptable')
  const [actif, setActif] = useState(true)
  const [error, setError] = useState('')
  const [errors, setErrors] = useState<Errors>({})

  useEffect(() => {
    if (open) {
      setNom(utilisateur?.nom ?? '')
      setPrenom(utilisateur?.prenom ?? '')
      setEmail(utilisateur?.email ?? '')
      setMotDePasse('')
      setRole(utilisateur?.role ?? 'comptable')
      setActif(utilisateur?.actif ?? true)
      setError('')
      setErrors({})
    }
  }, [open, utilisateur])

  const handleSubmit = () => {
    const errs = validateFields({
      prenom: required(prenom, 'Le prénom'),
      nom: required(nom, 'Le nom'),
      email: required(email, "L'e-mail") ?? validEmail(email),
      mot_de_passe: isEdit ? undefined : required(motDePasse, 'Le mot de passe') ?? minLength(motDePasse, 8, 'Le mot de passe'),
    })
    setErrors(errs)
    if (hasErrors(errs)) return
    mutation.mutate()
  }

  const mutation = useMutation({
    mutationFn: () => {
      if (isEdit) {
        return updateUtilisateur(utilisateur!.id, { nom, prenom, email, role, actif })
      }
      return createUtilisateur({ nom, prenom, email, mot_de_passe: motDePasse, role })
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['utilisateurs'] })
      toast(isEdit ? 'Compte modifié.' : 'Compte créé.')
      onClose()
    },
    onError: (err) => setError(extractErrorMessage(err)),
  })

  return (
    <Drawer open={open} onClose={onClose} title={isEdit ? 'Modifier le compte' : 'Nouveau compte'}>
      <form onSubmit={(e) => { e.preventDefault(); handleSubmit() }} noValidate className="flex flex-col h-full">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Prénom"
              placeholder="ex. Aminata"
              value={prenom}
              onChange={(e) => {
                setPrenom(e.target.value)
                if (errors.prenom) setErrors((prev) => ({ ...prev, prenom: undefined }))
              }}
              required
              error={errors.prenom}
            />
            <Input
              label="Nom"
              placeholder="ex. Diallo"
              value={nom}
              onChange={(e) => {
                setNom(e.target.value)
                if (errors.nom) setErrors((prev) => ({ ...prev, nom: undefined }))
              }}
              required
              error={errors.nom}
            />
          </div>
          <Input
            label="E-mail"
            type="email"
            placeholder="ex. aminata.diallo@ecole.ml"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              if (errors.email) setErrors((prev) => ({ ...prev, email: undefined }))
            }}
            required
            error={errors.email}
          />
          {!isEdit && (
            <Input
              label="Mot de passe"
              type="password"
              placeholder="8 caractères minimum"
              value={motDePasse}
              onChange={(e) => {
                setMotDePasse(e.target.value)
                if (errors.mot_de_passe) setErrors((prev) => ({ ...prev, mot_de_passe: undefined }))
              }}
              required
              minLength={8}
              error={errors.mot_de_passe}
            />
          )}
          <Select label="Rôle" value={role} onChange={(e) => setRole(e.target.value as Role)}>
            {ROLES.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
          </Select>
          {isEdit && (
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-[var(--color-ink)]">Statut</label>
              <button
                type="button"
                onClick={() => setActif(!actif)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${actif ? 'bg-[var(--color-success)]' : 'bg-[var(--color-border)]'}`}
              >
                <span className={`inline-block size-4 rounded-full bg-[var(--color-surface)] transition-transform ${actif ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
              <span className="text-sm text-[var(--color-ink-dim)]">{actif ? 'Actif' : 'Inactif'}</span>
            </div>
          )}
          {error && (
            <p className="rounded-[var(--radius-sm)] border border-[var(--color-danger)]/20 bg-[var(--color-danger)]/10 px-3 py-2 text-sm text-[var(--color-danger)]">
              {error}
            </p>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>Annuler</Button>
          <Button type="submit" variant="primary" isLoading={mutation.isPending}>{isEdit ? 'Enregistrer' : 'Créer'}</Button>
        </div>
      </form>
    </Drawer>
  )
}
