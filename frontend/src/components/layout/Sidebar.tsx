import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import { NAV_SECTIONS } from '@/routes/nav'
import { useAuth } from '@/auth/useAuth'

export function Sidebar() {
  const { user } = useAuth()
  if (!user) return null

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-[var(--color-border-soft)] bg-[var(--color-surface)]">
      <div className="flex items-center gap-3 px-5 py-6">
        <span className="relative flex size-9 shrink-0 items-center justify-center rounded-full border border-[var(--color-halo-dim)]">
          <span className="absolute inset-0 rounded-full halo-ring" />
          <img src="/logo-emblem.png" alt="" className="size-6 object-contain" />
        </span>
        <div className="leading-tight">
          <p className="font-[var(--font-display)] text-[17px] tracking-tight text-[var(--color-ink)]">Collège Auréole</p>
          <p className="font-[var(--font-display)] italic text-[11px] text-[var(--color-halo-dim)]">
            L’excellent n’a pas de concurrent
          </p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-6">
        {NAV_SECTIONS.map((section) => {
          const visibleItems = section.items.filter((item) => item.roles.includes(user.role))
          if (visibleItems.length === 0) return null

          return (
            <div key={section.title} className="mb-5">
              <p className="mb-1.5 px-3 text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-faint)]">
                {section.title}
              </p>
              <div className="flex flex-col gap-0.5">
                {visibleItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/app'}
                    className={({ isActive }) =>
                      clsx(
                        'group flex items-center gap-2.5 rounded-[var(--radius-sm)] px-3 py-2 text-sm transition-colors duration-150',
                        isActive
                          ? 'bg-[var(--color-halo-wash)] text-[var(--color-halo-bright)]'
                          : 'text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]',
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <span
                          className={clsx(
                            'h-4 w-0.5 shrink-0 rounded-full transition-colors',
                            isActive ? 'bg-[var(--color-halo)]' : 'bg-transparent',
                          )}
                        />
                        <item.icon className="size-4 shrink-0" strokeWidth={1.75} />
                        <span className="truncate">{item.label}</span>
                      </>
                    )}
                  </NavLink>
                ))}
              </div>
            </div>
          )
        })}
      </nav>
    </aside>
  )
}
