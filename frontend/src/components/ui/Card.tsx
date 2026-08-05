import type { HTMLAttributes } from 'react'
import { clsx } from 'clsx'

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        'rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)]',
        className,
      )}
      {...rest}
    />
  )
}

export function CardHeader({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('flex items-center justify-between gap-3 p-4', className)} {...rest} />
}

export function CardTitle({ className, ...rest }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={clsx('text-[15px] font-medium tracking-tight text-[var(--color-ink)]', className)}
      {...rest}
    />
  )
}

export function CardBody({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={clsx('p-4 pt-0', className)} {...rest} />
}
