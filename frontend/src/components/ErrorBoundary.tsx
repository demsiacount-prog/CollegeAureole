import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertOctagon } from 'lucide-react'
import { Button } from '@/components/ui/Button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/**
 * Sans ceci, une erreur de rendu dans n'importe quelle page (donnée
 * inattendue du backend, accès à un champ manquant, etc.) fait disparaître
 * silencieusement tout l'arbre React — une page totalement blanche, sans
 * aucun indice pour l'utilisateur ni pour nous. Ce composant intercepte ces
 * erreurs et affiche le message réel à la place.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Erreur de rendu interceptée par ErrorBoundary :', error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-center">
          <AlertOctagon className="size-10 text-[var(--color-danger)]" strokeWidth={1.75} />
          <div>
            <h2 className="text-xl font-semibold text-[var(--color-ink)]">
              Une erreur est survenue
            </h2>
            <p className="mt-1.5 max-w-md text-sm text-[var(--color-ink-dim)]">
              Cette page n'a pas pu s'afficher correctement.
            </p>
            <p className="mt-3 max-w-md rounded-[var(--radius-sm)] border border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2 font-[var(--font-mono)] text-xs text-[var(--color-danger)]">
              {this.state.error.message}
            </p>
          </div>
          <Button variant="primary" onClick={() => window.location.reload()}>
            Recharger la page
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
