import {
  LayoutDashboard,
  GraduationCap,
  Users,
  Building2,
  ClipboardList,
  HeartHandshake,
  BookOpen,
  Pencil,
  FileText,
  Trophy,
  CalendarDays,
  UserX,
  CreditCard,
  PieChart,
  Settings,
  DoorOpen,
  FolderOpen,
  FlagTriangleRight,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  id: string
  label: string
  path: string
  icon: LucideIcon
  /** Réservé aux administrateurs (masqué pour les autres rôles). */
  adminOnly?: boolean
}

export interface NavSection {
  /** Label de groupe affiché dans la sidebar. null = item standalone (pas de label). */
  title: string | null
  /** Token CSS de couleur module (var(--mod-*)). null → aucune identité de module. */
  moduleColor?: string | null
  items: NavItem[]
}

/** Module identity colors (v4.1) */
export const MOD_COLORS = {
  vie: 'var(--mod-vie)',
  peda: 'var(--mod-ped)',
  ress: 'var(--mod-res)',
  fin: 'var(--mod-fin)',
} as const

/** Design system §31 — Architecture de navigation : 5 groupes + item standalone. */
export const NAV_SECTIONS: NavSection[] = [
  {
    title: null,
    moduleColor: null,
    items: [{ id: 'tableau-de-bord', label: 'Tableau de bord', path: '/app', icon: LayoutDashboard }],
  },
  {
    title: 'Élèves & Classes',
    moduleColor: MOD_COLORS.peda,
    items: [
      { id: 'eleves', label: 'Élèves', path: '/app/eleves', icon: Users },
      { id: 'classes', label: 'Classes', path: '/app/classes', icon: Building2 },
      { id: 'inscriptions', label: 'Inscriptions', path: '/app/inscriptions', icon: ClipboardList },
      { id: 'tuteurs', label: 'Tuteurs', path: '/app/tuteurs', icon: HeartHandshake },
    ],
  },
  {
    title: 'Pédagogie',
    moduleColor: MOD_COLORS.peda,
    items: [
      { id: 'enseignants', label: 'Enseignants', path: '/app/enseignants', icon: GraduationCap },
      { id: 'cours', label: 'Cours', path: '/app/cours', icon: BookOpen },
      { id: 'notes', label: 'Notes', path: '/app/notes', icon: Pencil },
      { id: 'bulletins', label: 'Bulletins', path: '/app/bulletins', icon: FileText },
      { id: 'resultats', label: 'Résultats', path: '/app/resultats', icon: Trophy },
    ],
  },
  {
    title: 'Vie scolaire',
    moduleColor: MOD_COLORS.vie,
    items: [
      { id: 'seances', label: 'Séances', path: '/app/seances', icon: CalendarDays },
      { id: 'absences', label: 'Absences', path: '/app/absences', icon: UserX },
    ],
  },
  {
    title: 'Finances',
    moduleColor: MOD_COLORS.fin,
    items: [
      { id: 'paiements', label: 'Paiements', path: '/app/paiements', icon: CreditCard },
      { id: 'depenses', label: 'Dépenses', path: '/app/depenses', icon: PieChart },
    ],
  },
  {
    title: 'Administration',
    moduleColor: null,
    items: [
      { id: 'salles', label: 'Salles', path: '/app/salles', icon: DoorOpen },
      { id: 'documents', label: 'Documents administratifs', path: '/app/documents', icon: FolderOpen },
      { id: 'cloture', label: 'Clôture d\'année', path: '/app/cloture-annee', icon: FlagTriangleRight, adminOnly: true },
      { id: 'parametres', label: 'Paramètres', path: '/app/parametres', icon: Settings, adminOnly: true },
    ],
  },
]

export interface ModuleInfo {
  title: string
  moduleColor: string | null
}

/** Retrouve le module (titre + couleur) d'un chemin donné, en remontant les
 *  segments pour matcher les pages de détail (ex: /app/eleves/MAT). */
export function moduleForPath(path: string): ModuleInfo | null {
  for (const section of NAV_SECTIONS) {
    const flatTitle = section.title ?? section.items[0]?.label
    for (const item of section.items) {
      if (path === item.path || path.startsWith(`${item.path}/`)) {
        return { title: flatTitle ?? '', moduleColor: section.moduleColor ?? null }
      }
    }
  }
  return null
}

/** Vrai pour le rôle ADMIN (comparaison insensible à la casse). */
export function isAdmin(role?: string | null): boolean {
  return role?.toUpperCase() === 'ADMIN'
}

/** Navigation filtrée par rôle : les items `adminOnly` sont masqués pour un
 *  utilisateur non administrateur. Les sections vides sont retirées. */
export function navSectionsForRole(role?: string | null): NavSection[] {
  const admin = isAdmin(role)
  return NAV_SECTIONS.map((s) => ({
    ...s,
    items: s.items.filter((i) => admin || !i.adminOnly),
  })).filter((s) => s.items.length > 0)
}

/** Flat list des items (pour la Command Palette §40), filtrée par rôle. */
export function allNavItems(role?: string | null): NavItem[] {
  return navSectionsForRole(role).flatMap((s) => s.items)
}