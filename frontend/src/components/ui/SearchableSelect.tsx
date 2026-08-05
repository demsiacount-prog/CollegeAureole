import { useEffect, useMemo, useRef, useState } from 'react'
import { Check, ChevronDown, Search, X } from 'lucide-react'
import { clsx } from 'clsx'

export interface SearchableOption {
  value: string
  label: string
  sublabel?: string
}

interface SearchableSelectProps {
  label?: string
  value: string
  onChange: (value: string) => void
  options: SearchableOption[]
  placeholder?: string
  error?: string
  emptyMessage?: string
  disabled?: boolean
}

function normalize(s: string): string {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

export function SearchableSelect({
  label,
  value,
  onChange,
  options,
  placeholder = '— Sélectionner —',
  error,
  emptyMessage = 'Aucun résultat',
  disabled,
}: SearchableSelectProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const rootRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [highlight, setHighlight] = useState(0)

  const selected = useMemo(() => options.find((o) => o.value === value), [options, value])

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDocClick)
    return () => document.removeEventListener('mousedown', onDocClick)
  }, [])

  const filtered = useMemo(() => {
    const q = normalize(query.trim())
    if (!q) return options
    return options.filter((o) => normalize(o.label).includes(q) || (o.sublabel ? normalize(o.sublabel).includes(q) : false))
  }, [options, query])

  useEffect(() => {
    setHighlight(0)
  }, [query])

  function handleSelect(o: SearchableOption) {
    onChange(o.value)
    setQuery('')
    setOpen(false)
  }

  function handleClear() {
    onChange('')
    setQuery('')
    setOpen(false)
    inputRef.current?.focus()
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Escape') {
      setOpen(false)
      setQuery('')
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setOpen(true)
      setHighlight((h) => Math.min(h + 1, filtered.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setHighlight((h) => Math.max(h - 1, 0))
    } else if (e.key === 'Enter') {
      if (open && filtered[highlight]) {
        e.preventDefault()
        handleSelect(filtered[highlight])
      } else {
        setOpen(true)
      }
    }
  }

  return (
    <div className="flex flex-col gap-1.5" ref={rootRef}>
      {label && (
        <span className="text-sm font-medium text-[var(--color-ink-dim)]">{label}</span>
      )}
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--color-ink-faint)]" />
        <input
          ref={inputRef}
          role="combobox"
          aria-expanded={open}
          aria-autocomplete="list"
          aria-invalid={!!error}
          value={open ? query : selected?.label ?? ''}
          onChange={(e) => {
            setQuery(e.target.value)
            setOpen(true)
          }}
          onFocus={() => {
            setOpen(true)
            if (selected) setQuery(selected.label)
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={clsx(
            'h-10 w-full rounded-[var(--radius-sm)] border bg-[var(--color-surface-2)] pl-9 pr-9 text-sm text-[var(--color-ink)]',
            'placeholder:text-[var(--color-ink-faint)] transition-colors duration-150',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-halo)] focus-visible:border-[var(--color-halo)]',
            error ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
          )}
        />
        {selected && !disabled && (
          <button
            type="button"
            onClick={handleClear}
            aria-label="Effacer la sélection"
            className="absolute right-8 top-1/2 -translate-y-1/2 rounded-full p-0.5 text-[var(--color-ink-faint)] transition-colors hover:text-[var(--color-ink)]"
          >
            <X className="size-3.5" />
          </button>
        )}
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-[var(--color-ink-faint)]" />
      </div>
      {open && !disabled && (
        <div className="relative z-20">
          <ul
            role="listbox"
            className="absolute left-0 right-0 max-h-56 overflow-auto rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface)] py-1 shadow-[var(--shadow-soft)]"
          >
            {filtered.length === 0 ? (
              <li className="px-3 py-2 text-sm text-[var(--color-ink-faint)]">{emptyMessage}</li>
            ) : (
              filtered.map((o, i) => (
                <li key={o.value}>
                  <button
                    type="button"
                    role="option"
                    aria-selected={o.value === value}
                    onClick={() => handleSelect(o)}
                    onMouseEnter={() => setHighlight(i)}
                    className={clsx(
                      'flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-sm transition-colors',
                      i === highlight ? 'bg-[var(--color-surface-3)] text-[var(--color-ink)]' : 'text-[var(--color-ink)] hover:bg-[var(--color-surface-2)]',
                    )}
                  >
                    <span className="truncate">
                      {o.label}
                      {o.sublabel && <span className="ml-2 font-mono text-xs text-[var(--color-ink-faint)]">{o.sublabel}</span>}
                    </span>
                    {o.value === value && <Check className="size-4 shrink-0 text-[var(--color-brand-bright)]" />}
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
      {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
    </div>
  )
}
