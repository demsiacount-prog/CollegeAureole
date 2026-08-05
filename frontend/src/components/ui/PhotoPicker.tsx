import { useRef, useState } from 'react'
import { Camera, X, Loader2 } from 'lucide-react'
import { Avatar } from './Avatar'
import { Button } from './Button'

const MAX_SIZE_BYTES = 2 * 1024 * 1024 // 2 Mo

interface PhotoPickerProps {
  nom: string
  prenom: string
  value: string | null
  onChange: (dataUrl: string | null) => void
}

/**
 * Convertit le fichier choisi en data URL et l'envoie tel quel — le backend
 * stocke `photo` comme une simple chaîne (`Optional[str]`), il n'y a pas
 * d'endpoint d'upload dédié. Suffisant pour des photos d'identité de format
 * raisonnable ; à revoir si des photos haute résolution posent problème.
 */
export function PhotoPicker({ nom, prenom, value, onChange }: PhotoPickerProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [isReading, setIsReading] = useState(false)

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return

    setError(null)

    if (!file.type.startsWith('image/')) {
      setError('Le fichier doit être une image.')
      return
    }
    if (file.size > MAX_SIZE_BYTES) {
      setError('Image trop lourde (2 Mo maximum).')
      return
    }

    setIsReading(true)
    const reader = new FileReader()
    reader.onload = () => {
      onChange(String(reader.result))
      setIsReading(false)
    }
    reader.onerror = () => {
      setError('Impossible de lire ce fichier.')
      setIsReading(false)
    }
    reader.readAsDataURL(file)
  }

  return (
    <div className="flex items-center gap-4">
      <div className="relative">
        <Avatar nom={nom} prenom={prenom} photo={value} size="lg" />
        {isReading && (
          <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50">
            <Loader2 className="size-4 animate-spin text-white" />
          </div>
        )}
      </div>

      <div className="flex flex-col gap-1.5">
        <div className="flex items-center gap-2">
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => inputRef.current?.click()}
          >
            <Camera className="size-3.5" strokeWidth={1.75} />
            {value ? 'Changer la photo' : 'Ajouter une photo'}
          </Button>
          {value && (
            <Button
              type="button"
              variant="ghost"
              tone="danger"
              size="sm"
              onClick={() => onChange(null)}
            >
              <X className="size-3.5" strokeWidth={1.75} />
              Retirer
            </Button>
          )}
        </div>
        <p className="text-[11px] text-[var(--color-ink-faint)]">JPG ou PNG, 2 Mo maximum.</p>
        {error && <p className="text-[11px] text-[var(--color-danger)]">{error}</p>}
      </div>

      <input ref={inputRef} type="file" accept="image/*" onChange={handleFile} className="hidden" />
    </div>
  )
}
