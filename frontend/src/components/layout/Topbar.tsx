import { useRef, useState } from 'react'
import { ChevronDown, LogOut, Moon, Sun } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { Avatar } from '@/components/ui/Avatar'
import { RoleBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { useClickOutside } from '@/lib/useClickOutside'

export function Topbar() {
  const { user, logout } = useAuth()
  const { theme, toggle: toggleTheme } = useTheme()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  useClickOutside(menuRef, () => setMenuOpen(false))

  if (!user) return null

  return (
    <header className="flex h-16 shrink-0 items-center justify-end border-b border-[var(--color-border-soft)] bg-[var(--color-base)] px-6">
      <div className="flex items-center gap-4">
        

        <button
          type="button"
          onClick={toggleTheme}
          className="rounded-md border border-[var(--color-border)] p-2 text-[var(--color-ink-dim)] hover:bg-[var(--color-surface-2)] transition-colors"
        >
          {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        <div ref={menuRef} className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2.5 rounded-[var(--radius-sm)] py-1 pl-1 pr-2 transition-colors hover:bg-[var(--color-surface-2)]"
          >
            <Avatar nom={user.nom} prenom={user.prenom} size="sm" highlighted />
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
              <Button
                variant="ghost"
                onClick={logout}
                className="mt-1 w-full justify-start text-[var(--color-danger)] hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]"
              >
                <LogOut className="size-4" strokeWidth={1.75} />
                Déconnexion
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
