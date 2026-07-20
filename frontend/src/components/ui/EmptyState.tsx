export function EmptyState({ message }: { message: string }) {
  return (
    <div className="rounded-[var(--radius-md)] border border-dashed border-[var(--color-border)] px-4 py-10 text-center">
      <p className="text-sm text-[var(--color-ink-faint)]">{message}</p>
    </div>
  )
}
