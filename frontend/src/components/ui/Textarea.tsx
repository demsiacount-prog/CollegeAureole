import { type TextareaHTMLAttributes, forwardRef, useId } from 'react'
import { clsx } from 'clsx'

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  hint?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, id, className, ...rest }, ref) => {
    const generatedId = useId()
    const textareaId = id ?? generatedId

    return (
      <div className="flex flex-col gap-[5px]">
        {label && (
          <label htmlFor={textareaId} className="text-[12px] font-medium text-[var(--ink-dim)]">
            {label}
            {rest.required && <span className="ml-[2px] text-[var(--danger)]">*</span>}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          aria-invalid={!!error}
          aria-describedby={error ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined}
          className={clsx(
            'w-full min-h-[80px] resize-y rounded-[var(--radius-md)] border bg-[var(--surface)] px-[11px] py-[9px]',
            'text-[13px] leading-[1.5] text-[var(--ink)]',
            'placeholder:text-[var(--ink-disabled)] transition-colors duration-100',
            'focus:outline-none',
            error
              ? 'focus:border-[var(--danger)] focus:shadow-[0_0_0_3px_rgba(224,112,127,0.20)]'
              : 'focus:border-[var(--action)] focus:shadow-[0_0_0_3px_var(--action-ring)]',
            'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-[var(--surface-2)]',
            error ? 'border-[var(--danger)]' : 'border-[var(--border)]',
            className,
          )}
          {...rest}
        />
        {error && (
          <p id={`${textareaId}-error`} className="text-[11.5px] text-[var(--danger)]">
            {error}
          </p>
        )}
        {!error && hint && (
          <p id={`${textareaId}-hint`} className="text-[11.5px] text-[var(--ink-faint)]">
            {hint}
          </p>
        )}
      </div>
    )
  },
)
Textarea.displayName = 'Textarea'