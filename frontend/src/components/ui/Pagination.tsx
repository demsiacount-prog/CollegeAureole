import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  page: number
  totalPages: number
  onChange: (page: number) => void
  isFetching?: boolean
}

export function Pagination({ page, totalPages, onChange, isFetching }: PaginationProps) {
  return (
    <div className="flex items-center justify-between gap-4">
      <p className="text-sm text-[var(--color-ink-dim)]">
        Page {page} sur {totalPages}
        {isFetching && <span className="ml-2 text-[var(--color-ink-faint)]">Actualisation…</span>}
      </p>
      <div className="flex items-center gap-2">
        <button
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          className="flex items-center gap-1 rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] px-3 py-1.5 text-sm text-[var(--color-ink-dim)] transition-colors hover:bg-[var(--color-surface-2)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft className="size-4" /> Précédent
        </button>
        <button
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          className="flex items-center gap-1 rounded-[var(--radius-sm)] border border-[var(--color-border-soft)] px-3 py-1.5 text-sm text-[var(--color-ink-dim)] transition-colors hover:bg-[var(--color-surface-2)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Suivant <ChevronRight className="size-4" />
        </button>
      </div>
    </div>
  )
}
