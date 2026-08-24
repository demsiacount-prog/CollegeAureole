export const ELEVE_DOCS_LABELS: Record<string, string> = {
  acte_naissance: 'Acte de naissance',
  carnet_sante: "Carnet de santé",
}

export const ENSEIGNANT_DOCS_LABELS: Record<string, string> = {
  piece_identite: "Pièce d'identité",
  cv: 'Curriculum vitae',
  diplome: 'Diplômes',
  casier: 'Casier judiciaire',
}

export const TUTEUR_DOCS_LABELS: Record<string, string> = {
  piece_identite: "Pièce d'identité",
  justificatif_domicile: 'Justificatif de domicile',
  acte_naissance: 'Acte de naissance',
  jugement_tutelle: 'Jugement de tutelle',
}

export function countVisibleDocuments(
  documents: readonly { type_document: string }[],
  labels: Record<string, string>,
): number {
  return documents.filter((d) => labels[d.type_document] !== undefined).length
}
