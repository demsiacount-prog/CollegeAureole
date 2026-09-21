import { useRef, useState } from 'react'
import { LogOut, Moon, Search, Sun } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { useAnneeActive } from '@/features/annees_scolaires/useAnneeActive'
import { useCurrentModule } from '@/routes/useModule'
import { CommandPalette } from '@/components/ui/CommandPalette'
import { Tooltip } from '@/components/ui/Tooltip'
import { useClickOutside } from '@/lib/useClickOutside'
import { roleLabel } from '@/lib/roles'

function initials(nom: string, prenom: string) {
  return `${prenom.charAt(0)}${nom.charAt(0)}`.toUpperCase()
}

/** Design system §30 — TopBar contextuelle : breadcrumb + année + recherche + cloche + avatar. */
export function Topbar() {
  const { user, logout } = useAuth()
  const { theme, toggle: toggleTheme } = useTheme()
  const { data: annee } = useAnneeActive()
  const module = useCurrentModule()
  const [paletteOpen, setPaletteOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  useClickOutside(menuRef, () => setMenuOpen(false))

  if (!user) return null

  return (
    <header
      className="flex shrink-0 items-center gap-3 border-b border-[var(--border)] bg-[var(--surface)] px-4"
      style={{ height: 'var(--shell-topbar-h)' }}
    >
      {/* Breadcrumb contextuel */}
      <div className="flex min-w-0 flex-1 items-center gap-2 overflow-hidden whitespace-nowrap">
        {module ? (
          <>
            <span className="h-4 w-0.5 rounded-full bg-[var(--halo)]" />
            <span className="truncate text-[13px] font-medium tracking-[-0.01em] text-[var(--ink)]">
              {module.title}
            </span>
          </>
        ) : null}
      </div>

      {/* Année scolaire active (§30) — figée sur l'année courante */}
      {annee ? (
        <Tooltip content="Année scolaire active">
          <span
            className="flex max-w-[180px] items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)] px-[9px] text-[12px] text-[var(--ink)]"
            style={{ height: '28px' }}
          >
            <span className="size-[5px] shrink-0 rounded-full bg-[var(--success)]" />
            <span className="truncate">{annee.libelle}</span>
          </span>
        </Tooltip>
      ) : (
        <Tooltip content="Aucune année scolaire active">
          <span
            className="flex items-center gap-2 rounded-[var(--radius-md)] border border-dashed border-[var(--border)] bg-transparent px-[9px] text-[11.5px] text-[var(--warning)]"
            style={{ height: '28px' }}
          >
            <span className="size-[5px] shrink-0 rounded-full bg-[var(--warning)]" />
            <span className="hidden md:inline">Aucune année active</span>
          </span>
        </Tooltip>
      )}

      {/* Recherche (§40) */}
      <Tooltip content="Rechercher (Ctrl+K)">
      <button
        type="button"
        onClick={() => setPaletteOpen(true)}
        className="hidden items-center gap-2 rounded-[var(--radius-md)] bg-[var(--surface-2)] px-2.5 text-[11.5px] text-[var(--ink-faint)] transition-colors hover:bg-[var(--surface-3)] sm:flex"
        style={{ height: '28px', width: '224px' }}
      >
        <Search className="size-3.5 shrink-0" strokeWidth={1.75} />
        <span className="flex-1 truncate text-left">Rechercher…</span>
        <kbd className="rounded-[var(--radius-sm)] border border-[var(--border)] px-1 text-[9px] font-medium text-[var(--ink-faint)]">⌘K</kbd>
      </button>
      </Tooltip>

      {/* Thème */}
      <Tooltip content={theme === 'dark' ? 'Passer en thème clair' : 'Passer en thème sombre'}>
      <button
        type="button"
        onClick={toggleTheme}
        aria-label={theme === 'dark' ? 'Passer en thème clair' : 'Passer en thème sombre'}
        className="flex size-7 items-center justify-center rounded-[var(--radius-md)] text-[var(--ink-faint)] transition-colors duration-75 hover:bg-[var(--surface-2)] hover:text-[var(--ink)]"
      >
        {theme === 'dark' ? <Sun className="size-[15px]" strokeWidth={1.75} /> : <Moon className="size-[15px]" strokeWidth={1.75} />}
      </button>
      </Tooltip>

      {/* Cloche — notifications */}
      {/* <div className="relative" ref={bellRef}>
        <Tooltip content="Notifications">
        <button
          type="button"
          onClick={() => setBellOpen((o) => !o)}
          aria-label="Notifications"
          aria-expanded={bellOpen}
          className="relative flex size-7 items-center justify-center rounded-[var(--radius-md)] text-[var(--ink-dim)] transition-colors duration-75 hover:bg-[var(--surface-2)] hover:text-[var(--ink)]"
        >
          <Bell className="size-[15px]" strokeWidth={1.75} />
        </button>
        </Tooltip>
        {bellOpen && (
          <div className="animate-fade-in absolute right-0 top-[calc(100%+8px)] z-50 w-72 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] shadow-[0_16px_40px_-12px_rgba(0,0,0,0.25)]">
            <p className="border-b border-[var(--border)] px-3.5 py-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
              Notifications
            </p>
            <p className="px-3.5 py-6 text-center text-[12.5px] text-[var(--ink-faint)]">Aucune notification</p>
          </div>
        )}
      </div> */}

      {/* Avatar — menu utilisateur */}
      <div className="relative" ref={menuRef}>
        <button
          type="button"
          onClick={() => setMenuOpen((o) => !o)}
          aria-label="Menu utilisateur"
          aria-expanded={menuOpen}
          className="flex size-7 items-center justify-center rounded-full border border-[rgba(45,110,232,0.30)] bg-[var(--action-w)] text-[9.5px] font-semibold text-[var(--action)] transition-transform duration-75 hover:scale-[1.05]"
        >
          {initials(user.nom, user.prenom)}
        </button>
        {menuOpen && (
          <div className="animate-fade-in absolute right-0 top-[calc(100%+8px)] z-50 w-56 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] shadow-[0_16px_40px_-12px_rgba(0,0,0,0.25)]">
            <div className="border-b border-[var(--border)] px-3.5 py-3">
              <p className="truncate text-[13px] font-medium text-[var(--ink)]">
                {user.prenom} {user.nom}
              </p>
              <p className="truncate text-[11px] text-[var(--ink-faint)]">{roleLabel(user.role)}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-[12.5px] text-[var(--danger)] transition-colors hover:bg-[var(--surface-2)]"
            >
              <LogOut className="size-4" strokeWidth={1.75} />
              Se déconnecter
            </button>
          </div>
        )}
      </div>

      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </header>
  )
}