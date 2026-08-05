import type { LucideIcon } from 'lucide-react'
import {
  ClipboardList,
  FileText,
  GraduationCap,
  LayoutDashboard,
  Receipt,
  Settings,
  UserPlus,
  Wallet,
} from 'lucide-react'

export interface DemoDetail {
  description: string
  icon: LucideIcon
}

export const DEMO_DETAILS: Record<string, DemoDetail> = {
  '/app': {
    icon: LayoutDashboard,
    description:
      'Tous les indicateurs clés de l’établissement : effectifs, encaissements, absences et tendances, en un coup d’œil.',
  },
  '/app/eleves': {
    icon: GraduationCap,
    description:
      'L’annuaire des élèves avec recherche instantanée et fiche détaillée : photo, tuteur, classe et historique.',
  },
  '/app/enseignants': {
    icon: FileText,
    description: 'Le corps enseignant : coordonnées, affectations aux cours et charges hebdomadaires.',
  },
  '/app/tuteurs': {
    icon: UserPlus,
    description: 'Les tuteurs des élèves et leurs coordonnées, rattachés à chaque dossier.',
  },
  '/app/classes': {
    icon: GraduationCap,
    description: 'Les classes de l’établissement et leur affectation des matières.',
  },
  '/app/salles': {
    icon: ClipboardList,
    description: 'Le parc de salles, avec capacités et affectation aux emplois du temps.',
  },
  '/app/inscriptions': {
    icon: UserPlus,
    description: 'Inscrivez chaque élève à l’année scolaire en cours et suivez les statuts en temps réel.',
  },
  '/app/absences': {
    icon: FileText,
    description:
      'Enregistrez et justifiez les absences, filtrez par élève ou par cours, et gardez le motif de chaque justification.',
  },
  '/app/notes': {
    icon: ClipboardList,
    description: 'La saisie des notes se fait par classe, cours et trimestre, prête pour les bulletins.',
  },
  '/app/bulletins': {
    icon: FileText,
    description:
      'Générez automatiquement les bulletins : moyennes, rangs et appréciations pour chaque période.',
  },
  '/app/resultats': {
    icon: ClipboardList,
    description: 'Les résultats consolidés par classe et par période, avec les rangs.',
  },
  '/app/cours': {
    icon: FileText,
    description: 'Le catalogue des matières, leurs coefficients et les enseignants responsables.',
  },
  '/app/seances': {
    icon: ClipboardList,
    description: 'L’emploi du temps des classes, avec créneaux, salles et enseignants.',
  },
  '/app/paiements': {
    icon: Wallet,
    description:
      'Encaissements des scolarités, émission des reçus et suivi de chaque compte élève.',
  },
  '/app/depenses': {
    icon: Receipt,
    description: 'Suivez les dépenses de l’établissement et la trésorerie globale.',
  },
  '/app/cloture-annee': {
    icon: Settings,
    description: 'Clôturez l’année scolaire et préparez la suivante en toute sécurité.',
  },
  '/app/parametres': {
    icon: Settings,
    description:
      'Réglages généraux de l’établissement : informations, année scolaire, sauvegardes et sécurité.',
  },
}
