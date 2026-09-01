import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import { NAV_SECTIONS } from '@/routes/nav'
import { useNavBadges } from '@/routes/useNavBadges'
import { useAuth } from '@/auth/useAuth'
import { useEtablissement } from '@/features/etablissement/useEtablissement'
import { LogoEtablissement } from '@/components/ui/LogoEtablissement'

export function Sidebar() {
  const { user } = useAuth()
  const { data: etab } = useEtablissement()
  const badges = useNavBadges()
  if (!user) return null

  const nom = etab?.nom ?? ''
  const device = etab?.devise?.trim() ?? ''

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-[var(--color-border-soft)] bg-[var(--color-surface)]">
      {etab && (
        <div className="flex items-center gap-3 px-5 py-6">
          {etab.logo ? (
            <span className="relative flex size-11 shrink-0 items-center justify-center rounded-xl border border-[var(--color-halo-dim)] bg-[var(--color-surface-2)]">
              <span className="absolute inset-0 rounded-xl halo-ring" />
              <LogoEtablissement src={etab.logo} nom={nom} className="size-8" />
            </span>
          ) : null}
          <div className="leading-tight">
            <p className="font-[var(--font-display)] text-[16px] leading-tight tracking-tight text-[var(--color-ink)]">{nom}</p>
            {device && (
              <p className="mt-0.5 font-[var(--font-display)] italic text-[11px] text-[var(--color-halo-dim)]">{device}</p>
            )}
          </div>
        </div>
      )}

      <nav className="flex-1 overflow-y-auto px-3 pb-6">
        {NAV_SECTIONS.map((section) => {
          const visibleItems = section.items.filter((item) => item.roles.includes(user.role))
          if (visibleItems.length === 0) return null

          return (
            <div key={section.title} className="mb-5">
              <p className="mb-1.5 flex items-center gap-1.5 px-3 text-[11px] font-medium uppercase tracking-wider text-[var(--color-ink-faint)]">
                {section.moduleColor && (
                  <span className="size-[5px] shrink-0 rounded-full" style={{ background: section.moduleColor }} />
                )}
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
                        {(badges[item.path] ?? item.count) != null && (badges[item.path] ?? item.count) > 0 && (
                          <span
                            className={clsx(
                              'ml-auto rounded-full px-1.5 py-0.5 font-mono text-[10px] leading-none',
                              isActive
                                ? 'bg-[var(--color-halo-wash)] text-[var(--color-halo)]'
                                : 'bg-[var(--color-surface-3)] text-[var(--color-ink-faint)]',
                            )}
                          >
                            {badges[item.path] ?? item.count}
                          </span>
                        )}
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
