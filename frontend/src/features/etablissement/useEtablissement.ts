import { useQuery } from '@tanstack/react-query'
import { fetchEtablissement } from './api'

export function useEtablissement() {
  return useQuery({
    queryKey: ['etablissement'],
    queryFn: fetchEtablissement,
    staleTime: 5 * 60_000,
    retry: false,
  })
}
