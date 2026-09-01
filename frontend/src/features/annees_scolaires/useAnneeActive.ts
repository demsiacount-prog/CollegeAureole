import { useQuery } from '@tanstack/react-query'
import { fetchAnneesScolaires } from './api'

/** Année scolaire active (celle marquée active:true), ou null si aucune. */
export function useAnneeActive() {
  return useQuery({
    queryKey: ['anneesScolaires', 'active'],
    queryFn: async () => {
      const annees = await fetchAnneesScolaires()
      return annees.find((a) => a.active) ?? null
    },
    staleTime: 2 * 60_000,
  })
}
