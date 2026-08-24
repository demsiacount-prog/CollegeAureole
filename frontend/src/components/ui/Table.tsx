import type { HTMLAttributes, TdHTMLAttributes, ThHTMLAttributes } from 'react'
import { clsx } from 'clsx'

/**
 * Composants de tableau partagés — source de vérité du rendu des tableaux
 * (design system §06). Chaque page doit les utiliser au lieu de recopier du
 * `<table>`/`<th>`/`<td>` : en-tête sur fond `surface-2`, lignes séparées par
 * `border-soft`, densité 40px (`py-2.5`), survol de ligne.
 *
 * Les classes utilitaires des pages (alignement, largeur, couleurs de texte)
 * se passent en `className` et fusionnent avec les valeurs par défaut.
 */

export function TableContainer({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={clsx(
        'overflow-x-auto rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)]',
        className,
      )}
      {...rest}
    />
  )
}

export function Table({ className, ...rest }: HTMLAttributes<HTMLTableElement>) {
  return <table className={clsx('w-full text-sm', className)} {...rest} />
}

export function TableHeader({ className, ...rest }: HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={clsx('border-b border-[var(--color-border)] bg-[var(--color-surface-2)]', className)}
      {...rest}
    />
  )
}

export function TableBody({ className, ...rest }: HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={clsx('divide-y divide-[var(--color-border-soft)]', className)} {...rest} />
}

export function TableRow({ className, ...rest }: HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={clsx('transition-colors hover:bg-[var(--color-surface-2)]', className)} {...rest} />
}

export function TableHead({ className, ...rest }: ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th
      className={clsx('px-5 py-2.5 text-left font-medium text-[var(--color-ink-dim)]', className)}
      {...rest}
    />
  )
}

export function TableCell({ className, ...rest }: TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={clsx('px-5 py-2.5', className)} {...rest} />
}
