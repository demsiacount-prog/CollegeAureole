# Auréole — Système de Design v6.0

> **v6.0** introduit la couche structurelle complète : shell applicatif, navigation groupée, topbar contextuelle, et les patterns de page unifiés (liste, dashboard, dossier). Tout le contenu v5.0 est maintenu sans modification sauf mention `[mis à jour v6.0]`.
>
> Ce document est le référentiel principal pour l'agent Codex. Chaque section est suffisamment précise pour être implémentée directement sans interprétation.

---

## Table des matières

| Section | Titre | Statut |
|---|---|---|
| §00–§27 | Contenu v5.0 | Inchangé |
| **§28** | **Shell Applicatif** | **NEW v6.0** |
| **§29** | **Sidebar Navigation** | **NEW v6.0** |
| **§30** | **TopBar Contextuelle** | **NEW v6.0** |
| **§31** | **Architecture de Navigation** | **NEW v6.0** |
| **§32** | **Pattern Universel de Page** | **NEW v6.0** |
| **Type A v2** | **Page Liste (refonte)** | **mis à jour v6.0** |
| **Type J v2** | **Dashboard (refonte)** | **mis à jour v6.0** |
| **Type C v2** | **Page Dossier (refonte)** | **mis à jour v6.0** |
| **§33** | **Boutons & Actions** | **NEW v6.0** |
| **§34** | **Composants de Formulaire** | **NEW v6.0** |
| **§35** | **Drawer (Panneau Latéral)** | **NEW v6.0** |
| **§36** | **Modal de Confirmation** | **NEW v6.0** |
| **§37** | **Toasts & Notifications** | **NEW v6.0** |
| **§38** | **États Vides (Empty States)** | **NEW v6.0** |
| **§39** | **Skeletons (Chargement)** | **NEW v6.0** |
| **§40** | **Command Palette (Ctrl+K)** | **NEW v6.0** |
| **Type B v2** | **Formulaires via Drawer** | **NEW v6.0** |
| **Type D** | **Saisie de Notes** | **NEW v6.0** |
| **§41** | **Implémentation module par module** | **NEW v6.0** |
| **§42** | **Raccourcis Clavier** | **NEW v6.0** |
| **§43** | **Référentiel Complet des Tokens CSS** | **NEW v6.0** |
| **§44** | **Structure de fichiers Frontend** | **NEW v6.0** |
| **§45** | **Checklist d'implémentation** | **NEW v6.0** |

---

## Contexte v6.0 — Structure desktop

L'application Auréole est packagée via **Tauri** pour desktop Windows. La résolution cible est **1280 × 800 px minimum**, avec affichage optimal à **1440 × 900 px**. Toute l'interface est orientée usage à la souris avec support clavier complet.

Le shell applicatif est une **mise en page fixe** : sidebar + topbar + zone de contenu. Il ne scrolle jamais en entier — seule la zone de contenu principale scrolle verticalement.

---

## §28 · Shell Applicatif `NEW v6.0`

### Anatomie globale

```
┌──────────────────────────────────────────────────────────────┐
│ Sidebar (218px)  │  TopBar (52px height, flex-1 width)       │
│                  │──────────────────────────────────────────  │
│                  │                                            │
│                  │  Zone de Contenu (flex-1, scroll-y)        │
│                  │                                            │
│                  │                                            │
└──────────────────────────────────────────────────────────────┘
```

### Tokens de layout

```css
--shell-sidebar-w:     218px;   /* largeur sidebar déployée */
--shell-sidebar-col-w: 52px;    /* largeur sidebar réduite (icônes) */
--shell-topbar-h:      52px;    /* hauteur fixe de la topbar */
--shell-content-pad-x: 20px;    /* padding horizontal standard du contenu */
--shell-content-pad-y: 18px;    /* padding vertical haut du header de page */
```

### Structure HTML/JSX

```tsx
<div className="app-shell">           {/* display:flex; height:100vh; overflow:hidden */}
  <Sidebar />                          {/* width:218px → 52px; flex-shrink:0 */}
  <div className="app-main">          {/* display:flex; flex-direction:column; flex:1; min-width:0 */}
    <TopBar />                         {/* height:52px; flex-shrink:0 */}
    <main className="app-content">    {/* flex:1; overflow-y:auto; background:var(--base) */}
      {children}
    </main>
  </div>
</div>
```

### Règles CSS du shell

```css
.app-shell {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--base);
}

.app-main {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.app-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--base);
  scrollbar-width: thin;
  scrollbar-color: var(--surface-3) transparent;
}

.app-content::-webkit-scrollbar { width: 4px; }
.app-content::-webkit-scrollbar-track { background: transparent; }
.app-content::-webkit-scrollbar-thumb { background: var(--surface-3); border-radius: 4px; }
```

---

## §29 · Sidebar Navigation `NEW v6.0`

### Dimensions & comportement

| Propriété | Valeur |
|---|---|
| Largeur déployée | 218px |
| Largeur réduite | 52px |
| Fond | `--surface` |
| Bordure droite | 1px `--border` |
| Transition | `width 180ms ease`, `min-width 180ms ease` |
| Z-index | 10 |

### Zones de la sidebar

```
┌─────────────────────────────────────────┐
│ Header (52px)  — logo + nom + bouton ←  │  ← border-bottom 1px --border
│─────────────────────────────────────────│
│                                         │
│ Navigation (flex:1, overflow-y:auto)    │
│  • Groupes + items                      │
│                                         │
│─────────────────────────────────────────│
│ Footer (auto)  — avatar + info user     │  ← border-top 1px --border
└─────────────────────────────────────────┘
```

### Header de la sidebar

```
[ Logo mark 26×26 ] [ "Auréole" Fraunces 14.5px ] [ ← collapse ]
```

| Élément | Spec |
|---|---|
| Container | `height: 52px` · `padding: 0 12px` · `display:flex; align-items:center; gap:9px` |
| Logo mark | 26×26px · `border-radius: --radius-md` · fond `--halo` · Fraunces 14px `--halo-ink` |
| Nom "Auréole" | Fraunces 14.5px · `--ink` · `font-weight:600` · `flex:1` |
| Bouton collapse | 22×22px · Ghost icon · icône `ChevronLeft` (Lucide) · tourne à 180° en mode réduit |

**Mode réduit** : `.logo-name { opacity: 0; pointer-events: none }` — le logo mark reste visible.

### Item de navigation

```css
.nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
  height: 34px;
  margin: 1px 6px;
  border-radius: var(--radius-md);
  color: var(--ink-dim);
  cursor: pointer;
  transition: background 80ms, color 80ms;
  white-space: nowrap;
  overflow: hidden;
  position: relative;
  user-select: none;
}

/* Hover */
.nav-item:hover {
  background: var(--surface-2);
  color: var(--ink);
}

/* Actif */
.nav-item.active {
  background: var(--halo-wash);   /* rgba(217,167,92,.12) */
  color: var(--halo);
}

/* Barre verticale gauche sur item actif */
.nav-item.active::before {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 2px;
  height: 14px;
  background: var(--halo);
  border-radius: 0 2px 2px 0;
}

/* Icône */
.nav-item .nav-icon {
  font-size: 15px;
  flex-shrink: 0;
  width: 18px;
  text-align: center;
  color: inherit;
}

/* Label */
.nav-item .nav-label {
  font-size: 13px;
  transition: opacity 150ms;
}

/* Mode réduit : masquer les labels */
.sidebar.collapsed .nav-label  { opacity: 0; }
.sidebar.collapsed .nav-section { opacity: 0; }
.sidebar.collapsed .user-info  { opacity: 0; }
.sidebar.collapsed .nav-badge  { opacity: 0; }
```

### Label de section

```css
.nav-section {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  padding: 14px 14px 3px;
  text-transform: uppercase;
  white-space: nowrap;
  transition: opacity 150ms;
}
```

### Badge numérique (alerte)

```css
.nav-badge {
  margin-left: auto;
  background: var(--danger);
  color: #fff;
  font-size: 9px;
  font-weight: 600;
  padding: 1px 5px;
  border-radius: 8px;
  transition: opacity 150ms;
  line-height: 1.4;
}
```

Usage : visible sur "Absences" quand il y a des absences non justifiées en attente.

### Footer de la sidebar

```
[ Avatar 26px ] [ Nom (12px 500) ]
                [ Rôle (10.5px --ink-faint) ]
```

```css
.sidebar-footer {
  padding: 8px 10px;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  overflow: hidden;
}

.sidebar-user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--action-w);           /* rgba(45,110,232,.12) */
  border: 1px solid rgba(45, 110, 232, 0.30);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: var(--action);
  flex-shrink: 0;
  letter-spacing: 0.02em;
}
```

### Composant React `<Sidebar>`

```tsx
interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  activeItem: string
  onNavigate: (route: string) => void
}
```

**Tooltip en mode réduit** : chaque `nav-item` doit avoir un `title` HTML (ou Tooltip composant) qui affiche le label au survol quand `collapsed === true`.

---

## §30 · TopBar Contextuelle `NEW v6.0`

### Anatomie

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Fil d'ariane dynamique]         [2025–2026 ●] [🔍] [🔔] [Avatar]  │
└──────────────────────────────────────────────────────────────────────┘
```

### Dimensions & fond

| Propriété | Valeur |
|---|---|
| Hauteur | 52px |
| Fond | `--surface` |
| Bordure basse | 1px `--border` |
| Padding horizontal | 18px |
| Layout | `display:flex; align-items:center; gap:10px` |

### Fil d'ariane (Breadcrumb)

Élément le plus important de la topbar. Il reflète la navigation actuelle et change à chaque route.

```
Cas 1 — page de niveau 1 :
  Élèves

Cas 2 — page de détail :
  Élèves  ›  Aminata Diallo

Cas 3 — sous-page d'un détail :
  Élèves  ›  Aminata Diallo  ›  Notes T1
```

```css
.topbar-breadcrumb {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12.5px;
  color: var(--ink-dim);
  overflow: hidden;
  white-space: nowrap;
}

.topbar-breadcrumb .bc-sep {
  color: var(--ink-disabled);
  font-size: 10px;
}

.topbar-breadcrumb .bc-current {
  color: var(--ink);
  font-weight: 500;
}

/* Segments intermédiaires : cliquables */
.topbar-breadcrumb .bc-link {
  color: var(--ink-dim);
  cursor: pointer;
  text-decoration: none;
}
.topbar-breadcrumb .bc-link:hover { color: var(--ink); }
```

### Sélecteur d'année scolaire

**Présent sur toutes les pages.** Contexte critique — toutes les données (élèves, notes, bulletins, paiements) sont filtrées par année scolaire active.

```
[ ● 2025–2026  ▾ ]
```

| Propriété | Valeur |
|---|---|
| Fond | `--surface-2` |
| Bordure | 1px `--border` |
| Radius | `--radius-md` |
| Hauteur | 28px |
| Padding | 0 9px |
| Font | Inter 12px `--ink-dim` |
| Indicateur actif | Point 5×5px `--success` à gauche du texte |
| Survol | fond `--surface-3` |

**Dropdown de sélection** : liste les années scolaires disponibles (`GET /api/annees/`). L'année active est marquée d'un ● vert. Le changement d'année recharge les données de la page courante.

### Boutons d'icônes (topbar)

```css
.topbar-icon-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  border: none;
  background: none;
  cursor: pointer;
  color: var(--ink-faint);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  transition: background 80ms, color 80ms;
}
.topbar-icon-btn:hover {
  background: var(--surface-2);
  color: var(--ink);
}
```

Boutons présents (de gauche à droite dans la zone droite) :
1. **Recherche** — icône `Search` · déclenche la Command Palette (§31)
2. **Notifications** — icône `Bell` · badge rouge si alertes non lues
3. **Avatar utilisateur** — 28px · cercle · fond `--action-w` · initiales

### Avatar topbar

```css
.topbar-user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--action-w);
  border: 1px solid rgba(45, 110, 232, 0.30);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9.5px;
  font-weight: 600;
  color: var(--action);
  cursor: pointer;
  letter-spacing: 0.02em;
}
```

---

## §31 · Architecture de Navigation `NEW v6.0`

### Groupes et items

La navigation est organisée en **5 groupes** qui suivent l'ordre naturel du cycle scolaire, plus un item standalone en haut.

```
────────────────────────────────────
  Tableau de bord                    ← item standalone, pas de groupe
────────────────────────────────────
  ÉLÈVES & CLASSES
    Élèves
    Classes
    Inscriptions
    Tuteurs
────────────────────────────────────
  PÉDAGOGIE
    Enseignants
    Cours
    Notes
    Bulletins
    Résultats
────────────────────────────────────
  VIE SCOLAIRE
    Séances
    Absences                         ← badge si absences non justifiées
