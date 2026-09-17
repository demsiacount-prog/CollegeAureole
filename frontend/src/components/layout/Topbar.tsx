import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, ChevronDown, LogOut, Moon, Search, Sun } from 'lucide-react'
import { useAuth } from '@/auth/useAuth'
import { useTheme } from '@/hooks/useTheme'
import { fetchAnneesScolaires, activerAnneeScolaire } from '@/features/annees_scolaires/api'
import { useAnneeActive } from '@/features/annees_scolaires/useAnneeActive'
import { useCurrentModule } from '@/routes/useModule'
import { CommandPalette } from '@/components/ui/CommandPalette'
import { Tooltip } from '@/components/ui/Tooltip'
import { useClickOutside } from '@/lib/useClickOutside'
import { toast } from '@/components/ui/toast'
import { extractErrorMessage } from '@/lib/api'
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
  const [bellOpen, setBellOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [anneeOpen, setAnneeOpen] = useState(false)
  const bellRef = useRef<HTMLDivElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const anneeRef = useRef<HTMLDivElement>(null)
  const queryClient = useQueryClient()
  useClickOutside(bellRef, () => setBellOpen(false))
  useClickOutside(menuRef, () => setMenuOpen(false))
  useClickOutside(anneeRef, () => setAnneeOpen(false))

  const { data: annees = [] } = useQuery({
    queryKey: ['annees-scolaires'],
    queryFn: fetchAnneesScolaires,
    staleTime: 2 * 60_000,
  })

  const activerMutation = useMutation({
    mutationFn: activerAnneeScolaire,
    onSuccess: () => {
      setAnneeOpen(false)
      toast('Année scolaire activée. Les données rechargent…')
      queryClient.invalidateQueries({ queryKey: ['anneesScolaires'] })
      queryClient.invalidateQueries({ queryKey: ['annees-scolaires'] })
    },
    onError: (err: Error) => {
      toast(extractErrorMessage(err, "Impossible d'activer cette année."), 'error')
    },
  })

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

      {/* Année scolaire active — sélecteur (§30) */}
      <div className="relative" ref={anneeRef}>
        {annee ? (
          <Tooltip content="Changer d'année scolaire">
          <button
            type="button"
            onClick={() => setAnneeOpen((o) => !o)}
            aria-expanded={anneeOpen}
            className="flex max-w-[180px] items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface-2)] px-[9px] text-[12px] text-[var(--ink-dim)] transition-colors duration-75 hover:bg-[var(--surface-3)]"
            style={{ height: '28px' }}
          >
            <span className="size-[5px] shrink-0 rounded-full bg-[var(--success)]" />
            <span className="truncate">{annee.libelle}</span>
            <ChevronDown className="size-3 shrink-0 text-[var(--ink-faint)]" strokeWidth={1.75} />
          </button>
          </Tooltip>
        ) : (
          <Tooltip content="Aucune année scolaire active">
          <button
            type="button"
            onClick={() => setAnneeOpen((o) => !o)}
            aria-expanded={anneeOpen}
            className="flex items-center gap-2 rounded-[var(--radius-md)] border border-dashed border-[var(--border)] bg-transparent px-[9px] text-[11.5px] text-[var(--warning)] transition-colors duration-75 hover:bg-[var(--surface-2)]"
            style={{ height: '28px' }}
          >
            <span className="size-[5px] shrink-0 rounded-full bg-[var(--warning)]" />
            <span className="hidden md:inline">Aucune année active</span>
            <ChevronDown className="size-3 shrink-0" strokeWidth={1.75} />
          </button>
          </Tooltip>
        )}
        {anneeOpen && (
          <div className="animate-fade-in absolute right-0 top-[calc(100%+8px)] z-50 min-w-[220px] overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border)] bg-[var(--surface)] shadow-[0_16px_40px_-12px_rgba(0,0,0,0.25)]">
            <p className="border-b border-[var(--border)] px-3.5 py-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">
              Année scolaire
            </p>
            {annees.length === 0 && (
              <p className="px-3.5 py-6 text-center text-[12.5px] text-[var(--ink-faint)]">Aucune année</p>
            )}
            {annees.map((a) => (
              <button
                key={a.id}
                type="button"
                disabled={a.active || activerMutation.isPending}
                onClick={() => activerMutation.mutate(a.id)}
                className="flex w-full items-center gap-2 px-3.5 py-2.5 text-left text-[12.5px] transition-colors hover:bg-[var(--surface-2)] disabled:cursor-default disabled:hover:bg-transparent"
              >
                <span className={`size-[5px] shrink-0 rounded-full ${a.active ? 'bg-[var(--success)]' : 'bg-transparent'}`} />
                <span className={`flex-1 truncate ${a.active ? 'font-medium text-[var(--ink)]' : 'text-[var(--ink-dim)]'}`}>
                  {a.libelle}
                </span>
                {a.active && <span className="text-[10px] font-medium uppercase tracking-wide text-[var(--success)]">Active</span>}
              </button>
            ))}
          </div>
        )}
      </div>

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
      <div className="relative" ref={bellRef}>
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
      </div>

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