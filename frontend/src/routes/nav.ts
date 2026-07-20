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
  CalendarRange,
  ShieldCheck,
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

export const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Vue d’ensemble',
    items: [{ label: 'Tableau de bord', path: '/app', icon: LayoutDashboard, roles: ALL_ROLES }],
  },
  {
    title: 'Pédagogie',
    items: [
      { label: 'Élèves', path: '/app/eleves', icon: GraduationCap, roles: ALL_ROLES },
      { label: 'Enseignants', path: '/app/enseignants', icon: UserRound, roles: ALL_ROLES },
      { label: 'Tuteurs', path: '/app/tuteurs', icon: Users, roles: ALL_ROLES },
      { label: 'Classes', path: '/app/classes', icon: BookOpen, roles: ALL_ROLES },
      { label: 'Cours', path: '/app/cours', icon: NotebookPen, roles: ALL_ROLES },
      { label: 'Notes', path: '/app/notes', icon: FileText, roles: ALL_ROLES },
      { label: 'Bulletins', path: '/app/bulletins', icon: ClipboardList, roles: ALL_ROLES },
      { label: 'Résultats', path: '/app/resultats', icon: Award, roles: ALL_ROLES },
      { label: 'Absences', path: '/app/absences', icon: CalendarCheck, roles: ALL_ROLES },
      { label: 'Inscriptions', path: '/app/inscriptions', icon: UserPlus, roles: ALL_ROLES },
      { label: 'Séances', path: '/app/seances', icon: CalendarClock, roles: ALL_ROLES },
      { label: 'Salles', path: '/app/salles', icon: DoorOpen, roles: ALL_ROLES },
    ],
  },
  {
    title: 'Finances',
    items: [
      { label: 'Paiements', path: '/app/paiements', icon: Wallet, roles: ALL_ROLES },
      { label: 'Dépenses', path: '/app/depenses', icon: Receipt, roles: ALL_ROLES },
    ],
  },
  {
    title: 'Administration',
    items: [
      { label: 'Années scolaires', path: '/app/annees-scolaires', icon: CalendarRange, roles: ['admin', 'directeur'] },
      { label: 'Comptes', path: '/app/utilisateurs', icon: ShieldCheck, roles: ['admin'] },
    ],
  },
]
