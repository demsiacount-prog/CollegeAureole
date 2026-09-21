import { clsx } from 'clsx'

interface SwitchProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label?: string
  ariaLabel?: string
  disabled?: boolean
  className?: string
}

/** Design system §34 — Switch (toggle) 36×20, thumb 16px, fond action quand activé. */
export function Switch({ checked, onChange, label, ariaLabel, disabled, className }: SwitchProps) {
  return (
    <label className={clsx('flex cursor-pointer items-center gap-2 select-none', disabled && 'cursor-not-allowed opacity-50', className)}>
      <span className="relative inline-block h-5 w-9 shrink-0">
        <input
          type="checkbox"
          checked={checked}
          disabled={disabled}
          aria-label={ariaLabel}
          onChange={(e) => onChange(e.target.checked)}
          className="sr-only"
        />
        <span
          className={clsx(
            'absolute inset-0 rounded-[10px] transition-colors duration-150',
            checked ? 'bg-[var(--action)]' : 'bg-[var(--surface-3)]',
          )}
        />
        <span
          className={clsx(
            'absolute left-[2px] top-[2px] size-4 rounded-full bg-white shadow-[0_1px_3px_rgba(0,0,0,0.30)] transition-transform duration-150',
            checked && 'translate-x-4',
          )}
        />
      </span>
      {label && <span className="text-[13px] text-[var(--ink-dim)]">{label}</span>}
    </label>
  )
}