────────────────────────────────────
  FINANCES
    Paiements
    Dépenses
────────────────────────────────────
  ADMINISTRATION
    Comptes
    Paramètres
────────────────────────────────────
```

### Tableau des routes

| Label nav | Route | Icône (Lucide) | Groupe |
|---|---|---|---|
| Tableau de bord | `/` | `LayoutDashboard` | — |
| Élèves | `/eleves` | `Users` | Élèves & Classes |
| Classes | `/classes` | `Building2` | Élèves & Classes |
| Inscriptions | `/inscriptions` | `ClipboardList` | Élèves & Classes |
| Tuteurs | `/tuteurs` | `HeartHandshake` | Élèves & Classes |
| Enseignants | `/enseignants` | `GraduationCap` | Pédagogie |
| Cours | `/cours` | `BookOpen` | Pédagogie |
| Notes | `/notes` | `Pencil` | Pédagogie |
| Bulletins | `/bulletins` | `FileText` | Pédagogie |
| Résultats | `/resultats` | `Trophy` | Pédagogie |
| Séances | `/seances` | `CalendarDays` | Vie scolaire |
| Absences | `/absences` | `UserX` | Vie scolaire |
| Paiements | `/paiements` | `CreditCard` | Finances |
| Dépenses | `/depenses` | `PieChart` | Finances |
| Comptes | `/comptes` | `UserCog` | Administration |
| Paramètres | `/parametres` | `Settings` | Administration |

### Règles d'accès par rôle

| Route | admin | directeur | comptable |
|---|---|---|---|
| Tableau de bord | ✓ | ✓ | ✓ |
| Élèves | ✓ | ✓ | — |
| Classes | ✓ | ✓ | — |
| Inscriptions | ✓ | ✓ | — |
| Tuteurs | ✓ | ✓ | — |
| Enseignants | ✓ | ✓ | — |
| Cours | ✓ | ✓ | — |
| Notes | ✓ | ✓ | — |
| Bulletins | ✓ | ✓ | — |
| Résultats | ✓ | ✓ | — |
| Séances | ✓ | ✓ | — |
| Absences | ✓ | ✓ | — |
| Paiements | ✓ | ✓ | ✓ |
| Dépenses | ✓ | ✓ | ✓ |
| Comptes | ✓ | — | — |
| Paramètres | ✓ | — | — |

Les items non accessibles sont **masqués** dans la sidebar (pas grisés).

### Command Palette (Ctrl+K)

À implémenter en v6.0. Raccourci global `Ctrl+K` / `Cmd+K` qui ouvre une modal de recherche permettant de :
- Naviguer vers n'importe quelle page de l'app
- Rechercher un élève ou un enseignant par nom / matricule
- Lancer une action rapide (ex : « Ajouter un élève »)

```tsx
interface CommandPaletteItem {
  type: 'route' | 'eleve' | 'enseignant' | 'action'
  label: string
  sublabel?: string       // ex : "6e A · MAT-2024-001"
  icon: LucideIcon
  onSelect: () => void
}
```

---

## §32 · Pattern Universel de Page `NEW v6.0`

**Toutes les pages de l'application suivent le même squelette.** Les zones sont dans cet ordre strict, de haut en bas.

### Squelette

```
┌─────────────────────────────────────────────────────────────────┐
│ PageHeader    — 18px top padding, 20px horizontal               │
│   [Titre Fraunces] [Badge compteur]   [Actions primaires]       │
│   [Sous-titre --ink-faint]                                      │
├─────────────────────────────────────────────────────────────────┤
│ PageToolbar   — 10px vertical padding, 20px horizontal          │
│   [Recherche] [Filtres…]        [Spacer]  [Vue toggle]          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ PageContent   — variable                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ PageFooter    — pagination, 10px vertical padding               │
└─────────────────────────────────────────────────────────────────┘
```

### PageHeader

```tsx
<div className="page-header">
  <div className="page-title-group">
    <h1 className="page-title">
      {title}
      {count !== undefined && <span className="count-badge">{count}</span>}
    </h1>
    {subtitle && <p className="page-subtitle">{subtitle}</p>}
  </div>
  <div className="page-actions">
    {secondaryActions}
    {primaryAction}
  </div>
</div>
```

```css
.page-header {
  padding: 18px 20px 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.page-title {
  font-family: var(--font-serif);    /* Fraunces */
  font-size: 20px;
  font-weight: 600;
  color: var(--ink);
  display: flex;
  align-items: center;
  gap: 7px;
  line-height: 1.2;
}

.count-badge {
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 500;
  background: var(--surface-3);
  color: var(--ink-dim);
  border-radius: 9px;
  padding: 1px 7px;
}

.page-subtitle {
  font-size: 12px;
  color: var(--ink-faint);
  margin-top: 2px;
}

.page-actions {
  display: flex;
  align-items: center;
  gap: 5px;
  flex-shrink: 0;
  padding-top: 2px;
}
```

### PageToolbar

```css
.page-toolbar {
  padding: 10px 20px;
  display: flex;
  align-items: center;
  gap: 7px;
  border-bottom: 1px solid var(--border-soft);
  flex-wrap: nowrap;
}

/* Champ de recherche */
.toolbar-search {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0 10px;
  height: 30px;
  width: 200px;
  font-size: 12.5px;
  color: var(--ink-faint);
  flex-shrink: 0;
}

/* Filtre Select */
.toolbar-filter {
  display: flex;
  align-items: center;
  gap: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0 10px;
  height: 30px;
  font-size: 12.5px;
  color: var(--ink-dim);
  cursor: pointer;
  flex-shrink: 0;
  white-space: nowrap;
}

.toolbar-spacer { flex: 1; }

/* Toggle liste / grille */
.view-toggle {
  display: flex;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.view-toggle-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
  color: var(--ink-faint);
  border-right: 1px solid var(--border);
  transition: background 80ms, color 80ms;
}
.view-toggle-btn:last-child { border-right: none; }
.view-toggle-btn.active { background: var(--surface-2); color: var(--ink); }
```

### PageFooter (Pagination)

```css
.page-footer {
  padding: 10px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--border-soft);
  font-size: 12px;
  color: var(--ink-faint);
}
```

Voir §18 pour la spécification complète de la pagination.

---

## Type A v2 · Page Liste `mis à jour v6.0`

Applique le pattern §32. Spécifications additionnelles pour les tableaux de données.

### Tableau de données — anatomie

```
[ ☐ ] Nom complet ↕   Matricule   Classe   Statut   Date ↕   [⋯]
────────────────────────────────────────────────────────────────────
[ ☐ ] [Avatar] Aminata Diallo   MAT-001   6e A    ● Actif   12 jan.  [⋯]
[ ☐ ] [Avatar] Ibrahim Soumah   MAT-002   4e C    ● Actif   14 jan.  [⋯]
...
```

### Spécifications du tableau

| Élément | Spec |
|---|---|
| Hauteur de ligne `tbody tr` | **42px** · `vertical-align: middle` |
| Header `thead th` | Inter 10.5px · `font-weight:600` · `--ink-faint` · uppercase · `letter-spacing:.05em` |
| Padding cellule | `padding: 0 10px` |
| Colonne checkbox | `width: 32px` |
| Colonne actions | `width: 32px` · bouton `⋯` Ghost icon |
| Hover ligne | fond `--surface-2` · 60ms |
| Ligne cliquable | `cursor: pointer` · onclick → page de détail |
| Bordure ligne | `border-bottom: 1px solid var(--border-soft)` |
| Bordure header | `border-bottom: 1px solid var(--border)` |

### Colonne Nom (avec avatar initiales)

```tsx
<td className="td-name">
  <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
    <div className="row-avatar">{initials}</div>
    {fullName}
  </div>
</td>
```

```css
.row-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--surface-3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 9.5px;
  font-weight: 600;
  color: var(--ink-dim);
  flex-shrink: 0;
}

.td-name {
  color: var(--ink);
  font-weight: 500;
}
```

### Colonne Matricule

```css
.td-mono {
  font-family: var(--font-mono);
  font-size: 11.5px;
  color: var(--ink-dim);
}
```

### Badge Statut

```css
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 500;
}

.status-active  { background: rgba(163,192,95,.12);  color: var(--success); }
.status-inactive { background: rgba(107,110,122,.12); color: var(--ink-faint); }
.status-pending  { background: rgba(201,138,74,.12);  color: var(--warning); }
```

### Toolbars spécifiques par module

#### Élèves
```
[🔍 Rechercher un élève…] [Classe ▾] [Statut ▾] [Niveau ▾]   [≡ ⊞]
```

#### Enseignants
```
[🔍 Rechercher un enseignant…] [Matière ▾] [Statut ▾]        [≡ ⊞]
```

#### Inscriptions
```
[🔍 Rechercher…] [Classe ▾] [Statut ▾] [Trimestre ▾]         [≡]
```

#### Paiements
```
[🔍 Rechercher…] [Élève ▾] [Période ▾] [Statut ▾]   [↓ Export] [≡]
```

#### Absences
```
[🔍 Rechercher…] [Classe ▾] [Justifiée ▾] [Période ▾]         [≡]
```

---

## Type J v2 · Dashboard `mis à jour v6.0`

Applique §32 (PageHeader uniquement, pas de toolbar).

### Layout

```
PageHeader
──────────────────────────────────────────────────────────────────
KPI Grid (4 colonnes égales, gap 12px)
──────────────────────────────────────────────────────────────────
Charts Grid (2fr + 1fr, gap 12px)
──────────────────────────────────────────────────────────────────
Activité récente (pleine largeur)
```

### KPI Card

```css
.kpi-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 14px;
  box-shadow: var(--shadow-card);
}

.kpi-card-label {
  font-size: 10.5px;
  font-weight: 500;
  color: var(--ink-faint);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 5px;
}

.kpi-card-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--ink);
  line-height: 1;
  font-family: var(--font-sans);
}

.kpi-card-trend {
  font-size: 10.5px;
  margin-top: 3px;
}
```

**Bandes de module** (border-top 2px) :

| Module | Token couleur | Classe |
|---|---|---|
| Pédagogie (élèves) | `--mod-ped` `#2d6ee8` | `.band-ped` |
| Vie scolaire | `--mod-vie` `#7c9a3f` | `.band-vie` |
| Finances | `--mod-fin` `#c98a4a` | `.band-fin` |
| Résultats / absences | `--mod-res` `#5b9dc4` | `.band-res` |

```css
.band-ped { border-top: 2px solid var(--mod-ped); }
.band-vie { border-top: 2px solid var(--mod-vie); }
.band-fin { border-top: 2px solid var(--mod-fin); }
.band-res { border-top: 2px solid var(--mod-res); }
```

### KPIs affichés

| KPI | Source API | Bande |
|---|---|---|
| Élèves inscrits | `GET /api/dashboard/stats` → `eleves_count` | `.band-ped` |
| Enseignants actifs | `GET /api/dashboard/stats` → `enseignants_count` | `.band-vie` |
| Paiements du mois | `GET /api/dashboard/stats` → `paiements_mois` | `.band-fin` |
| Absences ce mois | `GET /api/dashboard/stats` → `absences_mois` | `.band-res` |

### Section Activité récente

```tsx
interface ActivityItem {
  icon: LucideIcon
  iconColor: string       // ex : "var(--mod-ped)"
  title: string
  subtitle: string
  time: string            // ex : "Il y a 23 min"
}
```

```css
.activity-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-soft);
}

.activity-icon {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  background: var(--surface);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 14px;
}
```

---

## Type C v2 · Page Dossier `mis à jour v6.0`

Les pages de détail (élève, enseignant, classe) utilisent un **layout en deux zones verticales** : un Hero band fixe suivi de la zone à onglets.

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Hero Band (fond --surface, border-bottom)                    │
│  [Avatar 48px] [Nom Fraunces 18px] [Métadonnées]  [Actions] │
├─────────────────────────────────────────────────────────────┤
│ Tab Navigation (fond --surface, border-bottom)              │
│  [Profil] [Inscriptions] [Notes] [Absences] [....]          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Tab Content (scroll-y, padding 16px 20px)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Hero Band — spécification

```css
.dossier-hero {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.hero-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--surface-3);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--ink-dim);
  flex-shrink: 0;
}

.hero-name {
  font-family: var(--font-serif);
  font-size: 18px;
  color: var(--ink);
  font-weight: 600;
  line-height: 1.2;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 3px;
}

.hero-meta-item {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11.5px;
  color: var(--ink-faint);
}

.hero-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 5px;
}
```

### Tab Navigation — spécification

