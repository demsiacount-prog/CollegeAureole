import type { Role } from '@/types'
import {
  LayoutDashboard,
  GraduationCap,
  UserRound,
  Users,
  BookOpen,
  NotebookPen,
  FileText,
  ClipboardList,
  Award,
  CalendarCheck,
  UserPlus,
  CalendarClock,
  DoorOpen,
  Wallet,
  Receipt,
  Settings,
  FlagTriangleRight,
  type LucideIcon,
} from 'lucide-react'

export interface NavItem {
  label: string
  path: string
  icon: LucideIcon
  roles: Role[]
}

export interface NavSection {
  title: string
  items: NavItem[]
}

const ALL_ROLES: Role[] = ['admin', 'directeur', 'comptable']
const DIRECTION: Role[] = ['admin', 'directeur']

export const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Vue d’ensemble',
    items: [{ label: 'Tableau de bord', path: '/app', icon: LayoutDashboard, roles: ALL_ROLES }],
  },
  {
    title: 'Pilotage',
    items: [
      { label: 'Élèves', path: '/app/eleves', icon: GraduationCap, roles: ALL_ROLES },
      { label: 'Enseignants', path: '/app/enseignants', icon: UserRound, roles: ALL_ROLES },
      { label: 'Tuteurs', path: '/app/tuteurs', icon: Users, roles: ALL_ROLES },
      { label: 'Classes', path: '/app/classes', icon: BookOpen, roles: ALL_ROLES },
      { label: 'Salles', path: '/app/salles', icon: DoorOpen, roles: ALL_ROLES },
    ],
  },
  {
    title: 'Pédagogie',
    items: [
      { label: 'Inscriptions', path: '/app/inscriptions', icon: UserPlus, roles: DIRECTION },
      { label: 'Absences', path: '/app/absences', icon: CalendarCheck, roles: DIRECTION },
      { label: 'Notes', path: '/app/notes', icon: FileText, roles: DIRECTION },
      { label: 'Bulletins', path: '/app/bulletins', icon: ClipboardList, roles: DIRECTION },
      { label: 'Résultats', path: '/app/resultats', icon: Award, roles: DIRECTION },
      { label: 'Cours', path: '/app/cours', icon: NotebookPen, roles: DIRECTION },
      { label: 'Emploi du temps', path: '/app/seances', icon: CalendarClock, roles: DIRECTION },
    ],
  },
  {
    title: 'Finances',
    items: [
      { label: 'Paiements', path: '/app/paiements', icon: Wallet, roles: ['admin', 'comptable'] },
      { label: 'Dépenses', path: '/app/depenses', icon: Receipt, roles: ['admin', 'comptable'] },
    ],
  },
  {
    title: 'Administration',
    items: [
      { label: 'Clôture d’année', path: '/app/cloture-annee', icon: FlagTriangleRight, roles: DIRECTION },
      { label: 'Paramètres', path: '/app/parametres', icon: Settings, roles: ['admin', 'directeur'] },
    ],
  },
]
