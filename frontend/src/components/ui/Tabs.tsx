import { type ReactNode, useState } from 'react'
import { clsx } from 'clsx'
import type { LucideIcon } from 'lucide-react'

interface TabDef {
  key: string
  label: string
  count?: number
  /** Icône affichée à gauche du libellé (Type C v2 — .dossier-tab svg 13px). */
  icon?: LucideIcon
  content?: ReactNode
}

type TabsProps =
  | { tabs: TabDef[]; defaultKey?: string; value?: undefined; onChange?: undefined }
  | { tabs: TabDef[]; defaultKey?: string; value: string; onChange: (key: string) => void }

/** Design system Type C v2 — Tab navigation (38px, soulignement halo 2px). */
export function Tabs({ tabs, defaultKey, value, onChange }: TabsProps) {
  const controlled = value !== undefined
  const [internal, setInternal] = useState(defaultKey ?? tabs[0]?.key)
  const active = controlled ? value : internal
  const current = tabs.find((t) => t.key === active) ?? tabs[0]

  const select = (key: string) => {
    if (controlled) onChange(key)
    else setInternal(key)
  }

  // §42 — ← / → naviguent entre les onglets d'un dossier.
  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return
    e.preventDefault()
    const idx = tabs.findIndex((t) => t.key === active)
    const next = e.key === 'ArrowRight' ? Math.min(idx + 1, tabs.length - 1) : Math.max(idx - 1, 0)
    if (next !== idx && tabs[next]) select(tabs[next].key)
  }

  return (
    <div>
      <div
        onKeyDown={onKeyDown}
        className="flex overflow-x-auto border-b border-[var(--border)] bg-[var(--surface)]"
        style={{ scrollbarWidth: 'none', paddingLeft: 'var(--shell-content-pad-x)', paddingRight: 'var(--shell-content-pad-x)' }}
        role="tablist"
      >
        {tabs.map((tab) => {
          const Icon = tab.icon
          const isActive = tab.key === active
          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={isActive}
              tabIndex={isActive ? 0 : -1}
              onClick={() => select(tab.key)}
              className={clsx(
                'relative flex h-[38px] shrink-0 select-none items-center gap-[5px] whitespace-nowrap px-3 text-[12.5px] transition-colors duration-80',
                isActive
                  ? 'font-medium text-[var(--halo)]'
                  : 'text-[var(--ink-dim)] hover:text-[var(--ink)]',
              )}
            >
              {Icon && <Icon className="size-[13px]" strokeWidth={1.75} />}
              {tab.label}
              {tab.count !== undefined && (
                <span
                  className={clsx(
                    'rounded-full px-1.5 py-px text-[10.5px] leading-tight tabular-nums',
                    isActive
                      ? 'bg-[var(--halo-wash)] text-[var(--halo)]'
                      : 'bg-[var(--surface-3)] text-[var(--ink-faint)]',
                  )}
                >
                  {tab.count}
                </span>
              )}
              {isActive && (
                <span className="absolute inset-x-0 -bottom-px h-[2px] rounded-full bg-[var(--halo)]" />
              )}
            </button>
          )
        })}
      </div>
      <div className="pt-[16px]">{current?.content}</div>
    </div>
  )
}