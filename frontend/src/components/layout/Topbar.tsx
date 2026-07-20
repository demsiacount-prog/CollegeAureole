import { useMemo, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { ChevronDown, LogOut } from 'lucide-react'
import { useAuth } from '@/auth/AuthContext'
import { NAV_SECTIONS } from '@/routes/nav'
import { Avatar } from '@/components/ui/Avatar'
import { RoleBadge } from '@/components/ui/Badge'
import { useClickOutside } from '@/lib/useClickOutside'

export function Topbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  useClickOutside(menuRef, () => setMenuOpen(false))

  const pageTitle = useMemo(() => {
    for (const section of NAV_SECTIONS) {
      const match = section.items.find((item) =>
        item.path === '/app' ? location.pathname === '/app' : location.pathname.startsWith(item.path),
      )
      if (match) return match.label
    }
    return 'Tableau de bord'
  }, [location.pathname])

  if (!user) return null

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-[var(--color-border-soft)] bg-[var(--color-base)] px-6">
      <div>
        <h1 className="font-[var(--font-display)] text-[19px] font-medium tracking-tight text-[var(--color-ink)]">
          {pageTitle}
        </h1>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden items-center gap-2 rounded-full border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-1.5 text-xs text-[var(--color-ink-dim)] sm:flex">
          Année scolaire
          <span className="font-medium text-[var(--color-ink)]">2025 – 2026</span>
        </div>

        <div ref={menuRef} className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2.5 rounded-[var(--radius-sm)] py-1 pl-1 pr-2 transition-colors hover:bg-[var(--color-surface-2)]"
          >
            <Avatar nom={user.nom} prenom={user.prenom} size="sm" haloed />
            <span className="hidden text-left leading-tight md:block">
              <span className="block text-sm font-medium text-[var(--color-ink)]">
                {user.prenom} {user.nom}
              </span>
            </span>
            <ChevronDown className="size-3.5 text-[var(--color-ink-faint)]" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full z-20 mt-2 w-56 rounded-[var(--radius-md)] border border-[var(--color-border)] bg-[var(--color-surface-2)] p-1.5 shadow-[var(--shadow-soft)]">
              <div className="border-b border-[var(--color-border)] px-2.5 py-2">
                <p className="text-sm font-medium text-[var(--color-ink)]">
                  {user.prenom} {user.nom}
                </p>
                <p className="mb-1.5 truncate text-xs text-[var(--color-ink-faint)]">{user.email}</p>
                <RoleBadge role={user.role} />
              </div>
              <button
                onClick={logout}
                className="mt-1 flex w-full items-center gap-2 rounded-[var(--radius-sm)] px-2.5 py-2 text-sm text-[var(--color-danger)] transition-colors hover:bg-[var(--color-danger-wash)]"
              >
                <LogOut className="size-4" strokeWidth={1.75} />
                Déconnexion
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
