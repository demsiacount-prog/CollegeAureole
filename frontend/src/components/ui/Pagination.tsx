import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  page: number
  totalPages: number
  onChange: (page: number) => void
  isFetching?: boolean
}

export function Pagination({ page, totalPages, onChange, isFetching }: PaginationProps) {
  return (
    <div className="flex items-center justify-between gap-4 border-t border-[var(--border-soft)] px-1 py-2.5 text-[12px] text-[var(--ink-faint)]">
      <p>
        Page {page} sur {totalPages}
        {isFetching && <span className="ml-2 text-[var(--ink-faint)]">Actualisation…</span>}
      </p>
      <div className="flex items-center gap-1.5">
        <button
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
          className="flex h-[28px] items-center gap-1 rounded-[var(--radius-md)] border border-[var(--border)] px-2.5 text-[12.5px] text-[var(--ink-dim)] transition-colors hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <ChevronLeft className="size-3.5" /> Précédent
        </button>
        <button
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
          className="flex h-[28px] items-center gap-1 rounded-[var(--radius-md)] border border-[var(--border)] px-2.5 text-[12.5px] text-[var(--ink-dim)] transition-colors hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Suivant <ChevronRight className="size-3.5" />
        </button>
      </div>
    </div>
  )
}
