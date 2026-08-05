import type { LucideIcon } from 'lucide-react'
import { Card } from '@/components/ui/Card'

export default function PlaceholderPage({ title, icon: Icon }: { title: string; icon: LucideIcon }) {
  return (
    <Card className="flex flex-col items-center justify-center gap-4 px-6 py-20 text-center">
      <span className="flex size-14 items-center justify-center rounded-full border border-[var(--color-border)] bg-[var(--color-surface-2)]">
        <Icon className="size-6 text-[var(--color-ink-dim)]" strokeWidth={1.75} />
      </span>
      <div>
        <h2 className="text-xl font-semibold text-[var(--color-ink)]">{title}</h2>
        <p className="mt-1.5 max-w-sm text-sm text-[var(--color-ink-dim)]">
          Ce module est la prochaine étape — les fondations (authentification, navigation,
          système de design) sont en place pour l’accueillir.
        </p>
      </div>
    </Card>
  )
}
