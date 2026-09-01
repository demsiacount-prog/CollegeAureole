import { Loader2 } from 'lucide-react'

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center gap-3 text-[var(--color-ink-dim)]">
      <Loader2 className="size-6 animate-spin text-[var(--color-action)]" />
      {label && <p className="text-sm">{label}</p>}
    </div>
  )
}