```css
.dossier-tabs {
  display: flex;
  border-bottom: 1px solid var(--border);
  padding: 0 20px;
  background: var(--surface);
  overflow-x: auto;
  scrollbar-width: none;
  flex-shrink: 0;
}

.dossier-tab {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 0 12px;
  height: 38px;
  font-size: 12.5px;
  color: var(--ink-dim);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  white-space: nowrap;
  transition: color 80ms, border-color 80ms;
  user-select: none;
}

.dossier-tab:hover { color: var(--ink); }

.dossier-tab.active {
  color: var(--halo);
  border-bottom-color: var(--halo);
  font-weight: 500;
}

.dossier-tab svg { width: 13px; height: 13px; }
```

### Onglets — Dossier Élève

| Onglet | Icône | Contenu |
|---|---|---|
| Profil | `User` | Infos personnelles, tuteur légal, contact |
| Inscriptions | `ClipboardList` | Historique des inscriptions par année |
| Notes | `Pencil` | Notes par matière / trimestre |
| Absences | `UserX` | Liste absences justifiées / non justifiées |
| Bulletins | `FileText` | Bulletins générés par trimestre |
| Documents | `Files` | Pièces jointes (§24) |
| Paiements | `CreditCard` | Historique paiements / échéances |

### Grille d'informations (dans un onglet)

```css
.info-section { margin-bottom: 18px; }

.info-section-title {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  margin-bottom: 8px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.info-field {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 9px 11px;
}

.info-field-label {
  font-size: 10.5px;
  color: var(--ink-faint);
  margin-bottom: 2px;
}

.info-field-value {
  font-size: 13px;
  color: var(--ink);
  font-weight: 500;
}

/* Valeur cliquable (lien vers une autre entité) */
.info-field-value.link {
  color: var(--action);
  cursor: pointer;
}

/* Valeur code (matricule, téléphone) */
.info-field-value.mono {
  font-family: var(--font-mono);
  font-size: 12px;
}
```

---

## Implémentation CSS — Tokens v6.0

> Ajouts sur le référentiel v5.0. Les variables existantes sont maintenues.

```css
:root {
  /* === Layout shell (NEW v6.0) === */
  --shell-sidebar-w:      218px;
  --shell-sidebar-col-w:  52px;
  --shell-topbar-h:       52px;
  --shell-content-pad-x:  20px;
  --shell-content-pad-y:  18px;

  /* === Tableau (NEW v6.0) === */
  --table-row-h:          42px;   /* hauteur ligne tbody */
  --table-header-h:       32px;   /* hauteur ligne thead */

  /* === Dossier (NEW v6.0) === */
  --dossier-hero-h:       80px;   /* hauteur hero band */
  --dossier-tabs-h:       38px;   /* hauteur barre d'onglets */
}
```

---

## Interfaces TypeScript — v6.0

```tsx
/* §29 — Sidebar */
interface NavItem {
  id: string
  label: string
  route: string
  icon: LucideIcon
  group: NavGroup
  badge?: number        // pour les absences non justifiées
  roles: UserRole[]
}

type NavGroup =
  | 'standalone'
  | 'eleves-classes'
  | 'pedagogie'
  | 'vie-scolaire'
  | 'finances'
  | 'administration'

type UserRole = 'admin' | 'directeur' | 'comptable'

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  activeRoute: string
  onNavigate: (route: string) => void
  user: { name: string; role: UserRole; initials: string }
  badgeCounts?: Partial<Record<string, number>>
}

/* §30 — TopBar */
interface TopBarProps {
  breadcrumbs: Array<{ label: string; route?: string }>
  activeYear: AnneeScol
  years: AnneeScol[]
  onYearChange: (id: number) => void
  user: { initials: string }
  notificationCount?: number
}

/* §32 — PageHeader */
interface PageHeaderProps {
  title: string
  count?: number
  subtitle?: string
  primaryAction?: ReactNode
  secondaryActions?: ReactNode[]
}

/* Type C v2 — Dossier */
interface DossierTab {
  id: string
  label: string
  icon: LucideIcon
  content: ReactNode
}

interface DossierHeroProps {
  initials: string
  name: string
  meta: Array<{ icon: LucideIcon; label: string; color?: string }>
  actions: ReactNode
}
```

---

## Changelog

### v6.0 (actuelle)

**Shell — Ajouts**
- `§28` Shell Applicatif : tokens layout, structure HTML, règles CSS.
- `§29` Sidebar Navigation : dimensions, états (déployée/réduite), header, nav-item, nav-section, badge, footer.
- `§30` TopBar Contextuelle : fil d'ariane dynamique, sélecteur d'année scolaire, boutons d'icônes.
- `§31` Architecture de Navigation : 5 groupes métier, table des routes, règles d'accès par rôle, Command Palette.
- `§32` Pattern Universel de Page : PageHeader, PageToolbar, PageContent, PageFooter — appliqué à tous les types.

**Types de pages — Refonte**
- `Type A v2` : hauteur de ligne 42px, colonne avatar+initiales, colonne mono matricule, toolbars spécifiques par module.
- `Type J v2` : KPI grid 4 colonnes, bandes de module border-top, section activité récente.
- `Type C v2` : Hero band 48px avatar + métadonnées + actions, tab navigation 7 onglets, grille d'informations.

**CSS — Ajouts**
- Tokens `--shell-*` (layout du shell).
- Tokens `--table-row-h`, `--table-header-h`.
- Tokens `--dossier-hero-h`, `--dossier-tabs-h`.

**TypeScript — Ajouts**
- `NavItem`, `NavGroup`, `SidebarProps`.
- `TopBarProps`.
- `PageHeaderProps`.
- `DossierTab`, `DossierHeroProps`.

### v5.0
Voir design-system-v5.0.md.

---

## §33 · Boutons & Actions `NEW v6.0`

Référentiel complet des boutons. Toutes les actions primaires, secondaires et destructives passent par ces variants.

### Variants

| Variant | Usage | CSS class |
|---|---|---|
| Primary (Halo) | Action principale de la page | `.btn-primary` |
| Ghost | Actions secondaires | `.btn-ghost` |
| Danger | Suppression / action destructive | `.btn-danger` |
| Ghost Danger | Danger moins prioritaire | `.btn-ghost-danger` |
| Icon only | Bouton sans label (toolbar, actions inline) | `.btn-icon` |

### CSS complet

```css
/* Base */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 30px;
  padding: 0 11px;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: 12.5px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: background 80ms, color 80ms, border-color 80ms, opacity 80ms;
  white-space: nowrap;
  user-select: none;
  text-decoration: none;
}

.btn svg, .btn .btn-icon-el {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}

/* Disabled (tout variant) */
.btn:disabled, .btn[aria-disabled="true"] {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

/* === Primary (Halo) === */
.btn-primary {
  background: var(--halo);          /* #d9a75c */
  color: var(--halo-ink);           /* #161208 */
}
.btn-primary:hover { background: var(--halo-bright); }    /* #f0c98a */
.btn-primary:active { background: var(--halo-dim); }

/* === Ghost === */
.btn-ghost {
  background: transparent;
  color: var(--ink-dim);
  border: 1px solid var(--border);
}
.btn-ghost:hover { background: var(--surface-2); color: var(--ink); }
.btn-ghost:active { background: var(--surface-3); }

/* === Danger === */
.btn-danger {
  background: var(--danger);        /* #e0707f */
  color: #fff;
}
.btn-danger:hover { background: #e8848f; }
.btn-danger:active { background: #c85e6b; }

/* === Ghost Danger === */
.btn-ghost-danger {
  background: transparent;
  color: var(--danger);
  border: 1px solid rgba(224, 112, 127, 0.30);
}
.btn-ghost-danger:hover { background: var(--danger-w); }

/* === Tailles === */
.btn-sm { height: 26px; padding: 0 9px; font-size: 12px; }
.btn-lg { height: 36px; padding: 0 14px; font-size: 13.5px; }

/* === Icon only === */
.btn-icon {
  width: 30px;
  height: 30px;
  padding: 0;
  background: transparent;
  border: none;
  color: var(--ink-faint);
  border-radius: var(--radius-md);
}
.btn-icon:hover { background: var(--surface-2); color: var(--ink); }
.btn-icon svg { width: 15px; height: 15px; }

/* .btn-icon-sm */
.btn-icon.btn-sm { width: 26px; height: 26px; }
.btn-icon.btn-sm svg { width: 13px; height: 13px; }
```

### Règles d'usage

- **1 seul bouton Primary** par page (le CTA principal dans `PageHeader`).
- **Actions destructives** : toujours précédées d'une Modal de Confirmation (§36).
- **Boutons dans les lignes de tableau** : `btn-icon` uniquement (bouton `⋯` → dropdown).
- **Icône + Label** : l'icône est à gauche du label, sauf pour les actions de téléchargement (↓) qui peuvent être à droite.

---

## §34 · Composants de Formulaire `NEW v6.0`

### Input texte

```css
.form-field { display: flex; flex-direction: column; gap: 5px; }

.form-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--ink-dim);
}

.form-label .required {
  color: var(--danger);
  margin-left: 2px;
}

.form-input {
  height: 34px;
  padding: 0 11px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--ink);
  width: 100%;
  transition: border-color 100ms, box-shadow 100ms;
  outline: none;
}

.form-input::placeholder { color: var(--ink-disabled); }

.form-input:focus {
  border-color: var(--action);
  box-shadow: 0 0 0 3px var(--action-ring);   /* rgba(45,110,232,.20) */
}

.form-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--surface-2);
}

/* Erreur */
.form-input.error { border-color: var(--danger); }
.form-input.error:focus { box-shadow: 0 0 0 3px rgba(224,112,127,.20); }
.form-error { font-size: 11.5px; color: var(--danger); margin-top: 3px; }

/* Input avec icône gauche */
.form-input-wrapper {
  position: relative;
}
.form-input-wrapper .input-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--ink-faint);
  pointer-events: none;
  width: 14px;
  height: 14px;
}
.form-input-wrapper .form-input { padding-left: 32px; }
```

### Textarea

```css
.form-textarea {
  padding: 9px 11px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--ink);
  width: 100%;
  min-height: 80px;
  resize: vertical;
  transition: border-color 100ms, box-shadow 100ms;
  outline: none;
  line-height: 1.5;
}

.form-textarea::placeholder { color: var(--ink-disabled); }
.form-textarea:focus {
  border-color: var(--action);
  box-shadow: 0 0 0 3px var(--action-ring);
}
```

### Select

```css
.form-select {
  height: 34px;
  padding: 0 30px 0 11px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: 13px;
  color: var(--ink);
  width: 100%;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b6e7a' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  cursor: pointer;
  outline: none;
  transition: border-color 100ms, box-shadow 100ms;
}
.form-select:focus {
  border-color: var(--action);
  box-shadow: 0 0 0 3px var(--action-ring);
}
```

### Checkbox & Switch

```css
/* Checkbox */
.form-checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.form-checkbox-wrapper input[type="checkbox"] {
  width: 15px;
  height: 15px;
  accent-color: var(--action);
  cursor: pointer;
}

.form-checkbox-label {
  font-size: 13px;
  color: var(--ink-dim);
}

/* Switch (toggle) */
.form-switch {
  position: relative;
  width: 36px;
  height: 20px;
  flex-shrink: 0;
}

.form-switch input { opacity: 0; width: 0; height: 0; }

.form-switch-track {
  position: absolute;
  inset: 0;
  background: var(--surface-3);
  border-radius: 10px;
  cursor: pointer;
  transition: background 150ms;
}

.form-switch input:checked ~ .form-switch-track { background: var(--action); }

.form-switch-thumb {
  position: absolute;
  left: 2px;
  top: 2px;
  width: 16px;
  height: 16px;
  background: #fff;
  border-radius: 50%;
  transition: transform 150ms;
  box-shadow: 0 1px 3px rgba(0,0,0,.30);
}

.form-switch input:checked ~ .form-switch-track .form-switch-thumb {
  transform: translateX(16px);
}
```

### Grille de formulaire

```css
/* Grille 2 colonnes (standard dans les drawers) */
.form-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

/* Champ pleine largeur dans la grille */
.form-grid-2 .form-field.full {
  grid-column: 1 / -1;
}

/* Espacement entre sections dans un formulaire */
.form-section {
  margin-bottom: 20px;
}

.form-section-title {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-soft);
}
```

### TypeScript — FormField

```tsx
interface FormFieldProps {
  label: string
  required?: boolean
  error?: string
  hint?: string
  children: ReactNode
}

// Valeurs de formulaire élève (exemple)
interface EleveFormValues {
  prenom: string
  nom: string
  date_naissance: string         // "YYYY-MM-DD"
  lieu_naissance: string
  genre: 'M' | 'F'
  nationalite: string
  tuteur_id?: number
  photo?: File
}
```

---

## §35 · Drawer (Panneau Latéral) `NEW v6.0`

