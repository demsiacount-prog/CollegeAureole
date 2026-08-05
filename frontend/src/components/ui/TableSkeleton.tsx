interface TableSkeletonProps {
  rows?: number
  columns?: number
}

export function TableSkeleton({ rows = 8, columns = 5 }: TableSkeletonProps) {
  return (
    <table className="w-full text-sm" aria-hidden>
      <thead>
        <tr className="border-b border-[var(--color-border)]">
          {Array.from({ length: columns }).map((_, i) => (
            <th key={i} className="px-5 py-3">
              <span className="skeleton inline-block h-3 w-24 rounded" />
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Array.from({ length: rows }).map((_, r) => (
          <tr key={r} className="border-b border-[var(--color-border-soft)] last:border-0">
            {Array.from({ length: columns }).map((_, c) => (
              <td key={c} className="px-5 py-3">
                <span
                  className="skeleton inline-block h-3.5 rounded"
                  style={{ width: `${[92, 64, 80, 56, 72][c % 5]}%`, maxWidth: '9rem' }}
                />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}