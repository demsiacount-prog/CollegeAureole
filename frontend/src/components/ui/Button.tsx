import { type ButtonHTMLAttributes, type AnchorHTMLAttributes, forwardRef } from 'react'
import { Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { Link } from 'react-router-dom'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'icon'
type Size = 'icon' | 'sm' | 'md'
type Tone = 'neutral' | 'danger' | 'success' | 'warning'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  tone?: Tone
  isLoading?: boolean
  to?: string
  href?: string
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-[var(--color-brand)] text-white hover:bg-[var(--color-brand-dark)] shadow-[0_1px_0_0_rgba(255,255,255,0.15)_inset]',
  secondary:
    'bg-[var(--color-surface-3)] text-[var(--color-ink)] border border-[var(--color-border)] hover:bg-[var(--color-surface-2)]',
  ghost: 'bg-transparent text-[var(--color-ink-dim)]',
  danger: 'bg-transparent text-[var(--color-danger)] border border-[var(--color-danger)]/40 hover:bg-[var(--color-danger-wash)]',
  icon: 'bg-transparent text-[var(--color-ink-faint)]',
}

const hoverTones: Record<Tone, string> = {
  neutral: 'hover:bg-[var(--color-surface-3)] hover:text-[var(--color-ink)]',
  danger: 'hover:bg-[var(--color-danger-wash)] hover:text-[var(--color-danger)]',
  success: 'hover:bg-[var(--color-success-wash)] hover:text-[var(--color-success)]',
  warning: 'hover:bg-[var(--color-warning-wash)] hover:text-[var(--color-warning)]',
}

const sizeClasses: Record<Size, string> = {
  icon: 'size-8',
  sm: 'h-8 px-3 text-sm gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
}

const baseClasses = (variant: Variant, size: Size, tone: Tone, className?: string) =>
  clsx(
    'inline-flex items-center justify-center rounded-[var(--radius-sm)] font-medium transition-colors duration-150',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    variantClasses[variant],
    (variant === 'ghost' || variant === 'icon') && hoverTones[tone],
    sizeClasses[size],
    className,
  )

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'secondary', size = 'md', tone = 'neutral', isLoading, disabled, className, to, href, children, ...rest }, ref) => {
    const classes = baseClasses(variant, size, tone, className)
    const content = (
      <>
        {isLoading && <Loader2 className="size-4 animate-spin" />}
        {children}
      </>
    )
    if (to) {
      return (
        <Link to={to} className={classes}>
          {content}
        </Link>
      )
    }
    if (href) {
      return (
        <a href={href} className={classes} {...(rest as AnchorHTMLAttributes<HTMLAnchorElement>)}>
          {content}
        </a>
      )
    }
    return (
      <button ref={ref} disabled={disabled || isLoading} className={classes} {...rest}>
        {content}
      </button>
    )
  },
)
Button.displayName = 'Button'
