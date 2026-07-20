import { type InputHTMLAttributes, forwardRef, useId } from 'react'
import { clsx } from 'clsx'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, className, ...rest }, ref) => {
    const generatedId = useId()
    const inputId = id ?? generatedId

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-[var(--color-ink-dim)]">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
          className={clsx(
            'h-10 rounded-[var(--radius-sm)] border bg-[var(--color-surface-2)] px-3 text-sm text-[var(--color-ink)]',
            'placeholder:text-[var(--color-ink-faint)] transition-colors duration-150',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-halo)] focus-visible:border-[var(--color-halo)]',
            error ? 'border-[var(--color-danger)]' : 'border-[var(--color-border)]',
            className,
          )}
          {...rest}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-xs text-[var(--color-danger)]">
            {error}
          </p>
        )}
        {!error && hint && (
          <p id={`${inputId}-hint`} className="text-xs text-[var(--color-ink-faint)]">
            {hint}
          </p>
        )}
      </div>
    )
  },
)
Input.displayName = 'Input'
