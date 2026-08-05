export function EmptyState({ title, message }: { title?: string; message: string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-dashed border-[var(--color-border)] px-4 py-10 text-center">
      {title && <p className="mb-1 font-medium text-[var(--color-ink)]">{title}</p>}
      <p className="text-sm text-[var(--color-ink-faint)]">{message}</p>
    </div>
  )
}
