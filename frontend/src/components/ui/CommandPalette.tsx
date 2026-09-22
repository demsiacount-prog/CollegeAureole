import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { BookOpen, ClipboardList, CreditCard, GraduationCap, Pencil, Search, User, type LucideIcon } from 'lucide-react'
import { clsx } from 'clsx'
import { allNavItems } from '@/routes/nav'
import { useAuth } from '@/auth/useAuth'
import { fetchEleves } from '@/features/eleves/api'
import { fetchEnseignants } from '@/features/enseignants/api'
import type { Eleve } from '@/features/eleves/types'
import type { Enseignant } from '@/features/enseignants/types'

interface PaletteEntry {
  id: string
  label: string
  hint?: string
  icon: LucideIcon
  to: string
}

const QUICK_ACTIONS: PaletteEntry[] = [
  { id: 'action-eleve', label: 'Ajouter un élève', hint: 'Élèves', icon: ClipboardList, to: '/app/eleves' },
  { id: 'action-inscription', label: 'Nouvelle inscription', hint: 'Inscriptions', icon: BookOpen, to: '/app/inscriptions' },
  { id: 'action-paiement', label: 'Enregistrer un paiement', hint: 'Paiements', icon: CreditCard, to: '/app/paiements' },
  { id: 'action-note', label: 'Saisir les notes', hint: 'Notes', icon: Pencil, to: '/app/notes' },
]

const kbd = 'inline-flex min-w-[18px] items-center justify-center rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface-2)] px-1 py-px text-[9.5px] font-medium text-[var(--ink-faint)]'

/** Design system §40 — Command palette (Ctrl+K).
 *  Utilisation libre (autonome) ou contrôlée via `open`/`onOpenChange`. */
