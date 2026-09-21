import { type InputHTMLAttributes, forwardRef, useId, useCallback } from 'react'
import { clsx } from 'clsx'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, className, onKeyDown, onPaste, ...rest }, ref) => {
    const generatedId = useId()
    const inputId = id ?? generatedId

    const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLInputElement>) => {
      if (rest.type === 'number') {
        if (e.ctrlKey || e.metaKey) return
        const allowed = ['Backspace', 'Delete', 'Tab', 'Escape', 'Enter', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End']
        if (allowed.includes(e.key)) return
        if (!/^[\d.]$/.test(e.key)) {
          e.preventDefault()
        }
      }
      onKeyDown?.(e)
    }, [rest.type, onKeyDown])

    const handlePaste = useCallback((e: React.ClipboardEvent<HTMLInputElement>) => {
      if (rest.type === 'number') {
        const data = e.clipboardData.getData('text')
        if (!/^[\d.]+$/.test(data)) {
          e.preventDefault()
        }
      }
      onPaste?.(e)
    }, [rest.type, onPaste])

    return (
      <div className="flex flex-col gap-[5px]">
        {label && (
          <div className="flex items-start gap-[2px]">
            <label htmlFor={inputId} className="text-[12px] font-medium text-[var(--ink-dim)]">
              {label}
            </label>
            {rest.required && (
              <span aria-hidden="true" className="translate-y-[-1px] text-[12px] leading-[150%] text-[var(--danger)]">
                *
              </span>
            )}
          </div>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={!!error}
          aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          className={clsx(
            'h-[34px] w-full rounded-[var(--radius-md)] border bg-[var(--surface)] px-[11px] text-[13px] text-[var(--ink)]',
            'placeholder:text-[var(--ink-disabled)] transition-colors duration-100',
            'focus:outline-none',
            error
              ? 'focus:border-[var(--danger)] focus:shadow-[0_0_0_3px_rgba(224,112,127,0.20)]'
              : 'focus:border-[var(--action)] focus:shadow-[0_0_0_3px_var(--action-ring)]',
            'disabled:cursor-not-allowed disabled:bg-[var(--surface-2)] disabled:opacity-50',
            error ? 'border-[var(--danger)]' : 'border-[var(--border)]',
            className,
          )}
          {...rest}
        />
        {error && (
          <p id={`${inputId}-error`} className="text-[11.5px] text-[var(--danger)]">
            {error}
          </p>
        )}
        {!error && hint && (
          <p id={`${inputId}-hint`} className="text-[11.5px] text-[var(--ink-faint)]">
            {hint}
          </p>
        )}
      </div>
    )
  },
)
Input.displayName = 'Input'