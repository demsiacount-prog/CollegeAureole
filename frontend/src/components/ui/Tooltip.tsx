import { clsx } from 'clsx'
import { useLayoutEffect, useRef, useState, type ReactNode } from 'react'

interface TooltipProps {
  content?: string
  children: ReactNode
  /** Direction demandée. NB : si la bulle sortirait de la fenêtre
   *  (topbar collée en haut, tooltip en bas de page, boutons collés au
   *  bord droit — année, thème, cloche, avatar…), elle est
   *  automatiquement retournée **et replacée** pour rester lisible. */
  side?: 'top' | 'bottom'
  className?: string
}

const BUBBLE_GAP = 8
const BUBBLE_H_MARGIN = 8

/** Bulle de tooltip : texte en `--ink` sur fond `--surface` → contraste
 *  garanti dans les deux thèmes (`--ink` clair en sombre renversait le
 *  blanc ; `--surface` suit le thème). Contrairement à la valeur `#999`
 *  grise par défaut, le texte reprend l'encre du design system. */
export function Tooltip({ content, children, side = 'top', className }: TooltipProps) {
  const hostRef = useRef<HTMLSpanElement>(null)
  const bubbleRef = useRef<HTMLSpanElement>(null)
  const [placement, setPlacement] = useState<'top' | 'bottom'>(side)
  const [dx, setDx] = useState(0)

  useLayoutEffect(() => {
    const host = hostRef.current
    const bubble = bubbleRef.current
    if (!host || !bubble || !content) return

    const update = () => {
      const r = host.getBoundingClientRect()
      const h = bubble.offsetHeight
      const w = bubble.offsetWidth
      const fitsTop = r.top - h - BUBBLE_GAP >= 0
      const fitsBelow = r.bottom + h + BUBBLE_GAP <= window.innerHeight
      if (side === 'top' && !fitsTop) setPlacement('bottom')
      else if (side === 'bottom' && !fitsBelow) setPlacement('top')
      else setPlacement(side)

      /* Clamp horizontal : la bulle centrée sous un bouton collé au bord
       *  droit débordait de l'écran → on la décale pour rester dans la
       *  fenêtre (topbar : année, thème, cloche, avatar ; topbar aune droite…). */
      const targetX = r.left + r.width / 2
      const clampedX = Math.min(Math.max(targetX, BUBBLE_H_MARGIN + w / 2), window.innerWidth - BUBBLE_H_MARGIN - w / 2)
      setDx(clampedX - targetX)
    }

    update()
    const t = window.setTimeout(update, 0)
    window.addEventListener('resize', update)
    window.addEventListener('scroll', update, true)
    return () => {
      window.clearTimeout(t)
      window.removeEventListener('resize', update)
      window.removeEventListener('scroll', update, true)
    }
  }, [side, content])

  return (
    <span ref={hostRef} className={clsx('group/tooltip relative inline-flex', className)}>
      {children}
      {content ? (
        <span
          ref={bubbleRef}
          role="tooltip"
          className={clsx(
            'pointer-events-none absolute z-50 whitespace-nowrap rounded-[var(--radius-sm)] bg-[var(--surface-2)] px-2 py-1 text-[11px] leading-tight text-[var(--ink)] opacity-0 shadow-[var(--shadow-card)] transition-opacity duration-150 group-hover/tooltip:opacity-100',
            placement === 'top'
              ? 'bottom-full left-1/2 mb-1.5 -translate-x-1/2'
              : 'top-full left-1/2 mt-1.5 -translate-x-1/2',
          )}
          style={{ marginLeft: dx }}
        >
          {content}
        </span>
      ) : null}
    </span>
  )
}
