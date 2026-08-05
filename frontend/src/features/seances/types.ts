export type JourSemaine = 'Lundi' | 'Mardi' | 'Mercredi' | 'Jeudi' | 'Vendredi' | 'Samedi'

export interface Seance {
  id: number
  id_cours: number
  id_classe: number
  id_annee_scolaire: number
  id_salle: number | null
  jour_semaine: JourSemaine
  heure_debut: string
  heure_fin: string
  created_at: string
  updated_at: string
}

export interface SeanceDetail extends Seance {
  cours: {
    id: number
    nom: string
    description: string
    volume_horaire: number
    enseignant: { matricule: string; nom: string; prenom: string } | null
  } | null
  classe: { id: number; niveau: string; nom: string } | null
  salle: { id: number; nom: string; capacite: number | null } | null
}

export interface SeanceCreateInput {
  id_cours: number
  id_classe: number
  id_annee_scolaire: number
  id_salle?: number | null
  jour_semaine: JourSemaine
  heure_debut: string
  heure_fin: string
}