Le Drawer est le **conteneur standard pour toute opération de création ou modification** dans Auréole. Il s'ouvre depuis la droite et coexiste avec la page (pas de modal plein écran).

### Dimensions & comportement

| Propriété | Valeur |
|---|---|
| Largeur | 460px |
| Largeur `sm` (formulaires courts) | 380px |
| Largeur `lg` (formulaires complexes) | 560px |
| Fond | `--surface` |
| Bordure gauche | 1px `--border` |
| Overlay | `rgba(0,0,0,.45)` sur le contenu principal |
| Transition ouverture | `transform 220ms cubic-bezier(.25,0,0,1)` |
| Fermeture | Clic overlay, touche `Escape`, bouton ✕ |

### Structure HTML

```tsx
{/* Overlay */}
<div
  className="drawer-overlay"
  onClick={onClose}
  aria-hidden="true"
/>

{/* Drawer */}
<div className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
  {/* Header */}
  <div className="drawer-header">
    <h2 className="drawer-title" id="drawer-title">{title}</h2>
    <button className="btn-icon" onClick={onClose} aria-label="Fermer">
      <X size={16} />
    </button>
  </div>

  {/* Body (scrollable) */}
  <div className="drawer-body">
    {children}
  </div>

  {/* Footer (actions) */}
  <div className="drawer-footer">
    <button className="btn btn-ghost" onClick={onClose}>Annuler</button>
    <button className="btn btn-primary" onClick={onSubmit} disabled={isSubmitting}>
      {isSubmitting ? 'Enregistrement…' : submitLabel}
    </button>
  </div>
</div>
```

### CSS

```css
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 100;
  animation: fadeIn 150ms ease;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 460px;
  height: 100vh;
  background: var(--surface);
  border-left: 1px solid var(--border);
  box-shadow: var(--shadow-float);
  z-index: 101;
  display: flex;
  flex-direction: column;
  transform: translateX(0);
  animation: slideIn 220ms cubic-bezier(.25, 0, 0, 1);
}

.drawer.closing { animation: slideOut 180ms cubic-bezier(.4, 0, 1, 1) forwards; }

@keyframes slideIn {
  from { transform: translateX(100%); }
  to   { transform: translateX(0); }
}
@keyframes slideOut {
  from { transform: translateX(0); }
  to   { transform: translateX(100%); }
}

/* Variantes de largeur */
.drawer.sm { width: 380px; }
.drawer.lg { width: 560px; }

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 52px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.drawer-title {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.drawer-body::-webkit-scrollbar { width: 4px; }
.drawer-body::-webkit-scrollbar-thumb { background: var(--surface-3); border-radius: 4px; }

.drawer-footer {
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-shrink: 0;
  background: var(--surface);
}
```

### Titres de Drawer par module

| Module | Titre création | Titre modification |
|---|---|---|
| Élève | Nouvel élève | Modifier l'élève |
| Classe | Nouvelle classe | Modifier la classe |
| Enseignant | Nouvel enseignant | Modifier l'enseignant |
| Cours | Nouveau cours | Modifier le cours |
| Inscription | Nouvelle inscription | Modifier l'inscription |
| Paiement | Enregistrer un paiement | Modifier le paiement |
| Absence | Signaler une absence | Modifier l'absence |
| Compte | Nouveau compte | Modifier le compte |

---

## §36 · Modal de Confirmation `NEW v6.0`

Utilisée **exclusivement pour les actions destructives** (suppression, désactivation, clôture d'année). Ne pas utiliser pour de simples avertissements.

### Structure

```
┌────────────────────────────────────────┐
│ [Icon danger 32px]                     │
│ Supprimer l'élève ?               [✕]  │
│                                        │
│ Cette action est irréversible.         │
│ Les données d'Aminata Diallo           │
│ seront définitivement supprimées.      │
│                                        │
│          [Annuler]  [Supprimer]        │
└────────────────────────────────────────┘
```

### CSS

```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn 120ms ease;
}

.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  padding: 24px;
  width: 360px;
  box-shadow: var(--shadow-float);
  animation: popIn 150ms cubic-bezier(.34, 1.3, .64, 1);
}

@keyframes popIn {
  from { opacity: 0; transform: scale(0.94); }
  to   { opacity: 1; transform: scale(1); }
}

.modal-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  background: var(--danger-w);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--danger);
  margin-bottom: 14px;
}

.modal-title {
  font-family: var(--font-serif);
  font-size: 16px;
  font-weight: 600;
  color: var(--ink);
  margin-bottom: 8px;
}

.modal-body {
  font-size: 13px;
  color: var(--ink-dim);
  line-height: 1.6;
  margin-bottom: 20px;
}

.modal-body strong { color: var(--ink); }

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
```

### TypeScript

```tsx
interface ConfirmModalProps {
  title: string
  body: ReactNode
  confirmLabel?: string          // défaut : "Supprimer"
  confirmVariant?: 'danger' | 'warning'
  onConfirm: () => Promise<void>
  onCancel: () => void
  isLoading?: boolean
}
```

---

## §37 · Toasts & Notifications `NEW v6.0`

Les toasts fournissent un retour immédiat après chaque action (création, modification, suppression, erreur).

### Position

Coin **bas-droite** de l'écran. Stack vertical (le plus récent en bas). Disparaissent automatiquement après **4 000 ms**. Peuvent être fermés manuellement.

### Variants

| Type | Couleur icône | Fond | Usage |
|---|---|---|---|
| `success` | `--success` | `rgba(163,192,95,.10)` | Enregistrement réussi |
| `error` | `--danger` | `rgba(224,112,127,.10)` | Erreur API / validation |
| `warning` | `--warning` | `rgba(201,138,74,.10)` | Avertissement non bloquant |
| `info` | `--action` | `rgba(45,110,232,.10)` | Information neutre |

### CSS

```css
.toast-container {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 300;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-float);
  min-width: 280px;
  max-width: 380px;
  pointer-events: all;
  animation: toastIn 200ms cubic-bezier(.34, 1.2, .64, 1);
}

@keyframes toastIn {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0); }
}

.toast.exiting { animation: toastOut 150ms ease forwards; }

@keyframes toastOut {
  to { opacity: 0; transform: translateX(20px); }
}

.toast-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.toast-content { flex: 1; }

.toast-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
  line-height: 1.3;
}

.toast-message {
  font-size: 12px;
  color: var(--ink-dim);
  margin-top: 2px;
  line-height: 1.4;
}

.toast-close {
  width: 18px;
  height: 18px;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--ink-faint);
  flex-shrink: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Barre de progression (timer visuel) */
.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 2px;
  border-radius: 0 0 var(--radius-lg) var(--radius-lg);
  animation: toastProgress 4000ms linear forwards;
}

@keyframes toastProgress { from { width: 100%; } to { width: 0%; } }

.toast.success .toast-progress { background: var(--success); }
.toast.error   .toast-progress { background: var(--danger); }
.toast.warning .toast-progress { background: var(--warning); }
.toast.info    .toast-progress { background: var(--action); }
```

### Messages standards par action

| Action | Type | Titre | Message |
|---|---|---|---|
| Élève créé | success | Élève ajouté | {nom} a été enregistré avec succès. |
| Élève modifié | success | Modifications enregistrées | Le dossier de {nom} a été mis à jour. |
| Élève supprimé | success | Élève supprimé | Le dossier a été définitivement supprimé. |
| Erreur réseau | error | Erreur de connexion | Impossible de joindre le serveur. Vérifiez le réseau. |
| Erreur validation | error | Données invalides | {message de l'API}. |
| Bulletin publié | success | Bulletin publié | Le bulletin T{n} de {classe} a été publié. |
| Paiement enregistré | success | Paiement enregistré | {montant} GNF pour {élève}. |

---

## §38 · États Vides (Empty States) `NEW v6.0`

Affiché quand une liste ou un onglet ne contient aucune donnée.

### Structure

```
          [Icône 40px --ink-faint]

          Aucun élève inscrit

          Les élèves inscrits apparaîtront ici.

               [+ Ajouter un élève]       ← optionnel
```

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  gap: 10px;
  color: var(--ink-faint);
}

.empty-state-icon {
  width: 40px;
  height: 40px;
  opacity: 0.4;
  margin-bottom: 4px;
}

.empty-state-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--ink-dim);
}

.empty-state-subtitle {
  font-size: 12.5px;
  color: var(--ink-faint);
  max-width: 280px;
  line-height: 1.5;
}
```

### Messages par module

| Module / Contexte | Titre | Sous-titre |
|---|---|---|
| Élèves (liste vide) | Aucun élève inscrit | Les élèves inscrits apparaîtront ici. |
| Élèves (recherche sans résultat) | Aucun résultat | Aucun élève ne correspond à « {terme} ». |
| Notes (aucune note) | Notes non saisies | Les notes de ce trimestre n'ont pas encore été saisies. |
| Absences (aucune) | Aucune absence | Aucune absence enregistrée pour cette période. |
| Bulletins (aucun) | Aucun bulletin | Les bulletins seront disponibles après la saisie des notes. |
| Paiements (aucun) | Aucun paiement | Aucun paiement enregistré pour cet élève. |
| Documents (aucun) | Aucun document | Aucune pièce jointe pour ce dossier. |

---

## §39 · Skeletons (Chargement) `NEW v6.0`

Utilisé pendant le chargement initial des données API. Remplace les spinners.

```css
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--surface-2) 25%,
    var(--surface-3) 50%,
    var(--surface-2) 75%
  );
  background-size: 800px 100%;
  animation: shimmer 1.4s infinite linear;
  border-radius: var(--radius-sm);
}
```

### Skeleton — ligne de tableau

```tsx
// Répéter 8 fois pendant le chargement
<tr>
  <td><div className="skeleton" style={{ width:15, height:15, borderRadius:3 }} /></td>
  <td>
    <div style={{ display:'flex', alignItems:'center', gap:8 }}>
      <div className="skeleton" style={{ width:26, height:26, borderRadius:'50%' }} />
      <div className="skeleton" style={{ width:140, height:13 }} />
    </div>
  </td>
  <td><div className="skeleton" style={{ width:100, height:12 }} /></td>
  <td><div className="skeleton" style={{ width:50, height:12 }} /></td>
  <td><div className="skeleton" style={{ width:60, height:20, borderRadius:9 }} /></td>
  <td><div className="skeleton" style={{ width:70, height:12 }} /></td>
</tr>
```

### Skeleton — KPI card

```tsx
<div className="kpi-card">
  <div className="skeleton" style={{ width:80, height:11, marginBottom:8 }} />
  <div className="skeleton" style={{ width:60, height:28 }} />
  <div className="skeleton" style={{ width:100, height:11, marginTop:6 }} />
</div>
```

---

## §40 · Command Palette (Ctrl+K) `NEW v6.0`

### Comportement

- Déclenchement : `Ctrl+K` (Windows) ou icône Loupe dans la TopBar.
- Fermeture : `Escape`, clic hors de la palette, sélection d'un résultat.
- Recherche locale : navigation entre pages + routes.
- Recherche API : élèves et enseignants par nom ou matricule (`GET /api/eleves/?q=` et `GET /api/enseignants/?q=`).
- Latence API : debounce 250ms avant d'envoyer la requête.

### Structure

```
┌────────────────────────────────────────────────────────────┐
│ [🔍  Rechercher une page, un élève…             ]    [Esc] │
├────────────────────────────────────────────────────────────┤
│ PAGES                                                       │
│  📊  Tableau de bord                                        │
│  👤  Élèves                                                 │
│  ✏   Notes                                                  │
│                                                             │
│ ÉLÈVES                                                      │
│  [av] Aminata Diallo       MAT-001 · 6e A                  │
│  [av] Aissatou Diallo      MAT-009 · 5e A                  │
└────────────────────────────────────────────────────────────┘
```

### CSS

```css
.cmd-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  z-index: 500;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 120px;
  animation: fadeIn 100ms ease;
}

.cmd-palette {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-xl);
  width: 520px;
  max-height: 440px;
  box-shadow: var(--shadow-float);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: popIn 150ms cubic-bezier(.34, 1.2, .64, 1);
}

.cmd-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  height: 48px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.cmd-input {
  flex: 1;
  background: none;
  border: none;
  font-family: var(--font-sans);
  font-size: 14px;
  color: var(--ink);
  outline: none;
}
.cmd-input::placeholder { color: var(--ink-faint); }

.cmd-results {
  overflow-y: auto;
  padding: 6px 0;
}

.cmd-group-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  padding: 8px 16px 4px;
}

.cmd-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 12px;
  height: 38px;
  cursor: pointer;
  border-radius: var(--radius-md);
  margin: 1px 6px;
  color: var(--ink-dim);
  font-size: 13px;
  transition: background 60ms, color 60ms;
}

