import { useState } from 'react'
import { Drawer } from '@/components/ui/Drawer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import type { AnneeScolaireCreateInput } from './types'

interface Props {
  open: boolean
  onClose: () => void
  onSubmit: (data: AnneeScolaireCreateInput) => void
}

export default function AnneeScolaireFormDrawer({ open, onClose, onSubmit }: Props) {
  const [libelle, setLibelle] = useState('')
  const [dateDebut, setDateDebut] = useState('')
  const [dateFin, setDateFin] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      libelle,
      date_debut: dateDebut,
      date_fin: dateFin,
    })
    setLibelle('')
    setDateDebut('')
    setDateFin('')
  }

  return (
    <Drawer open={open} onClose={onClose} title="Nouvelle année scolaire">
      <form onSubmit={handleSubmit} className="flex flex-col h-full">
        <div className="flex-1 overflow-y-auto space-y-4">
          <Input label="Libellé" value={libelle} onChange={(e) => setLibelle(e.target.value)} placeholder="ex. 2025-2026" required />
          <Input label="Date de début" type="date" value={dateDebut} onChange={(e) => setDateDebut(e.target.value)} required />
          <Input label="Date de fin" type="date" value={dateFin} onChange={(e) => setDateFin(e.target.value)} required />
        </div>

        <div className="p-4 border-t border-[var(--color-border)]">
          <Button type="submit" variant="primary" className="w-full">
            Créer
          </Button>
        </div>
      </form>
    </Drawer>
  )
}
