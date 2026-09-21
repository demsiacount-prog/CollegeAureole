import { type SelectHTMLAttributes, forwardRef, useId } from 'react'
import { ChevronDown } from 'lucide-react'
import { clsx } from 'clsx'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  /** Alternative aux <option> passées en children. */
  options?: { value: string | number; label: string }[]
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, id, className, children, options, ...rest }, ref) => {
    const generatedId = useId()
    const selectId = id ?? generatedId

    return (
      <div className="flex flex-col gap-[5px]">
        {label && (
          <div className="flex items-start gap-[2px]">
            <label htmlFor={selectId} className="text-[12px] font-medium text-[var(--ink-dim)]">
              {label}
            </label>
            {rest.required && (
              <span aria-hidden="true" className="translate-y-[-1px] text-[12px] leading-[150%] text-[var(--danger)]">
                *
              </span>
            )}
          </div>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            aria-invalid={!!error}
            className={clsx(
              'h-[34px] w-full appearance-none rounded-[var(--radius-md)] border bg-[var(--surface)] pl-[11px] pr-[30px] text-[13px] text-[var(--ink)]',
              'transition-colors duration-100 cursor-pointer',
              'focus:outline-none cursor-pointer',
              error
                ? 'focus:border-[var(--danger)] focus:shadow-[0_0_0_3px_rgba(224,112,127,0.20)]'
                : 'focus:border-[var(--action)] focus:shadow-[0_0_0_3px_var(--action-ring)]',
              'disabled:cursor-not-allowed disabled:opacity-50',
              error ? 'border-[var(--danger)]' : 'border-[var(--border)]',
              className,
            )}
            {...rest}
          >
            {options
              ? options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))
              : children}
          </select>
          <ChevronDown className="pointer-events-none absolute right-[10px] top-1/2 size-3 -translate-y-1/2 text-[var(--ink-faint)]" />
        </div>
        {error && <p className="text-[11.5px] text-[var(--danger)]">{error}</p>}
      </div>
    )
  },
)
Select.displayName = 'Select'