.cmd-item:hover,
.cmd-item.focused {
  background: var(--surface-2);
  color: var(--ink);
}

.cmd-item-icon {
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  font-size: 14px;
}

.cmd-item-meta {
  margin-left: auto;
  font-size: 11px;
  color: var(--ink-faint);
  font-family: var(--font-mono);
}
```

---

## Type B v2 · Formulaires via Drawer `NEW v6.0`

Tous les formulaires de création et modification utilisent le Drawer (§35). Il n'y a pas de page dédiée aux formulaires — tout se fait inline.

### Champs par module

#### Drawer — Élève

```
Section : Identité
  [Prénom *]          [Nom de famille *]
  [Date de naissance *] [Lieu de naissance *]
  [Genre * ▾]         [Nationalité]

Section : Tuteur légal
  [Tuteur * ▾ — sélectionner un tuteur existant]
  [ou] Lien "Créer un nouveau tuteur"

Section : Photo
  [Zone upload 1:1, max 2MB, JPG/PNG]
```

#### Drawer — Classe

```
Section : Informations
  [Nom * ]            [Niveau * ▾]
  [Capacité max *]    [Année scolaire * ▾]

Section : Frais
  [Frais d'inscription]  [Mensualité]
```

#### Drawer — Inscription

```
Section : Inscription
  [Élève * — search autocomplete]
  [Classe * ▾]
  [Année scolaire * ▾]
  [Statut ▾]           [Date d'inscription *]
```

#### Drawer — Paiement

```
Section : Paiement
  [Élève * — search autocomplete]
  [Montant * (GNF)]    [Date *]
  [Type ▾]             [Référence]
  [Commentaire (textarea)]
```

#### Drawer — Absence

```
Section : Absence
  [Élève * — search autocomplete]
  [Date *]             [Séance * ▾]
  [Justifiée ? (switch)]
  [Motif (textarea, visible si justifiée)]
```

#### Drawer — Compte utilisateur

```
Section : Informations
  [Prénom *]           [Nom *]
  [Nom d'utilisateur *] [Email]
  [Rôle * ▾ : admin / directeur / comptable]

Section : Mot de passe
  [Mot de passe *]     [Confirmer *]
```

---

## Type D · Saisie de Notes `NEW v6.0`

La saisie de notes est le type de page le plus spécifique de l'application. Elle n'utilise pas le pattern §32 standard.

### Layout

```
TopBar : Notes ›  Mathématiques · 5e B · T1

┌──────────────────────────────────────────────────────────────┐
│ PageHeader                                                    │
│  Saisie des notes — Mathématiques        [Enregistrer] [▸]   │
│  5e B · Trimestre 1 · 2025–2026 · Coef. 3                    │
├──────────────────────────────────────────────────────────────┤
│ Toolbar                                                       │
│  [🔍 Rechercher un élève…]    [Tous ▾]   [Écarts-type]       │
├──────────────────────────────────────────────────────────────┤
│ Tableau de saisie                                             │
│  Nom élève ↕    Composition 1   Composition 2   Moyenne       │
│  ──────────────────────────────────────────────────────────── │
│  Aminata D.    [  14.50  ]     [  16.00  ]     15.25 / 20    │
│  Ibrahim S.    [         ]     [  12.50  ]     12.50 / 20    │
│  ...                                                          │
├──────────────────────────────────────────────────────────────┤
│ Pied : Moyenne de classe : 13.42 / 20   Manquantes : 3       │
└──────────────────────────────────────────────────────────────┘
```

### Input de note dans le tableau

```css
.note-input {
  width: 80px;
  height: 34px;
  text-align: center;
  background: var(--surface-2);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 500;
  color: var(--ink);
  outline: none;
  transition: border-color 100ms, background 100ms;
}

.note-input:focus {
  background: var(--surface);
  border-color: var(--action);
  box-shadow: 0 0 0 2px var(--action-ring);
}

/* Note invalide (hors 0–20) */
.note-input.invalid {
  border-color: var(--danger);
  color: var(--danger);
}

/* Cellule moyenne (non éditable) */
.note-avg {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 600;
  color: var(--ink);
  padding: 0 10px;
}

.note-avg.high  { color: var(--success); }
.note-avg.low   { color: var(--danger); }
.note-avg.empty { color: var(--ink-faint); font-style: italic; }
```

### Règles de validation

- Note comprise entre **0.00 et 20.00** (2 décimales).
- Séparateur décimal : point ou virgule → normaliser en point avant envoi API.
- `Tab` → passe à la cellule suivante dans la même colonne.
- `Enter` → passe à la ligne suivante.
- Sauvegarde auto : `PATCH /api/notes/{id}` à chaque `blur` (sortie du champ).
- Sauvegarde manuelle : bouton [Enregistrer tout] → `PATCH /api/notes/bulk`.

---

## §41 · Implémentation module par module `NEW v6.0`

Guide de correspondance entre chaque module de l'application, ses types de pages, et ses endpoints API.

### Tableau de bord

| Type de page | API | Données |
|---|---|---|
| Type J v2 | `GET /api/dashboard/stats` | KPIs, moyennes, absences 6 mois, activité |

### Élèves

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/eleves/?page=&q=&classe_id=&statut=` |
| Créer | Drawer B v2 | `POST /api/eleves/` |
| Modifier | Drawer B v2 | `PATCH /api/eleves/{id}` |
| Voir dossier | Type C v2 | `GET /api/eleves/{id}` |
| Désactiver | Confirm Modal | `PATCH /api/eleves/{id}` → `{ statut: 'inactif' }` |
| Supprimer | Confirm Modal | `DELETE /api/eleves/{id}` |

**Onglets du dossier élève et leurs API :**

| Onglet | API |
|---|---|
| Profil | données de `GET /api/eleves/{id}` |
| Inscriptions | `GET /api/inscriptions/?eleve_id={id}` |
| Notes | `GET /api/notes/?eleve_id={id}&trimestre_id=` |
| Absences | `GET /api/absences/?eleve_id={id}` |
| Bulletins | `GET /api/bulletins/?eleve_id={id}` |
| Documents | `GET /api/eleves/{id}/documents` |
| Paiements | `GET /api/paiements/?eleve_id={id}` |

### Classes

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/classes/?annee_id=` |
| Créer | Drawer B v2 | `POST /api/classes/` |
| Modifier | Drawer B v2 | `PATCH /api/classes/{id}` |
| Voir détail | Type C v2 | `GET /api/classes/{id}` |
| Supprimer | Confirm Modal | `DELETE /api/classes/{id}` |

**Onglets dossier classe :**

| Onglet | API |
|---|---|
| Informations | données de `GET /api/classes/{id}` |
| Élèves inscrits | `GET /api/inscriptions/?classe_id={id}` |
| Cours affectés | `GET /api/cours/?classe_id={id}` |
| Emploi du temps | `GET /api/seances/?classe_id={id}` |

### Enseignants

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/enseignants/?q=&statut=` |
| Créer | Drawer B v2 | `POST /api/enseignants/` |
| Modifier | Drawer B v2 | `PATCH /api/enseignants/{id}` |
| Voir dossier | Type C v2 | `GET /api/enseignants/{id}` |

**Onglets dossier enseignant :**

| Onglet | API |
|---|---|
| Profil | données de `GET /api/enseignants/{id}` |
| Cours enseignés | `GET /api/cours/?enseignant_id={id}` |
| Emploi du temps | `GET /api/seances/?enseignant_id={id}` |
| Absences | `GET /api/absences/?enseignant_id={id}` |

### Inscriptions

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/inscriptions/?annee_id=&classe_id=&statut=` |
| Créer | Drawer B v2 | `POST /api/inscriptions/` |
| Modifier | Drawer B v2 | `PATCH /api/inscriptions/{id}` |

### Notes

| Opération | Type | API |
|---|---|---|
| Saisie | Type D | `GET /api/notes/?cours_id=&trimestre_id=&classe_id=` |
| Enregistrer | Type D | `PATCH /api/notes/{id}` ou `POST /api/notes/bulk` |

**Navigation vers la saisie de notes :** depuis la liste des cours → clic sur [Saisir notes] → Type D.

### Bulletins

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/bulletins/?classe_id=&trimestre_id=&statut=` |
| Générer | Action sur liste | `POST /api/bulletins/generate` `{ classe_id, trimestre_id }` |
| Publier | Confirm Modal | `PATCH /api/bulletins/{id}` `{ statut: 'publié' }` |
| Voir | Type L (visionneuse) | `GET /api/bulletins/{id}/pdf` |

### Résultats

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/resultats/?annee_id=&classe_id=` |
| Modifier passage | Drawer B v2 | `PATCH /api/resultats/{id}` |

### Absences

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/absences/?classe_id=&justifiee=&periode=` |
| Signaler | Drawer B v2 | `POST /api/absences/` |
| Justifier | Drawer B v2 (sm) | `PATCH /api/absences/{id}` `{ justifiee: true, motif }` |
| Supprimer | Confirm Modal | `DELETE /api/absences/{id}` |

### Paiements

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/paiements/?eleve_id=&periode=&statut=` |
| Enregistrer | Drawer B v2 | `POST /api/paiements/` |
| Modifier | Drawer B v2 | `PATCH /api/paiements/{id}` |

### Dépenses

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/depenses/?periode=&categorie=` |
| Ajouter | Drawer B v2 | `POST /api/depenses/` |

### Paramètres — Années scolaires

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/annees/` |
| Créer | Drawer B v2 | `POST /api/annees/` |
| Clôturer | Confirm Modal | `POST /api/annees/{id}/cloture` |

### Comptes utilisateurs

| Opération | Type | API |
|---|---|---|
| Liste | Type A v2 | `GET /api/comptes/` |
| Créer | Drawer B v2 | `POST /api/comptes/` |
| Modifier | Drawer B v2 | `PATCH /api/comptes/{id}` |
| Désactiver | Confirm Modal | `PATCH /api/comptes/{id}` `{ actif: false }` |

---

## §42 · Raccourcis Clavier (Desktop) `NEW v6.0`

| Raccourci | Action |
|---|---|
| `Ctrl+K` | Ouvrir Command Palette |
| `Escape` | Fermer Drawer / Modal / Command Palette |
| `Ctrl+S` | Sauvegarder le formulaire en cours (Drawer) |
| `Tab` | Dans Type D : passer au champ de note suivant |
| `Enter` | Dans Type D : passer à la ligne suivante |
| `Ctrl+Enter` | Dans les Drawers : soumettre le formulaire |
| `←` `→` | Naviguer entre les onglets d'un dossier |

---

## §43 · Référentiel Complet des Tokens CSS `NEW v6.0`

```css
/* ==========================================================
   Auréole Design System — Tokens complets v6.0
   À importer dans globals.css ou index.css
   ========================================================== */

:root {
  /* === Couleurs de fond === */
  --base:       #0e0f13;
  --surface:    #16181f;
  --surface-2:  #1d1f28;
  --surface-3:  #262932;

  /* === Texte === */
  --ink:          #f1eee4;
  --ink-dim:      #a7a9b4;
  --ink-faint:    #6b6e7a;
  --ink-disabled: #3f424b;

  /* === Halo (accent gold) === */
  --halo:        #d9a75c;
  --halo-bright: #f0c98a;
  --halo-dim:    #8a6a3c;
  --halo-ink:    #161208;
  --halo-wash:   rgba(217, 167, 92, 0.12);

  /* === Action (bleu) === */
  --action:      #2d6ee8;
  --action-dk:   #1e58c4;
  --action-w:    rgba(45, 110, 232, 0.12);
  --action-ring: rgba(45, 110, 232, 0.20);

  /* === Feedback === */
  --success:   #a3c05f;
  --success-w: rgba(163, 192, 95, 0.10);
  --warning:   #c98a4a;
  --warning-w: rgba(201, 138, 74, 0.10);
  --danger:    #e0707f;
  --danger-w:  rgba(224, 112, 127, 0.10);
  --info:      #5b9dc4;
  --info-w:    rgba(91, 157, 196, 0.10);

  /* === Couleurs de module === */
  --mod-ped:  #2d6ee8;   /* Pédagogie */
  --mod-vie:  #7c9a3f;   /* Vie scolaire */
  --mod-fin:  #c98a4a;   /* Finances */
  --mod-res:  #5b9dc4;   /* Résultats */

  /* === Bordures === */
  --border:      rgba(255, 255, 255, 0.09);
  --border-soft: rgba(255, 255, 255, 0.04);

  /* === Ombres === */
  --shadow-card:  0 1px 3px rgba(0,0,0,.35), 0 4px 12px -4px rgba(0,0,0,.40);
  --shadow-float: 0 4px 24px rgba(0,0,0,.55), 0 1px 4px rgba(0,0,0,.30);

  /* === Radius === */
  --radius-xs:  2px;
  --radius-sm:  4px;
  --radius:     6px;
  --radius-md:  8px;
  --radius-lg:  12px;
  --radius-xl:  16px;

  /* === Typographie === */
  --font-sans:  'Inter', system-ui, -apple-system, sans-serif;
  --font-serif: 'Fraunces', Georgia, 'Times New Roman', serif;
  --font-mono:  'IBM Plex Mono', 'Courier New', monospace;

  /* === Layout shell (NEW v6.0) === */
  --shell-sidebar-w:      218px;
  --shell-sidebar-col-w:  52px;
  --shell-topbar-h:       52px;
  --shell-content-pad-x:  20px;
  --shell-content-pad-y:  18px;

  /* === Composants (NEW v6.0) === */
  --table-row-h:     42px;
  --table-header-h:  32px;
  --dossier-hero-h:  80px;
  --dossier-tabs-h:  38px;
  --drawer-w:        460px;
  --drawer-w-sm:     380px;
  --drawer-w-lg:     560px;
}
```

---

## §44 · Structure de fichiers Frontend `NEW v6.0`

```
aureole-frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx          # §28 — Shell applicatif
│   │   │   ├── Sidebar.tsx           # §29 — Sidebar navigation
│   │   │   ├── TopBar.tsx            # §30 — TopBar contextuelle
│   │   │   └── nav-config.ts         # §31 — Tableau des routes + rôles
│   │   │
│   │   ├── ui/
│   │   │   ├── Button.tsx            # §33 — Variants de boutons
│   │   │   ├── Input.tsx             # §34 — Input, Select, Textarea
│   │   │   ├── Checkbox.tsx          # §34 — Checkbox + Switch
│   │   │   ├── Drawer.tsx            # §35 — Panneau latéral
│   │   │   ├── ConfirmModal.tsx      # §36 — Modal de confirmation
│   │   │   ├── Toast.tsx             # §37 — Toasts
│   │   │   ├── EmptyState.tsx        # §38 — États vides
│   │   │   ├── Skeleton.tsx          # §39 — Skeletons
│   │   │   └── CommandPalette.tsx    # §40 — Ctrl+K
│   │   │
│   │   ├── data/
│   │   │   ├── DataTable.tsx         # Tableau générique (Type A v2)
│   │   │   ├── PageHeader.tsx        # §32 — En-tête de page
│   │   │   ├── PageToolbar.tsx       # §32 — Barre de filtres
│   │   │   └── Pagination.tsx        # §32 — Pied de page
│   │   │
│   │   └── dossier/
│   │       ├── DossierHero.tsx       # Type C v2 — Hero band
│   │       ├── DossierTabs.tsx       # Type C v2 — Navigation onglets
│   │       └── InfoGrid.tsx          # Type C v2 — Grille d'infos
│   │
│   ├── pages/
│   │   ├── dashboard/
│   │   │   └── DashboardPage.tsx     # Type J v2
│   │   ├── eleves/
│   │   │   ├── ElevesPage.tsx        # Type A v2 (liste)
│   │   │   ├── EleveDossier.tsx      # Type C v2 (dossier)
│   │   │   └── EleveDrawer.tsx       # Type B v2 (formulaire)
│   │   ├── classes/
│   │   │   ├── ClassesPage.tsx
│   │   │   ├── ClasseDossier.tsx
│   │   │   └── ClasseDrawer.tsx
│   │   ├── notes/
│   │   │   └── SaisieNotesPage.tsx   # Type D
│   │   └── ...
│   │
│   ├── services/
│   │   ├── api.ts                    # Axios instance + intercepteurs JWT
│   │   ├── eleves.service.ts
│   │   ├── classes.service.ts
│   │   └── ...
│   │
│   ├── hooks/
│   │   ├── useToast.ts
│   │   ├── useConfirm.ts
│   │   ├── useAnneeActive.ts         # Année scolaire active (global)
│   │   └── usePermissions.ts         # Rôle utilisateur courant
│   │
│   ├── store/
│   │   └── auth.store.ts             # Token JWT + user info (Zustand)
│   │
│   └── styles/
│       ├── globals.css               # Tokens CSS §43
│       └── reset.css
```

---

## §45 · Checklist d'implémentation pour l'agent `NEW v6.0`

Ordre d'implémentation recommandé :

```
PHASE 1 — Fondations
  ☐ globals.css (tokens §43)
  ☐ AppShell.tsx (§28)
  ☐ Sidebar.tsx + nav-config.ts (§29, §31)
  ☐ TopBar.tsx (§30)
  ☐ auth.store.ts + login flow (JWT)
  ☐ api.ts (Axios + intercepteurs)
  ☐ useAnneeActive hook

PHASE 2 — Composants UI
  ☐ Button.tsx (§33)
  ☐ Input, Select, Checkbox, Switch (§34)
  ☐ Drawer.tsx (§35)
  ☐ ConfirmModal.tsx (§36)
  ☐ Toast.tsx + useToast hook (§37)
  ☐ EmptyState.tsx (§38)
  ☐ Skeleton.tsx (§39)
  ☐ CommandPalette.tsx (§40)

PHASE 3 — Composants de page
  ☐ PageHeader.tsx
  ☐ PageToolbar.tsx
  ☐ DataTable.tsx
  ☐ Pagination.tsx
  ☐ DossierHero.tsx + DossierTabs.tsx + InfoGrid.tsx

PHASE 4 — Modules (ordre recommandé)
  ☐ DashboardPage.tsx
  ☐ ElevesPage + EleveDossier + EleveDrawer
  ☐ ClassesPage + ClasseDossier + ClasseDrawer
  ☐ InscriptionsPage + InscriptionDrawer
  ☐ EnseignantsPage + EnseignantDossier
  ☐ CoursPage + CourDrawer
  ☐ SaisieNotesPage (Type D)
  ☐ AbsencesPage + AbsenceDrawer
  ☐ BulletinsPage
  ☐ ResultatsPage
  ☐ SeancesPage
  ☐ PaiementsPage + PaiementDrawer
  ☐ DepensesPage
  ☐ ComptesPage + CompteDrawer
  ☐ ParametresPage (années scolaires, trimestres)

PHASE 5 — Polish
  ☐ Raccourcis clavier (§42)
  ☐ Skeletons sur toutes les listes
  ☐ Empty states
  ☐ Gestion des erreurs API (toast error)
  ☐ Tests sur Tauri (desktop)
```

---

## Type K · Gestion Documentaire `NEW v6.0`

L'onglet **Documents** dans les dossiers (élève, enseignant) constitue la zone de gestion documentaire. Il présente les pièces jointes uploadées, permet d'en ajouter, de les prévisualiser et de les télécharger.

### Contexte d'usage

| Module | Documents attendus |
|---|---|
| Élève | Acte de naissance, carte d'identité, photo d'identité, attestation de scolarité, livret scolaire antérieur, fiche médicale |
| Enseignant | CV, diplômes, pièce d'identité, contrat, attestations |
| Classe | Emploi du temps imprimé, liste d'élèves |

### Layout de l'onglet Documents

```
┌────────────────────────────────────────────────────────────────┐
│ [+ Ajouter un document]           [≡ Liste] [⊞ Grille]  [🔍]  │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PIÈCES D'IDENTITÉ                                              │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ 📄           │  │ 📄           │                            │
│  │ CNI_Diallo   │  │ Acte_nais…   │                            │
│  │ PDF · 420 Ko │  │ JPG · 1.2 Mo │                            │
│  │ 12 jan. 2025 │  │ 12 jan. 2025 │                            │
│  │ [👁] [↓] [✕] │  │ [👁] [↓] [✕] │                            │
│  └──────────────┘  └──────────────┘                            │
│                                                                 │
│  PHOTOS                                                         │
│  ┌──────────────┐                                               │
│  │  [preview]   │                                               │
│  │ Photo_id.jpg │                                               │
│  │ JPG · 85 Ko  │                                               │
│  │ [👁] [↓] [✕] │                                               │
│  └──────────────┘                                               │
│                                                                 │
│  ┌── Zone de dépôt ────────────────────────────────────────┐   │
│  │   ⬆  Glisser-déposer un fichier ou cliquer pour         │   │
│  │      parcourir · PDF, JPG, PNG, DOCX · max 10 Mo        │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

### Toolbar de l'onglet Documents

```css
.doc-toolbar {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 12px 0 10px;
  border-bottom: 1px solid var(--border-soft);
  margin-bottom: 16px;
}
```

Contenu (gauche → droite) :
- `[+ Ajouter un document]` → `btn btn-primary btn-sm` → ouvre le Drawer d'upload
- Spacer
- Toggle Vue liste / Grille (`btn-icon` group)
- Recherche par nom (si > 5 documents)

### Carte de document (vue grille)

```css
.doc-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 0;
  overflow: hidden;
  width: 160px;
  cursor: pointer;
  transition: border-color 100ms, box-shadow 100ms;
}

.doc-card:hover {
  border-color: rgba(255, 255, 255, 0.20);
  box-shadow: var(--shadow-card);
}

/* Zone preview (haut de la carte) */
.doc-card-preview {
  height: 100px;
  background: var(--surface-2);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
}

/* Image réelle si disponible */
.doc-card-preview img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Icône type fichier si pas de preview image */
.doc-card-preview .doc-type-icon {
  font-size: 36px;
  opacity: 0.4;
}

/* Badge type de fichier (coin haut-droit) */
.doc-type-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  background: var(--surface-3);
  color: var(--ink-dim);
  font-size: 9px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: var(--radius-sm);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Couleurs par type */
.doc-type-badge.pdf   { background: rgba(224,112,127,.20); color: var(--danger); }
.doc-type-badge.jpg,
.doc-type-badge.png   { background: rgba(45,110,232,.20);  color: var(--action); }
.doc-type-badge.docx  { background: rgba(45,110,232,.15);  color: #6fa8dc; }

/* Infos (bas de la carte) */
.doc-card-body {
  padding: 9px 10px 6px;
}

.doc-card-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.doc-card-meta {
  font-size: 10.5px;
  color: var(--ink-faint);
  display: flex;
  justify-content: space-between;
}

/* Actions (visibles au hover) */
.doc-card-actions {
  display: flex;
  gap: 2px;
  padding: 4px 6px;
  border-top: 1px solid var(--border-soft);
  opacity: 0;
  transition: opacity 100ms;
}

.doc-card:hover .doc-card-actions { opacity: 1; }

.doc-action-btn {
  width: 26px;
  height: 26px;
  border-radius: var(--radius-sm);
  border: none;
  background: none;
  cursor: pointer;
  color: var(--ink-faint);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  transition: background 80ms, color 80ms;
}
.doc-action-btn:hover { background: var(--surface-2); color: var(--ink); }
.doc-action-btn.danger:hover { color: var(--danger); }
```

### Ligne de document (vue liste)

```css
.doc-list-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-soft);
  cursor: pointer;
  transition: background 60ms;
  border-radius: var(--radius-md);
}

.doc-list-row:hover { background: var(--surface-2); padding: 8px 8px; margin: 0 -8px; }

.doc-list-icon {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-md);
  background: var(--surface-2);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
}

.doc-list-info { flex: 1; overflow: hidden; }
.doc-list-name { font-size: 13px; font-weight: 500; color: var(--ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.doc-list-meta { font-size: 11px; color: var(--ink-faint); margin-top: 1px; }

.doc-list-actions {
  display: flex;
  gap: 3px;
  opacity: 0;
  transition: opacity 100ms;
}
.doc-list-row:hover .doc-list-actions { opacity: 1; }
```

### Groupes de documents par catégorie

```tsx
const DOC_CATEGORIES: Record<string, { label: string; icon: string }> = {
  identite:      { label: "Pièces d'identité", icon: "IdCard" },
  photo:         { label: "Photos",             icon: "Image" },
  naissance:     { label: "Actes de naissance", icon: "FileText" },
  scolaire:      { label: "Documents scolaires", icon: "GraduationCap" },
  medical:       { label: "Documents médicaux", icon: "HeartPulse" },
  administratif: { label: "Administratif",      icon: "FolderOpen" },
  autre:         { label: "Autres",             icon: "File" },
}
```

### Zone de dépôt (Upload Zone)

```css
.upload-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius-lg);
  padding: 28px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: border-color 150ms, background 150ms;
  text-align: center;
  background: transparent;
  margin-top: 16px;
}

.upload-zone:hover,
.upload-zone.drag-over {
  border-color: var(--action);
  background: var(--action-w);
}

.upload-zone-icon {
  color: var(--ink-faint);
  margin-bottom: 4px;
}

.upload-zone-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--ink-dim);
}

.upload-zone-sub {
  font-size: 11.5px;
  color: var(--ink-faint);
}

/* Barre de progression upload */
.upload-progress {
  width: 100%;
  height: 3px;
  background: var(--surface-3);
  border-radius: 2px;
  overflow: hidden;
  margin-top: 8px;
}

.upload-progress-bar {
  height: 100%;
  background: var(--action);
  border-radius: 2px;
  transition: width 200ms ease;
}
```

### Drawer d'upload — Ajouter un document

```
Titre : Ajouter un document

  [Nom du document *]
  ex : CNI_Aminata_Diallo

  [Catégorie * ▾]
  Pièces d'identité / Photos / Actes de naissance / ...

  [Zone de dépôt — glisser ou parcourir]
  PDF, JPG, PNG, DOCX · max 10 Mo

  [Commentaire (optionnel)]

Footer : [Annuler]  [Enregistrer]
```

---

## Type L · Visionneuse de Document — Plein Écran `mis à jour v6.0`

La visionneuse s'ouvre en **overlay plein écran** qui recouvre l'intégralité de l'application (sidebar incluse). Elle est dédiée à la lecture de documents et reproduit l'expérience d'un vrai lecteur de fichiers (comparable à macOS Preview ou Adobe Acrobat Reader).

### Décision de conception

L'ancien panneau latéral (520px à droite) était insuffisant : il compressait le contenu principal, manquait de place pour les tableaux larges des documents scolaires (bulletins à 18+ colonnes, fiches de suivi DEF à 23 colonnes) et rompait la continuité de lecture. Le plein écran supprime toute distraction et donne au document la place qu'il mérite.

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ OVERLAY (position:absolute; inset:0; z-index:50; bg:#0a0b0e)     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ TOOLBAR (52px, --surface, border-bottom)                 │   │
│  │ [← Retour]  [divider]  [📄 Bulletin de notes 2nd cycle] │   │
│  │               [−][100%][+]       [🖨] [↓] [⤢]           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ZONE DE DOCUMENT (flex:1, overflow:auto, bg:#0a0b0e)     │   │
│  │                                                          │   │
│  │         ╔══════════════════════════════╗                 │   │
│  │         ║   DOCUMENT — fond blanc      ║                 │   │
│  │         ║   Rendu HTML ou PDF          ║                 │   │
│  │         ║   (794px largeur, A4)        ║                 │   │
│  │         ║   box-shadow: deep           ║                 │   │
│  │         ║   ─────────────────────────  ║                 │   │
│  │         ║   [page 2 si multi-pages]    ║                 │   │
│  │         ╚══════════════════════════════╝                 │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ BARRE DE STATUT (42px, --surface, border-top)           │   │
│  │  📄 Bulletin de notes — 2nd cycle · 8.2 Ko   Page 1/1   │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Dimensions

| Propriété | Valeur |
|---|---|
| Couverture | `position: absolute; inset: 0` (couvre sidebar + topbar) |
| Z-index | 50 |
| Fond de la zone doc | `#0a0b0e` (plus sombre que `--base`) |
| Toolbar height | 52px |
| Status bar height | 42px |
| Largeur papier document | 794px (A4 à 96dpi) |
| Niveaux de zoom | 60%, 75%, 90%, **100%**, 115%, 130%, 150%, 175%, 200% |
| Ouverture | Instantané (pas de transition — plein écran est immédiat) |
| Fermeture | Bouton `← Retour`, touche `Escape` |

> **Pas de panneau latéral de miniatures** pour les documents HTML (pas de pagination native). Pour les PDF multi-pages, ajouter un panneau gauche escamotable de thumbnails (§47 — pdfjs-dist).

> **Le document n'est jamais un iframe** pour les documents HTML internes — le contenu HTML est injecté directement dans un `<div class="vpaper">` avec une classe CSS d'isolation. Ceci évite les restrictions cross-origin de l'environnement Tauri avec srcdoc.

### Structure JSX

```tsx
<div className="viewer-shell">
  {/* Contenu principal compressé */}
  <div className="viewer-main" style={{ flex: 1, minWidth: 0 }}>
    {children}
  </div>

  {/* Visionneuse */}
  {viewerOpen && (
    <div className="doc-viewer">
      <div className="doc-viewer-header">
        <div className="doc-viewer-title">
          <FileIcon type={doc.type} size={14} />
          <span>{doc.nom}</span>
        </div>
        <div className="doc-viewer-actions">
          <button className="btn-icon" onClick={handleDownload} title="Télécharger">
            <Download size={14} />
          </button>
          <button className="btn-icon" onClick={handlePrint} title="Imprimer">
            <Printer size={14} />
          </button>
          <button className="btn-icon" onClick={closeViewer} title="Fermer (Esc)">
            <X size={14} />
          </button>
        </div>
      </div>

      <div className="doc-viewer-body">
        {doc.type === 'pdf'
          ? <PDFRenderer url={doc.url} />
          : <ImageRenderer url={doc.url} />
        }
      </div>

      <div className="doc-viewer-footer">
        <span className="doc-viewer-pages">Page {page} / {totalPages}</span>
        <div className="doc-viewer-nav">
          <button className="btn-icon btn-sm" onClick={prevPage} disabled={page === 1}>
            <ChevronLeft size={13} />
          </button>
          <button className="btn-icon btn-sm" onClick={nextPage} disabled={page === totalPages}>
            <ChevronRight size={13} />
          </button>
        </div>
        <div className="doc-viewer-zoom">
          <button className="btn-icon btn-sm" onClick={zoomOut}>
            <ZoomOut size={13} />
          </button>
          <span className="zoom-level">{zoom}%</span>
          <button className="btn-icon btn-sm" onClick={zoomIn}>
            <ZoomIn size={13} />
          </button>
        </div>
      </div>
    </div>
  )}
</div>
```

### CSS de la visionneuse

```css
/* Shell conteneur (flex row) */
.viewer-shell {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* Panneau visionneuse */
.doc-viewer {
  width: 520px;
  min-width: 520px;
  background: var(--surface);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  transition: width 220ms cubic-bezier(.25, 0, 0, 1),
              min-width 220ms cubic-bezier(.25, 0, 0, 1);
  overflow: hidden;
}

/* Header de la visionneuse */
.doc-viewer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  height: 44px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  gap: 10px;
}

.doc-viewer-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--ink);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  flex: 1;
}

.doc-viewer-actions {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

/* Zone de rendu (scrollable) */
.doc-viewer-body {
  flex: 1;
  overflow: auto;
  background: var(--base);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 16px;
}

/* Footer de navigation */
.doc-viewer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 14px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
  gap: 10px;
}

.doc-viewer-pages {
  font-size: 11.5px;
  color: var(--ink-faint);
  font-family: var(--font-mono);
  min-width: 70px;
}

.doc-viewer-nav {
  display: flex;
  gap: 3px;
}

.doc-viewer-zoom {
  display: flex;
  align-items: center;
  gap: 4px;
}

.zoom-level {
  font-size: 11.5px;
  color: var(--ink-dim);
  font-family: var(--font-mono);
  min-width: 36px;
  text-align: center;
}
```

### Rendu PDF — `<PDFRenderer>`

```tsx
// Librairie : pdfjs-dist (inclus dans Vite/Tauri sans config serveur externe)
import * as pdfjsLib from 'pdfjs-dist'
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker?url'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker

interface PDFRendererProps {
  url: string          // URL blob:// ou chemin local via Tauri
  page: number
  zoom: number         // 0.5 → 2.0
  onTotalPages: (n: number) => void
}

export function PDFRenderer({ url, page, zoom, onTotalPages }: PDFRendererProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    let cancelled = false

    async function render() {
      const pdf = await pdfjsLib.getDocument(url).promise
      onTotalPages(pdf.numPages)

      const pdfPage = await pdf.getPage(page)
      const viewport = pdfPage.getViewport({ scale: zoom })

      const canvas = canvasRef.current
      if (!canvas || cancelled) return

      canvas.width  = viewport.width
      canvas.height = viewport.height

      await pdfPage.render({
        canvasContext: canvas.getContext('2d')!,
        viewport,
      }).promise
    }

    render()
    return () => { cancelled = true }
  }, [url, page, zoom])

  return (
    <canvas
      ref={canvasRef}
      style={{
        display: 'block',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 2px 12px rgba(0,0,0,.5)',
        maxWidth: '100%',
      }}
    />
  )
}
```

### Rendu Image — `<ImageRenderer>`

```tsx
interface ImageRendererProps {
  url: string
  zoom: number
}

export function ImageRenderer({ url, zoom }: ImageRendererProps) {
  return (
    <img
      src={url}
      alt="Document"
      style={{
        transform: `scale(${zoom})`,
        transformOrigin: 'top center',
        borderRadius: 'var(--radius-md)',
        boxShadow: '0 2px 12px rgba(0,0,0,.5)',
        maxWidth: '100%',
        display: 'block',
        transition: 'transform 150ms ease',
      }}
    />
  )
}
```

### Niveaux de zoom

```ts
const ZOOM_LEVELS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
const ZOOM_DEFAULT = 1.0

function zoomIn(current: number)  { return ZOOM_LEVELS[ZOOM_LEVELS.indexOf(current) + 1] ?? current }
function zoomOut(current: number) { return ZOOM_LEVELS[ZOOM_LEVELS.indexOf(current) - 1] ?? current }
```

### Raccourcis clavier dans la visionneuse

| Raccourci | Action |
|---|---|
| `Escape` | Fermer la visionneuse |
| `ArrowLeft` / `ArrowRight` | Page précédente / suivante |
| `+` / `-` | Zoom in / out |
| `Ctrl+P` | Imprimer |
| `Ctrl+S` | Télécharger |

---

## §46 · Implémentation Technique — Documents `NEW v6.0`

### Endpoints API Backend

```
# Récupérer les documents d'une entité
GET  /api/documents/?entite_type=eleve&entite_id={id}
     → DocumentList[]

# Uploader un document
POST /api/documents/
     Content-Type: multipart/form-data
     Body: { fichier, nom, categorie, entite_type, entite_id }
     → Document

# Télécharger un fichier
GET  /api/documents/{id}/fichier
     → fichier binaire (Content-Disposition: attachment)

# Stream / prévisualisation inline
GET  /api/documents/{id}/preview
     → fichier binaire (Content-Disposition: inline)

# Modifier les métadonnées
PATCH /api/documents/{id}
      Body: { nom?, categorie? }
      → Document

# Supprimer
DELETE /api/documents/{id}
       → 204 No Content
```

### Schéma Pydantic (Backend)

```python
class DocumentBase(BaseModel):
    nom: str                         # Nom affiché dans l'UI
    categorie: str                   # "identite" | "photo" | etc.
    entite_type: str                 # "eleve" | "enseignant"
    entite_id: int

class DocumentCreate(DocumentBase):
    pass                             # Le fichier arrive via UploadFile

class DocumentRead(DocumentBase):
    id: int
    nom_fichier_original: str        # Nom d'origine du fichier
    type_mime: str                   # "application/pdf" | "image/jpeg" | etc.
    taille_octets: int
    created_at: datetime
    url_preview: str                 # /api/documents/{id}/preview
    url_download: str                # /api/documents/{id}/fichier

    model_config = ConfigDict(from_attributes=True)
```

### Modèle SQLAlchemy

```python
class Document(Base):
    __tablename__ = "documents"

    id                   = Column(Integer, primary_key=True)
    nom                  = Column(String(200), nullable=False)
    categorie            = Column(String(50), nullable=False, default="autre")
    entite_type          = Column(String(20), nullable=False)   # "eleve" | "enseignant"
    entite_id            = Column(Integer, nullable=False)
    nom_fichier_original = Column(String(255), nullable=False)
    nom_fichier_stocke   = Column(String(255), nullable=False, unique=True)
    type_mime            = Column(String(100), nullable=False)
    taille_octets        = Column(Integer, nullable=False)
    chemin_stockage      = Column(String(500), nullable=False)  # chemin absolu sur disque
    created_at           = Column(DateTime, default=func.now())
    created_by           = Column(Integer, ForeignKey("utilisateurs.id"))
```

### Router FastAPI

```python
import uuid, os, shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "./uploads/documents")
MAX_SIZE_BYTES = 10 * 1024 * 1024   # 10 Mo
ALLOWED_MIME = {
    "application/pdf",
    "image/jpeg", "image/png", "image/webp",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.get("/", response_model=list[DocumentRead])
def list_documents(
    entite_type: str,
    entite_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return db.query(Document).filter(
        Document.entite_type == entite_type,
        Document.entite_id   == entite_id,
    ).order_by(Document.created_at.desc()).all()


@router.post("/", response_model=DocumentRead, status_code=201)
async def upload_document(
    nom: str,
    categorie: str,
    entite_type: str,
    entite_id: int,
    fichier: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # Validation type MIME
    if fichier.content_type not in ALLOWED_MIME:
        raise HTTPException(415, "Type de fichier non autorisé.")

    # Validation taille (lecture streaming)
    content = await fichier.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(413, "Fichier trop volumineux (max 10 Mo).")

    # Nom unique sur disque
    ext = os.path.splitext(fichier.filename)[1].lower()
    nom_stocke = f"{uuid.uuid4().hex}{ext}"
    chemin = os.path.join(UPLOAD_DIR, entite_type, str(entite_id), nom_stocke)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)

    with open(chemin, "wb") as f:
        f.write(content)

    doc = Document(
        nom=nom,
        categorie=categorie,
        entite_type=entite_type,
        entite_id=entite_id,
        nom_fichier_original=fichier.filename,
        nom_fichier_stocke=nom_stocke,
        type_mime=fichier.content_type,
        taille_octets=len(content),
        chemin_stockage=chemin,
        created_by=current_user.id,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{doc_id}/preview")
def preview_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404)
    return FileResponse(
        doc.chemin_stockage,
        media_type=doc.type_mime,
        headers={"Content-Disposition": "inline"},
    )


@router.get("/{doc_id}/fichier")
def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404)
    return FileResponse(
        doc.chemin_stockage,
        media_type=doc.type_mime,
        filename=doc.nom_fichier_original,
        headers={"Content-Disposition": f'attachment; filename="{doc.nom_fichier_original}"'},
    )


@router.patch("/{doc_id}", response_model=DocumentRead)
def update_document(
    doc_id: int,
    payload: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, field, value)
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/{doc_id}", status_code=204)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404)
    # Supprimer le fichier physique
    if os.path.exists(doc.chemin_stockage):
        os.remove(doc.chemin_stockage)
    db.delete(doc)
    db.commit()
```

### Service Frontend — `documents.service.ts`

```ts
import api from './api'

export interface Document {
  id: number
  nom: string
  categorie: string
  entite_type: string
  entite_id: number
  nom_fichier_original: string
  type_mime: string
  taille_octets: number
  created_at: string
  url_preview: string
  url_download: string
}

export interface UploadDocumentPayload {
  nom: string
  categorie: string
  entite_type: 'eleve' | 'enseignant'
  entite_id: number
  fichier: File
}

export const documentsService = {
  list(entite_type: string, entite_id: number) {
    return api.get<Document[]>('/documents/', {
      params: { entite_type, entite_id },
    })
  },

  upload({ fichier, ...params }: UploadDocumentPayload) {
    const form = new FormData()
    form.append('fichier', fichier)
    Object.entries(params).forEach(([k, v]) => form.append(k, String(v)))
    return api.post<Document>('/documents/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        const pct = Math.round((e.loaded * 100) / (e.total ?? 1))
        // dispatcher vers un state de progression
        console.log(`Upload : ${pct}%`)
      },
    })
  },

  getPreviewUrl(docId: number) {
    return `${api.defaults.baseURL}/documents/${docId}/preview`
  },

  getDownloadUrl(docId: number) {
    return `${api.defaults.baseURL}/documents/${docId}/fichier`
  },

  update(docId: number, payload: Partial<Pick<Document, 'nom' | 'categorie'>>) {
    return api.patch<Document>(`/documents/${docId}`, payload)
  },

  delete(docId: number) {
    return api.delete(`/documents/${docId}`)
  },
}
```

### Hook `useDocuments`

```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsService, UploadDocumentPayload } from '../services/documents.service'
import { useToast } from './useToast'

export function useDocuments(entiteType: string, entiteId: number) {
  const qc = useQueryClient()
  const toast = useToast()
  const key = ['documents', entiteType, entiteId]

  const query = useQuery({
    queryKey: key,
    queryFn: () => documentsService.list(entiteType, entiteId).then(r => r.data),
    enabled: !!entiteId,
  })

  const upload = useMutation({
    mutationFn: (payload: UploadDocumentPayload) =>
      documentsService.upload(payload).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key })
      toast.success('Document ajouté', 'Le fichier a été enregistré.')
    },
    onError: (err: any) => {
      toast.error('Erreur upload', err.response?.data?.detail ?? 'Impossible d\'enregistrer le fichier.')
    },
  })

  const remove = useMutation({
    mutationFn: (docId: number) => documentsService.delete(docId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: key })
      toast.success('Document supprimé')
    },
  })

  return { ...query, upload, remove }
}
```

### Hook `useDocumentViewer`

```ts
import { useState, useEffect, useCallback } from 'react'

export function useDocumentViewer() {
  const [doc, setDoc] = useState<Document | null>(null)
  const [page, setPage]   = useState(1)
  const [total, setTotal] = useState(1)
  const [zoom, setZoom]   = useState(1.0)

  const ZOOM_LEVELS = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

  const open = useCallback((document: Document) => {
    setDoc(document)
    setPage(1)
    setZoom(1.0)
  }, [])

  const close = useCallback(() => {
    setDoc(null)
    setPage(1)
  }, [])

  const zoomIn  = () => setZoom(z => ZOOM_LEVELS[ZOOM_LEVELS.indexOf(z) + 1] ?? z)
  const zoomOut = () => setZoom(z => ZOOM_LEVELS[ZOOM_LEVELS.indexOf(z) - 1] ?? z)
  const nextPage = () => setPage(p => Math.min(p + 1, total))
  const prevPage = () => setPage(p => Math.max(p - 1, 1))

  // Raccourcis clavier
  useEffect(() => {
    if (!doc) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape')       close()
      if (e.key === 'ArrowRight')   nextPage()
      if (e.key === 'ArrowLeft')    prevPage()
      if (e.key === '+')            zoomIn()
      if (e.key === '-')            zoomOut()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [doc, page, total, zoom])

  return {
    doc, page, total, zoom,
    open, close,
    setTotal,
    zoomIn, zoomOut,
    nextPage, prevPage,
    isOpen: !!doc,
  }
}
```

---

## §47 · Intégration Tauri — Fichiers locaux `NEW v6.0`

Tauri permet d'accéder directement au système de fichiers local sans passer par un serveur externe. Les documents sont stockés sur la machine serveur et servis par le backend FastAPI.

### Variables d'environnement à configurer

```bash
# .env (sur le serveur)
UPLOAD_DIR=/var/aureole/uploads    # dossier de stockage des fichiers
BACKEND_URL=http://192.168.1.10:8000

# .env (sur les postes clients Tauri)
VITE_API_BASE_URL=http://192.168.1.10:8000/api
```

### Configuration CORS pour les fichiers

```python
# main.py — s'assurer que les routes /documents/*/preview et /fichier
# passent par la config CORS et transmettent les headers JWT

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "tauri://localhost").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],   # ← nécessaire pour le nom de fichier en download
)
```

### Flux de prévisualisation depuis Tauri

```
1. Utilisateur clique [👁 Prévisualiser] sur une carte document
2. Frontend → GET /api/documents/{id}/preview
   Headers: Authorization: Bearer {token}
3. Backend → FileResponse (streaming du fichier depuis le disque)
4. Frontend → crée un URL.createObjectURL(blob) temporaire
5. PDFRenderer / ImageRenderer charge l'URL blob://...
6. À la fermeture du viewer → URL.revokeObjectURL(blobUrl)
```

```ts
// Charger un doc pour preview (évite d'exposer le chemin disque dans l'URL)
async function loadPreviewBlob(docId: number): Promise<string> {
  const response = await api.get(`/documents/${docId}/preview`, {
    responseType: 'blob',
  })
  const blob = new Blob([response.data], { type: response.headers['content-type'] })
  return URL.createObjectURL(blob)
}
```

### Limites et formats acceptés

| Type | MIME | Extension | Max |
|---|---|---|---|
| PDF | `application/pdf` | `.pdf` | 10 Mo |
| Image JPEG | `image/jpeg` | `.jpg`, `.jpeg` | 10 Mo |
| Image PNG | `image/png` | `.png` | 10 Mo |
| Image WebP | `image/webp` | `.webp` | 10 Mo |
| Word | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | `.docx` | 10 Mo |

> Les fichiers `.docx` ne peuvent pas être prévisualisés inline — seul le téléchargement est proposé. Afficher le bouton [👁] désactivé avec tooltip "Prévisualisation non disponible pour ce format".

---

## §48 · Composants React — Récapitulatif Documents `NEW v6.0`

```
src/components/documents/
├── DocumentsTab.tsx          # Onglet complet (Type K) — s'insère dans DossierTabs
├── DocumentGrid.tsx          # Grille de cartes de documents
├── DocumentList.tsx          # Liste ligne par ligne
├── DocumentCard.tsx          # Carte individuelle (vue grille)
├── DocumentRow.tsx           # Ligne individuelle (vue liste)
├── UploadZone.tsx            # Zone glisser-déposer
├── UploadDrawer.tsx          # Drawer d'upload (formulaire)
├── DocumentViewer.tsx        # Panneau visionneuse (Type L)
├── PDFRenderer.tsx           # Rendu PDF via pdfjs-dist
├── ImageRenderer.tsx         # Rendu image zoomable
└── index.ts                  # Re-exports
```

### `<DocumentsTab>` — interface publique

```tsx
interface DocumentsTabProps {
  entiteType: 'eleve' | 'enseignant'
  entiteId: number
  readOnly?: boolean           // désactive upload/suppression (ex : role comptable)
}

export function DocumentsTab({ entiteType, entiteId, readOnly = false }: DocumentsTabProps) {
  const { data: docs = [], isLoading, upload, remove } = useDocuments(entiteType, entiteId)
  const viewer = useDocumentViewer()
  const [view, setView]         = useState<'grid' | 'list'>('grid')
  const [uploadOpen, setUploadOpen] = useState(false)

  // Grouper par catégorie
  const grouped = groupBy(docs, d => d.categorie)

  if (isLoading) return <DocumentsSkeleton />

  return (
    <div className="documents-tab">
      <div className="doc-toolbar">
        {!readOnly && (
          <button className="btn btn-primary btn-sm" onClick={() => setUploadOpen(true)}>
            <Plus size={13} /> Ajouter un document
          </button>
        )}
        <div className="toolbar-spacer" />
        <ViewToggle value={view} onChange={setView} />
      </div>

      {docs.length === 0
        ? <EmptyState icon={Files} title="Aucun document" subtitle="Aucune pièce jointe pour ce dossier." />
        : Object.entries(grouped).map(([cat, catDocs]) => (
            <div key={cat} className="doc-category-section">
              <div className="doc-category-title">
                {DOC_CATEGORIES[cat]?.label ?? 'Autres'}
              </div>
              {view === 'grid'
                ? <DocumentGrid docs={catDocs} onPreview={viewer.open} onDelete={!readOnly ? remove.mutate : undefined} />
                : <DocumentList docs={catDocs} onPreview={viewer.open} onDelete={!readOnly ? remove.mutate : undefined} />
              }
            </div>
          ))
      }

      {!readOnly && docs.length > 0 && (
        <UploadZone onFile={file => setUploadOpen(true)} />
      )}

      {uploadOpen && (
        <UploadDrawer
          entiteType={entiteType}
          entiteId={entiteId}
          onSubmit={upload.mutate}
          onClose={() => setUploadOpen(false)}
          isLoading={upload.isPending}
        />
      )}
    </div>
  )
}
```

---

## Mise à jour §45 · Checklist — Documents

Ajouter à la **PHASE 4** de la checklist d'implémentation :

```
PHASE 4 (suite) — Documents
  ☐ Modèle SQLAlchemy Document + migration
  ☐ Router FastAPI /api/documents/ (list, upload, preview, download, patch, delete)
  ☐ Variable UPLOAD_DIR + création du dossier au démarrage
  ☐ Expose Content-Disposition dans les headers CORS
  ☐ documents.service.ts (frontend)
  ☐ useDocuments hook (react-query)
  ☐ useDocumentViewer hook (état + raccourcis)
  ☐ UploadZone.tsx (drag & drop)
  ☐ UploadDrawer.tsx (formulaire)
  ☐ DocumentCard.tsx + DocumentRow.tsx
  ☐ DocumentGrid.tsx + DocumentList.tsx
  ☐ PDFRenderer.tsx (pdfjs-dist)
  ☐ ImageRenderer.tsx
  ☐ DocumentViewer.tsx (panneau Type L)
  ☐ DocumentsTab.tsx (intégration dans DossierTabs)
  ☐ Intégrer l'onglet Documents dans EleveDossier et EnseignantDossier
  ☐ Bloquer la preview .docx (bouton désactivé + tooltip)
  ☐ Nettoyage des blob URLs à la fermeture du viewer
```

---

*Fin du document — Auréole Design System v6.0*
*v6.1 prévu : exports PDF bulletins, mode impression, Clôture d'année UI.*
