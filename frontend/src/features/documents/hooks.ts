import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import type { DocumentCategorieKey, EntiteDocument } from './types'
import {
  documentsQueryKey,
  fetchDocumentsByEntite,
  modifierDocument,
  uploadDocumentGenerique,
} from './api'

/** Liste des documents d'une entité (cache partagé avec l'onglet Documents). */
export function useDocuments(entiteType: EntiteDocument, entiteId: string) {
  return useQuery({
    queryKey: documentsQueryKey(entiteType, entiteId),
    queryFn: () => fetchDocumentsByEntite(entiteType, entiteId),
    enabled: !!entiteId,
  })
}

export interface NouveauDocumentEnvoyable {
  fichier: File
  nom?: string
  categorie?: DocumentCategorieKey
}

export function useUploadDocument(entiteType: EntiteDocument, entiteId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (params: NouveauDocumentEnvoyable) =>
      uploadDocumentGenerique({ entiteType, entiteId, ...params }),
    onSuccess: () => qc.invalidateQueries({ queryKey: documentsQueryKey(entiteType, entiteId) }),
  })
}

export function useModifierDocument(entiteType: EntiteDocument, entiteId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (vars: { id: number; data: { nom?: string; categorie?: DocumentCategorieKey } }) =>
      modifierDocument(vars.id, vars.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: documentsQueryKey(entiteType, entiteId) }),
  })
}