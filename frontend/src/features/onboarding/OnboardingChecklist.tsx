import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { useAuth } from '@/auth/useAuth'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { MOD_COLORS } from '@/routes/nav'
import { fetchCours } from '@/features/cours/api'
import { fetchSeances } from '@/features/seances/api'
import { fetchPaiements } from '@/features/paiements/api'
import { toast } from '@/components/ui/toast'

/** Design system Type J — Premier Tableau de Bord.
 *  Bandeau de bienvenue + checklist de mise en route (6 tâches). Affiché
 *  uniquement au tout début de vie de l'instance : il se masque définitivement
 *  si l'utilisateur ferme le bandeau ou si les 6 tâches sont complétées.
 *  État persisté en localStorage. */

const STORAGE_KEY = 'aureole_onboarding'

interface OnboardingState {
  banniereFermee: boolean
  toastEnvoye: boolean
}

interface Tache {
  id: string
  label: string
  description: string
  moduleColor: string
  href: string
}

function lireEtat(): OnboardingState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { banniereFermee: false, toastEnvoye: false, ...JSON.parse(raw) }
  } catch {
    /* localStorage indisponible : on repart de zéro. */
  }
  return { banniereFermee: false, toastEnvoye: false }
}

function ecrireEtat(patch: Partial<OnboardingState>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...lireEtat(), ...patch }))
  } catch {
    /* silencieux */
  }
}

interface OnboardingChecklistProps {
  /** Counts réels déjà chargés par le dashboard Type A. */
  compteurs: { nb_eleves: number; nb_enseignants: number; nb_classes: number }
}

export function OnboardingChecklist({ compteurs }: OnboardingChecklistProps) {
  const { user } = useAuth()
  const etat = useMemo(lireEtat, [])

  const { data: cours, isLoading: chargCours } = useQuery({ queryKey: ['cours'], queryFn: fetchCours, staleTime: 60_000 })
  const { data: seances, isLoading: chargSeances } = useQuery({ queryKey: ['seances'], queryFn: () => fetchSeances(), staleTime: 60_000 })
  const { data: paiements } = useQuery({
    queryKey: ['onboarding-paiements'],
    queryFn: () => fetchPaiements({ skip: 0, limit: 1 }),
    staleTime: 60_000,
  })

  const fait: Record<string, boolean> = {
    eleves: compteurs.nb_eleves > 0,
    classes: compteurs.nb_classes > 0,
    enseignants: compteurs.nb_enseignants > 0,
    cours: (cours?.length ?? 0) > 0,
    edt: (seances?.length ?? 0) > 0,
    paiement: (paiements?.length ?? 0) > 0,
  }

  const taches: Tache[] = [
    { id: 'eleves', label: 'Ajouter le premier élève', description: 'Créez la fiche du premier élève', moduleColor: MOD_COLORS.vie, href: '/app/eleves' },
    { id: 'classes', label: 'Créer les classes', description: 'Définissez les classes et niveaux', moduleColor: MOD_COLORS.vie, href: '/app/classes' },
    { id: 'enseignants', label: 'Ajouter les enseignants', description: 'Créez la fiche des enseignants', moduleColor: MOD_COLORS.ress, href: '/app/enseignants' },
    { id: 'cours', label: 'Créer les cours', description: 'Attribuez les enseignements', moduleColor: MOD_COLORS.peda, href: '/app/cours' },
    { id: 'edt', label: "Configurer l'emploi du temps", description: 'Planifiez les séances', moduleColor: MOD_COLORS.ress, href: '/app/seances' },
    { id: 'paiement', label: 'Enregistrer un paiement', description: 'Saisissez votre premier paiement', moduleColor: MOD_COLORS.fin, href: '/app/paiements' },
  ]

  const completees = taches.filter((t) => fait[t.id]).length
  const toutFait = completees === taches.length
  const chargement = chargCours || chargSeances
  const masque = etat.banniereFermee || toutFait

  // Toast de bienvenue unique (design system Type J, auto-dismiss 6 s).
  useMemo(() => {
    if (!etat.toastEnvoye && user && !masque) {
      ecrireEtat({ toastEnvoye: true })
      toast('Instance créée avec succès — Vous êtes connecté en tant qu’administrateur.', 'success', { duration: 6000 })
    }
  }, [etat.toastEnvoye, user, masque])

  if (!user || masque) return null

  return (
    <div className="flex flex-col gap-6">
      {/* Bandeau de bienvenue */}
      <div
        className="relative flex items-start gap-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-5 sm:items-center"
        style={{ borderTop: '2px solid var(--color-halo)' }}
      >
        <span className="halo-ring flex size-10 shrink-0 items-center justify-center rounded-full">
          <CheckCircle2 className="size-5 text-[var(--color-halo)]" strokeWidth={1.75} />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="font-[var(--font-display)] text-[22px] font-semibold leading-tight text-[var(--color-ink)]">
            Auréole est prêt !
          </h2>
          <p className="mt-0.5 text-sm text-[var(--color-ink-dim)]">
            Votre instance est configurée. Commencez par ajouter vos premiers élèves ou configurez l’emploi du temps.
          </p>
        </div>
        <button
          type="button"
          onClick={() => ecrireEtat({ banniereFermee: true })}
          className="shrink-0 rounded-md p-1.5 text-[var(--color-ink-faint)] transition-colors hover:bg-[var(--color-surface-2)] hover:text-[var(--color-ink)]"
          aria-label="Fermer le bandeau de bienvenue"
        >
          <X className="size-4" strokeWidth={2} />
        </button>
      </div>

      {/* Checklist de mise en route */}
      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h3 className="text-[15px] font-semibold text-[var(--color-ink)]">Par où commencer ?</h3>
          <div className="flex items-center gap-3">
            <p className="font-[var(--font-mono)] text-xs text-[var(--color-ink-faint)]">
              {completees} / {taches.length} tâches complétées
            </p>
            <div className="w-36">
              <ProgressBar variant="wizard" value={(completees / taches.length) * 100} />
            </div>
          </div>
        </div>

        {chargement ? (
          <p className="text-sm text-[var(--color-ink-faint)]">Vérification des tâches…</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {taches.map((tache) => {
              const done = fait[tache.id]
              return (
                <Link
                  key={tache.id}
                  to={tache.href}
                  className={clsx(
                    'flex h-28 flex-col justify-between rounded-lg border p-4 transition-colors',
                    done
                      ? 'border-[var(--color-border)] bg-[var(--color-surface)] opacity-60'
                      : 'border-[var(--color-border)] bg-[var(--color-surface)] hover:border-[var(--color-halo)]',
                  )}
                >
                  <div>
                    <p className="flex items-center gap-2 text-sm font-semibold text-[var(--color-ink)]">
                      <span className="size-2 shrink-0 rounded-full" style={{ background: tache.moduleColor }} />
                      <span className={clsx(done && 'line-through text-[var(--color-ink-faint)]')}>{tache.label}</span>
                      {done && <CheckCircle2 className="ml-auto size-4 shrink-0 text-[var(--color-success)]" strokeWidth={2} />}
                    </p>
                    <p className="mt-1 text-[13px] leading-snug text-[var(--color-ink-dim)]">{tache.description}</p>
                  </div>
                  <p className="mt-2 text-[13px] font-medium text-[var(--color-action)]">
                    {done ? 'Terminée' : 'Commencer →'}
                  </p>
                </Link>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}