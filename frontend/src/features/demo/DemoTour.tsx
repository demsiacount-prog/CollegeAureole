import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Sparkles, X } from 'lucide-react'
import { clsx } from 'clsx'
import { subscribeDemo, startDemo, stopDemo, shouldStartDemo, markDemoCompleted } from './demoStore'
import { DEMO_DETAILS } from './demoSteps'
import { NAV_SECTIONS } from '@/routes/nav'
import { useAuth } from '@/auth/useAuth'
import { Button } from '@/components/ui/Button'

const AUTO_DELAY = 6000

function clearHighlights() {
  document.querySelectorAll('nav a').forEach((a) => a.classList.remove('demo-highlight'))
}

function highlightSidebar(path: string) {
  clearHighlights()
  const el = document.querySelector(`nav a[href="${path}"]`)
  if (el instanceof HTMLElement) {
    el.classList.add('demo-highlight')
    el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
  }
}

export function DemoTour() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [index, setIndex] = useState(0)
  const navigate = useNavigate()
  const location = useLocation()

  const steps = useMemo(() => {
    if (!user) return []
    return NAV_SECTIONS.flatMap((section) => section.items)
      .filter((item) => item.roles.includes(user.role))
      .map((item) => ({
        path: item.path,
        label: item.label,
        icon: item.icon,
        description:
          DEMO_DETAILS[item.path]?.description ??
          `Découvrez la gestion des ${item.label.toLowerCase()}.`,
      }))
  }, [user])

  useEffect(() => {
    const unsubscribe = subscribeDemo(setOpen)
    return () => {
      unsubscribe()
      stopDemo()
    }
  }, [])

  useEffect(() => {
    let mounted = true
    const maybeStart = async () => {
      if (!mounted || !user) return
      if (await shouldStartDemo()) {
        startDemo()
      }
    }
    maybeStart()
    return () => {
      mounted = false
    }
  }, [user])

  useEffect(() => {
    if (!open || steps.length === 0) {
      clearHighlights()
      return
    }
    if (index >= steps.length) {
      setIndex(0)
      return
    }
    const step = steps[index]
    if (location.pathname === step.path) highlightSidebar(step.path)
    else navigate(step.path)
  }, [open, index, steps, location.pathname, navigate])

  useEffect(() => {
    if (!open || index >= steps.length - 1) return
    const timer = setTimeout(() => setIndex((i) => i + 1), AUTO_DELAY)
    return () => clearTimeout(timer)
  }, [open, index, steps.length])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') finish()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, index, steps.length])

  if (!open || steps.length === 0) return null

  const step = steps[index]
  const isLast = index === steps.length - 1

  function finish() {
    stopDemo()
    void markDemoCompleted()
  }

  return (
    <div className="fixed inset-0 z-50 bg-[var(--color-base)]/30">
      <div className="absolute inset-x-4 bottom-6 mx-auto w-full max-w-lg rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 shadow-[var(--shadow-soft)]">
        <div className="mb-3 flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-brand-wash)] text-[var(--color-brand)]">
              <step.icon className="size-5" strokeWidth={1.75} />
            </span>
            <div>
              <p className="font-[var(--font-mono)] text-[11px] uppercase tracking-wider text-[var(--color-brand-dim)]">
                Tutoriel de l’application · {index + 1} / {steps.length}
              </p>
              <h3 className="text-lg font-semibold leading-tight text-[var(--color-ink)]">
                {step.label}
              </h3>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={finish}
            aria-label="Fermer le tutoriel"
          >
            <X className="size-4" />
          </Button>
        </div>

        <p className="text-sm leading-relaxed text-[var(--color-ink-dim)]">{step.description}</p>

        <div className="mt-4 flex items-center gap-1.5">
          {steps.map((s, i) => (
            <span
              key={s.path}
              className={clsx(
                'h-1 rounded-full transition-all duration-300',
                i === index ? 'w-6 bg-[var(--color-brand)]' : 'w-1.5 bg-[var(--color-border)]',
              )}
            />
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between border-t border-[var(--color-border-soft)] pt-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={finish}
          >
            <Sparkles className="size-3.5" strokeWidth={1.75} />
            Passer le tutoriel
          </Button>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={index === 0}
              onClick={() => setIndex((i) => i - 1)}
            >
              <ChevronLeft className="size-3.5" strokeWidth={1.75} />
              Précédent
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={isLast ? finish : () => setIndex((i) => i + 1)}
            >
              {isLast ? 'Terminer' : 'Suivant'}
              {!isLast && <ChevronRight className="size-3.5" strokeWidth={1.75} />}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
