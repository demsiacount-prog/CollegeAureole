import { type ButtonHTMLAttributes, type AnchorHTMLAttributes, forwardRef, type ComponentProps } from 'react'
import { Loader2 } from 'lucide-react'
import { clsx } from 'clsx'
import { Link } from 'react-router-dom'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'ghost-danger' | 'icon'
type Size = 'sm' | 'md' | 'lg' | 'icon'
type Tone = 'neutral' | 'danger' | 'success' | 'warning'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  tone?: Tone
  isLoading?: boolean
  to?: string
  href?: string
}

/** Design system §33 — Boutons & Actions.
 *  Base : 30px de haut, radius-md, Inter 12.5px/500, transition 80ms. */
const variantClasses: Record<Variant, string> = {
  primary:
    'bg-[var(--halo)] text-[var(--halo-ink)] hover:bg-[var(--halo-bright)] active:bg-[var(--halo-dim)]',
  secondary:
    'bg-[var(--surface-3)] text-[var(--ink)] border border-[var(--border)] hover:bg-[var(--surface-2)] active:bg-[var(--surface-3)]',
  ghost:
    'bg-transparent text-[var(--ink-dim)] border border-[var(--border)] hover:bg-[var(--surface-2)] hover:text-[var(--ink)] active:bg-[var(--surface-3)]',
  danger:
    'bg-[var(--danger)] text-white hover:bg-[#e8848f] active:bg-[#c85e6b]',
  'ghost-danger':
    'bg-transparent text-[var(--danger)] border border-[rgba(224,112,127,0.30)] hover:bg-[var(--danger-w)]',
  icon: 'bg-transparent text-[var(--ink-faint)]',
}

const hoverTones: Record<Tone, string> = {
  neutral: 'hover:bg-[var(--surface-3)] hover:text-[var(--ink)]',
  danger: 'hover:bg-[var(--danger-w)] hover:text-[var(--danger)]',
  success: 'hover:bg-[var(--success-w)] hover:text-[var(--success)]',
  warning: 'hover:bg-[var(--warning-w)] hover:text-[var(--warning)]',
}

const sizeClasses: Record<Size, string> = {
  sm: 'h-[26px] px-[9px] text-[12px]',
  md: 'h-[30px] px-[11px] text-[12.5px]',
  lg: 'h-[36px] px-[14px] text-[13.5px]',
  icon: 'size-[30px] p-0 [&>svg]:size-[15px]',
}

const baseClasses = (variant: Variant, size: Size, tone: Tone, className?: string) =>
  clsx(
    'inline-flex items-center justify-center gap-[5px] rounded-[var(--radius-md)] font-medium leading-none',
    'whitespace-nowrap select-none transition-[background,color,border-color,opacity] duration-80',
    'disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none',
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
        <Link {...(rest as ComponentProps<typeof Link>)} to={to} className={clsx(classes, 'no-underline')}>
          {content}
        </Link>
      )
    }
    if (href) {
      return (
        <a href={href} className={clsx(classes, 'no-underline')} {...(rest as AnchorHTMLAttributes<HTMLAnchorElement>)}>
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

/** Bouton icône seule — §33 `.btn-icon`. Taille par défaut 30×30 (sm = 26×26). */
export function IconButton({
  size = 'md',
  className,
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { size?: Size }) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center rounded-[var(--radius-md)] transition-colors duration-80',
        'disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none',
        'text-[var(--ink-faint)] hover:bg-[var(--surface-2)] hover:text-[var(--ink)]',
        size === 'sm' ? 'size-[26px] [&>svg]:size-3.5' : 'size-[30px] [&>svg]:size-[15px]',
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  )
}