import { useLocation } from 'react-router-dom'
import { moduleForPath, type ModuleInfo } from './nav'

/** Retrouve le module actif (titre + couleur) à partir de la route courante. */
export function useCurrentModule(): ModuleInfo | null {
  const { pathname } = useLocation()
  return moduleForPath(pathname)
}
