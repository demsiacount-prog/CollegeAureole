import { Link, NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import { ChevronLeft, KeyRound, LogOut } from 'lucide-react'
import { navSectionsForRole } from '@/routes/nav'
import { useAuth } from '@/auth/useAuth'
import { useEtablissement } from '@/features/etablissement/useEtablissement'
import { LogoEtablissement } from '@/components/ui/LogoEtablissement'
import { Tooltip } from '@/components/ui/Tooltip'
import { roleLabel } from '@/lib/roles'

function initials(nom: string, prenom: string) {
  return `${prenom.charAt(0)}${nom.charAt(0)}`.toUpperCase()
}

/** Design system §29 — Sidebar navigation. 218px déployée, 52px réduite. */
export function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const { user, logout } = useAuth()
  const { data: etab } = useEtablissement()

  if (!user) return null

  const nom = etab?.nom ?? 'Collège Aureole'
  const logo = etab?.logo ?? null
  const initialsUser = initials(user.nom, user.prenom)

  return (
    <aside
      className={clsx(
        'flex shrink-0 flex-col border-r border-[var(--border)] bg-[var(--surface)]',
        collapsed && 'collapsed',
      )}
      style={{
        width: collapsed ? 'var(--shell-sidebar-col-w)' : 'var(--shell-sidebar-w)',
        minWidth: collapsed ? 'var(--shell-sidebar-col-w)' : 'var(--shell-sidebar-w)',
        transition: 'width 180ms ease, min-width 180ms ease',
      }}
      aria-label="Navigation principale"
    >
      {/* Header — logo mark + nom + bouton collapse */}
      <div className="flex h-[52px] shrink-0 items-center gap-[9px] px-3">
        {logo ? (
          <span className="relative flex size-[26px] shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--surface-2)]">
            <span className="absolute inset-0 rounded-[var(--radius-md)] halo-ring" />
            <LogoEtablissement src={logo} nom={nom} className="size-[18px]" />
          </span>
        ) : (
          <span className="relative flex size-[26px] shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--halo)] font-[var(--font-serif)] text-[14px] text-[var(--halo-ink)]">
            <span className="absolute inset-0 rounded-[var(--radius-md)] halo-ring" />
            {nom.charAt(0).toUpperCase()}
          </span>
        )}
        <p className="flex-1 truncate font-[var(--font-serif)] text-[14.5px] font-semibold leading-tight text-[var(--ink)] transition-opacity duration-150" style={{ opacity: collapsed ? 0 : 1 }}>
          {nom}
        </p>
        <button
          type="button"
          onClick={onToggle}
          title={collapsed ? 'Déployer le menu' : 'Réduire le menu'}
          aria-label={collapsed ? 'Déployer le menu' : 'Réduire le menu'}
          className="flex size-[22px] shrink-0 items-center justify-center rounded-[var(--radius-md)] text-[var(--ink-faint)] transition-colors duration-80 hover:bg-[var(--surface-2)] hover:text-[var(--ink)]"
        >
          <ChevronLeft className={clsx('size-4 transition-transform duration-180', collapsed && 'rotate-180')} strokeWidth={1.75} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden pb-6" role="navigation">
        {navSectionsForRole(user.role).map((section) => (
          <div key={section.title ?? 'standalone'}>
            {section.title && (
              <p className="px-[14px] pt-3.5 pb-0.5 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)] transition-opacity duration-150" style={{ opacity: collapsed ? 0 : 1 }}>
                {section.title}
              </p>
            )}
            <div className="flex flex-col">
              {section.items.map((item) => {
                return (
                  <Tooltip key={item.id} content={collapsed ? item.label : undefined}>
                  <NavLink
                    to={item.path}
                    end={item.path === '/app'}
                    aria-label={collapsed ? item.label : undefined}
                    className={({ isActive }) =>
                      clsx(
                        'group relative flex h-[34px] items-center overflow-hidden whitespace-nowrap rounded-[var(--radius-md)] px-2 text-[13px] select-none',
                        'transition-colors duration-80',
                        isActive
                          ? 'bg-[var(--halo-wash)] text-[var(--halo)]'
                          : 'text-[var(--ink-dim)] hover:bg-[var(--surface-2)] hover:text-[var(--ink)]',
                      )
                    }
                    style={{ margin: '1px 6px' }}
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <span className="absolute -left-1.5 top-1/2 h-[14px] w-0.5 -translate-y-1/2 rounded-r-md bg-[var(--halo)]" />
                        )}
                        <item.icon className="w-[18px] shrink-0 text-center text-[15px] text-inherit" strokeWidth={1.75} />
                        <span className="ml-[8px] flex-1 truncate text-left transition-opacity duration-150" style={{ opacity: collapsed ? 0 : 1 }}>
                          {item.label}
                        </span>
                        
                      </>
                    )}
                  </NavLink>
                  </Tooltip>
                )
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer — avatar + identité */}
      <footer className="flex shrink-0 items-center gap-2 overflow-hidden border-t border-[var(--border)] px-2.5 py-2">
        <span className="flex size-[26px] shrink-0 items-center justify-center rounded-full border border-[rgba(45,110,232,0.30)] bg-[var(--action-w)] text-[10px] font-semibold tracking-[0.02em] text-[var(--action)]">
          {initialsUser}
        </span>
        <div className="min-w-0 flex-1 leading-tight transition-opacity duration-150" style={{ opacity: collapsed ? 0 : 1 }}>
          <p className="truncate text-[12px] font-medium text-[var(--ink)]">
            {user.prenom} {user.nom}
          </p>
          <p className="truncate text-[10.5px] text-[var(--ink-faint)]">{roleLabel(user.role)}</p>
        </div>
        <Link to="/app/mot-de-passe" title="Changer mon mot de passe" aria-label="Changer mon mot de passe" className="rounded-[var(--radius-sm)] p-1.5 text-[var(--ink-dim)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--ink)]">
          <KeyRound className="size-3.5" strokeWidth={1.75} />
        </Link>
        <Tooltip content="Déconnexion">
          <button
            type="button"
            onClick={logout}
            aria-label="Se déconnecter"
            className="rounded-[var(--radius-sm)] p-1.5 text-[var(--ink-dim)] transition-colors hover:bg-[var(--danger-w)] hover:text-[var(--danger)]"
          >
            <LogOut className="size-3.5" strokeWidth={1.75} />
          </button>
        </Tooltip>
      </footer>
    </aside>
  )
}