export function CommandPalette({
  open: openProp,
  onOpenChange,
}: {
  open?: boolean
  onOpenChange?: (open: boolean) => void
} = {}) {
  const [internalOpen, setInternalOpen] = useState(false)
  const open = openProp ?? internalOpen
  const setOpen = useCallback(
    (o: boolean) => (onOpenChange ? onOpenChange(o) : setInternalOpen(o)),
    [onOpenChange],
  )
  const openRef = useRef(open)
  useEffect(() => {
    openRef.current = open
  }, [open])
  const [query, setQuery] = useState('')
  const [activeIndex, setActiveIndex] = useState(0)
  const [apiEleves, setApiEleves] = useState<Eleve[]>([])
  const [apiEnseignants, setApiEnseignants] = useState<Enseignant[]>([])
  const [searching, setSearching] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const listRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const { user } = useAuth()

  // §40 — recherche API élèves/enseignants, debounce 250 ms (dès 2 caractères).
  useEffect(() => {
    const q = query.trim()
    if (q.length < 2) {
      setApiEleves([])
      setApiEnseignants([])
      setSearching(false)
      return
    }
    setSearching(true)
    const timer = setTimeout(async () => {
      try {
        const [eleves, enseignants] = await Promise.all([
          fetchEleves({ q, limit: 6 }),
          fetchEnseignants({ q, limit: 6 }),
        ])
        setApiEleves(eleves)
        setApiEnseignants(enseignants)
      } catch {
        setApiEleves([])
        setApiEnseignants([])
      } finally {
        setSearching(false)
      }
    }, 250)
    return () => {
      clearTimeout(timer)
      setSearching(false)
    }
  }, [query])

  const pages: PaletteEntry[] = useMemo(
    () =>
      allNavItems(user?.role).map((item) => ({
        id: item.id,
        label: item.label,
        hint: item.path,
        icon: item.icon,
        to: item.path,
      })),
    [user?.role],
  )

  const entries = useMemo(() => {
    const q = query.trim().toLowerCase()
    const filter = (list: PaletteEntry[]) =>
      q ? list.filter((e) => e.label.toLowerCase().includes(q) || (e.hint ?? '').toLowerCase().includes(q)) : list
    const pagesFiltered = filter(pages)
    const actionsFiltered = filter(QUICK_ACTIONS)
    const eleves: PaletteEntry[] = apiEleves.map((e) => ({
      id: `eleve-${e.matricule}`,
      label: `${e.prenom} ${e.nom}`,
      hint: e.matricule,
      icon: User,
      to: `/app/eleves/${e.matricule}`,
    }))
    const enseignants: PaletteEntry[] = apiEnseignants.map((e) => ({
      id: `enseignant-${e.matricule}`,
      label: `${e.prenom} ${e.nom}`,
      hint: e.specialite,
      icon: GraduationCap,
      to: `/app/enseignants/${e.matricule}`,
    }))
    return {
      pages: pagesFiltered,
      actions: actionsFiltered,
      eleves,
      enseignants,
      total: pagesFiltered.length + actionsFiltered.length + eleves.length + enseignants.length,
    }
  }, [pages, query, apiEleves, apiEnseignants])

  useEffect(() => setOpen(false), [pathname, setOpen])

  useEffect(() => {
    function onGlobalKey(e: KeyboardEvent) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setOpen(!openRef.current)
      }
    }
    window.addEventListener('keydown', onGlobalKey)
    return () => window.removeEventListener('keydown', onGlobalKey)
  }, [setOpen])

  useEffect(() => {
    if (open) {
      setQuery('')
      setActiveIndex(0)
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open, setOpen])

  // §42 — Escape ferme la palette même quand le focus n'est plus sur l'input.
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, setOpen])

  if (!open) return null

  function goTo(to: string) {
    setOpen(false)
    navigate(to)
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Escape') {
      e.preventDefault()
      setOpen(false)
      return
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, Math.max(entries.total - 1, 0)))
      return
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, 0))
      return
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      const flat = [...entries.pages, ...entries.actions, ...entries.eleves, ...entries.enseignants]
      const target = flat[activeIndex]
      if (target) goTo(target.to)
    }
  }

  function renderRow(entry: PaletteEntry, index: number) {
    const active = index === activeIndex
    return (
      <button
        key={entry.id}
        type="button"
        onMouseEnter={() => setActiveIndex(index)}
        onClick={() => goTo(entry.to)}
        className={clsx(
          'flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors',
          active ? 'bg-[var(--surface-2)]' : 'bg-transparent',
        )}
      >
        <span className={clsx('flex size-[26px] shrink-0 items-center justify-center rounded-[var(--radius-md)]', active ? 'bg-[var(--halo-wash)] text-[var(--halo)]' : 'bg-[var(--surface-2)] text-[var(--ink-dim)]')}>
          <entry.icon className="size-4" strokeWidth={1.75} />
        </span>
        <span className="flex-1 truncate text-[13px] text-[var(--ink)]">{entry.label}</span>
        {entry.hint && <span className="truncate text-[10.5px] text-[var(--ink-faint)]">{entry.hint}</span>}
      </button>
    )
  }

  const flatEntries = [...entries.pages, ...entries.actions, ...entries.eleves, ...entries.enseignants]

  return (
    <div className="fixed inset-0 z-[400] flex items-start justify-center px-3 pt-[12vh]" role="dialog" aria-modal="true">
      <div className="animate-fade-in absolute inset-0 bg-[rgba(6,9,16,0.45)]" onClick={() => setOpen(false)} />
      <div className="animate-modal-in relative w-full max-w-[520px] overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border)] bg-[var(--surface)] shadow-[0_24px_60px_-16px_rgba(0,0,0,0.35)]">
        {/* Barre de recherche */}
        <div className="flex h-[46px] items-center gap-2 border-b border-[var(--border)] px-3.5">
          <Search className="size-4 shrink-0 text-[var(--ink-faint)]" strokeWidth={1.75} />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setActiveIndex(0)
            }}
            onKeyDown={onKeyDown}
            placeholder="Rechercher une page, une action…"
            autoComplete="off"
            spellCheck={false}
            className="h-full flex-1 bg-transparent text-[13px] text-[var(--ink)] outline-none placeholder:text-[var(--ink-faint)]"
          />
          <kbd aria-hidden className={kbd}>ESC</kbd>
        </div>

        {/* Résultats */}
        <div ref={listRef} className="max-h-[52vh] overflow-y-auto pb-2">
          {entries.total === 0 && !searching && (
            <p className="px-4 py-8 text-center text-[12.5px] text-[var(--ink-faint)]">Aucun résultat pour « {query} »</p>
          )}
          {entries.total === 0 && searching && (
            <p className="px-4 py-8 text-center text-[12.5px] text-[var(--ink-faint)]">Recherche…</p>
          )}
          {entries.pages.length > 0 && (
            <div className="pt-1.5">
              <p className="px-3.5 pb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">Pages</p>
              {entries.pages.map((e) => renderRow(e, flatEntries.indexOf(e)))}
            </div>
          )}
          {entries.actions.length > 0 && (
            <div className="pt-1.5">
              <p className="px-3.5 pb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">Actions rapides</p>
              {entries.actions.map((e) => renderRow(e, flatEntries.indexOf(e)))}
            </div>
          )}
          {entries.eleves.length > 0 && (
            <div className="pt-1.5">
              <p className="px-3.5 pb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">Élèves</p>
              {entries.eleves.map((e) => renderRow(e, flatEntries.indexOf(e)))}
            </div>
          )}
          {entries.enseignants.length > 0 && (
            <div className="pt-1.5">
              <p className="px-3.5 pb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-[var(--ink-faint)]">Enseignants</p>
              {entries.enseignants.map((e) => renderRow(e, flatEntries.indexOf(e)))}
            </div>
          )}
        </div>

        {/* Pied de la palette */}
        <div className="flex items-center gap-3 border-t border-[var(--border)] px-3.5 py-2">
          <span className="flex items-center gap-1 text-[10px] text-[var(--ink-faint)]">
            <kbd className={kbd}>↑</kbd> <kbd className={kbd}>↓</kbd> naviguer
          </span>
          <span className="flex items-center gap-1 text-[10px] text-[var(--ink-faint)]">
            <kbd className={kbd}>↵</kbd> ouvrir
          </span>
        </div>
      </div>
    </div>
  )
}