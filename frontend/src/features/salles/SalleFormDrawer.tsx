import { useState } from 'react'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import type { Salle, SalleCreateInput } from './types'

interface Props {
  salle?: Salle | null
  open: boolean
  onClose: () => void
  onSubmit: (data: SalleCreateInput) => void
}

export default function SalleFormDrawer({ salle, open, onClose, onSubmit }: Props) {
  const isEdit = !!salle

  const [nom, setNom] = useState(salle?.nom ?? '')
  const [capacite, setCapacite] = useState(salle?.capacite != null ? String(salle.capacite) : '')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      nom,
      capacite: capacite ? Number(capacite) : null,
    })
  }

  return (
    <Drawer open={open} onClose={onClose} title={isEdit ? 'Modifier la salle' : 'Nouvelle salle'}>
      <form onSubmit={handleSubmit} className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <Input label="Nom" placeholder="ex. Salle 12" value={nom} onChange={(e) => setNom(e.target.value)} required />
          <Input label="Capacité" type="number" placeholder="ex. 45" value={capacite} onChange={(e) => setCapacite(e.target.value)} />
        </div>

        <div className="p-4 border-t border-[var(--color-border)]">
          <Button type="submit" variant="primary" className="w-full">
            {isEdit ? 'Mettre à jour' : 'Créer'}
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
