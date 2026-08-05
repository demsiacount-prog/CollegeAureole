import { type ReactNode, useState } from 'react'
import { clsx } from 'clsx'

interface TabDef {
  key: string
  label: string
  count?: number
  content: ReactNode
}

export function Tabs({ tabs, defaultKey }: { tabs: TabDef[]; defaultKey?: string }) {
  const [active, setActive] = useState(defaultKey ?? tabs[0]?.key)
  const current = tabs.find((t) => t.key === active) ?? tabs[0]

  return (
    <div>
      <div className="flex gap-1 border-b border-[var(--color-border-soft)]">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={clsx(
              'relative px-3.5 py-2.5 text-sm font-medium transition-colors',
              tab.key === active
                ? 'text-[var(--color-brand)]'
                : 'text-[var(--color-ink-dim)] hover:text-[var(--color-ink)]',
            )}
          >
            {tab.label}
            {tab.count !== undefined && (
              <span
                className={clsx(
                  'ml-1.5 rounded-full px-1.5 py-0.5 text-[11px] tabular-nums',
                  tab.key === active
                    ? 'bg-[var(--color-brand-wash)] text-[var(--color-brand)]'
                    : 'bg-[var(--color-surface-3)] text-[var(--color-ink-faint)]',
                )}
              >
                {tab.count}
              </span>
            )}
            {tab.key === active && (
              <span className="absolute inset-x-0 -bottom-px h-0.5 rounded-full bg-[var(--color-brand)]" />
            )}
          </button>
        ))}
      </div>
      <div className="pt-5">{current?.content}</div>
    </div>
  )
}
