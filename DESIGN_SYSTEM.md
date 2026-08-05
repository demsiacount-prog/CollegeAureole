# Collège Auréole — Système de Design v3

> Système conçu pour un logiciel de gestion scolaire utilisé quotidiennement, sur poste fixe, par du personnel non technique (secrétariat, comptabilité, direction). Chaque décision de couleur, espacement et composant sert la **vitesse de lecture**, la **fiabilité de saisie** et la **clarté de l'information**. L'esthétique suit la fonction, jamais l'inverse. Ce document est la source de vérité visuelle.

---

## 01 — Palette & Tokens CSS

Neutre par défaut — la couleur = information. 90 % de l'écran reste en tons gris. **Un seul badge coloré par ligne de tableau.**

### Fonds & surfaces
| Token | Hex | Usage |
|---|---|---|
| `--color-base` | `#F5F6F8` | Fond application |
| `--color-surface` | `#FFFFFF` | Carte / panneau |
| `--color-surface-alt` | `#F9FAFB` | Ligne paire / en-tête `th` |
| `--color-border` | `#E1E5EC` | Bordure par défaut |
| `--color-border-strong` | `#C5CCD9` | Bordure input / emphase |

### Échelle de texte (ink)
| Token | Hex | Usage |
|---|---|---|
| `--color-ink` | `#111827` | Texte principal |
| `--color-ink-secondary` | `#374151` | Texte secondaire |
| `--color-ink-dim` | `#6B7280` | Labels, descriptions |
| `--color-ink-faint` | `#9CA3AF` | Métadonnées, périodes |
| `--color-ink-disabled` | `#D1D5DB` | Champs désactivés |

### Marque & interaction
| Token | Hex | Usage |
|---|---|---|
| `--color-halo` | `#C9A84C` | Focus clavier & nav actif |
| `--color-halo-wash` | `#FEF9EC` | Fond item actif sidebar |
| `--color-brand` | `#2D6EE8` | Action primaire |
| `--color-brand-dark` | `#1E58C4` | Hover / pressed |
| `--color-brand-wash` | `#EBF2FF` | Sélection, fond focus |
| `--color-brand-border` | `#BFDBFE` | Bordure focus wash |

### Couleurs sémantiques (un seul badge coloré par ligne)
| Token | Couleur / Wash | Usage |
|---|---|---|
| `--color-success` / `-wash` | `#15803D` · `#F0FDF4` | Présent, validé, payé |
| `--color-warning` / `-wash` | `#D97706` · `#FFFBEB` | Retard, partiel, alerte |
| `--color-danger` / `-wash` | `#DC2626` · `#FEF2F2` | Absent, impayé, erreur |
| `--color-info` / `-wash` | `#0284C7` · `#F0F9FF` | Information, dispensé |

### Couleurs de rôle (badges profils uniquement)
| Token | Couleur / Wash | Rôle |
|---|---|---|
| `--color-role-student` | `#6D28D9` · `#F5F3FF` | Élève |
| `--color-role-teacher` | `#0E7490` · `#ECFEFF` | Enseignant |
| `--color-role-admin` | `#BE123C` · `#FFF1F2` | Administration |
| `--color-role-staff` | `#166534` · `#F0FDF4` | Personnel |

### Polices
- **Fraunces** (serif) — display, réservé
- **Inter** (sans) — corps de texte, UI
- **IBM Plex Mono** (mono) — IDs, montants, notes

### Rayons de bordure
`--r-sm: 4px` · `--r: 6px` · `--r-md: 8px` · `--r-lg: 12px` · `--r-xl: 16px`

---

## 02 — Typographie

4 niveaux max par écran. **Fraunces réservé à 2 emplacements fixes** + valeur KPI dashboard (une seule occurrence par page).

| Style | Spécification | Usage |
|---|---|---|
| Fraunces 600 · text-3xl | 30px / 1.2 · tracking -0.02em | KPI dashboard uniquement |
| Inter 600 · text-2xl | 24px / 1.3 · tracking -0.02em | Titre de page — h1 |
| Inter 500 · text-[15px] | 15px / 1.6 · tracking 0 | Titre carte / section |
| Inter 400 · text-sm | 14px / 1.5 · tracking 0 | Corps, valeurs tableau |
| Inter 400 · text-xs | 12px / 1.4 · tracking 0 | Métadonnées, labels |
| IBM Plex Mono 400 | 12–13px · tracking 0 | IDs, notes, montants |

### Règle d'emphase inline dans un tableau
Exemple : `Dupont Martin — 3ème B — 2024-0847 — [Présent]`

- `font-medium` **uniquement** pour le nom (identité primaire)
- `mono` pour l'ID structuré
- badge pour le statut
- pas d'autres emphases sur la même ligne
- **jamais** de `font-bold` dans l'UI

---

## 03 — Espacement, Grille & Densité

Base **4px**. Hauteur de ligne tableau : **36–40px** (compacte) ou **48px** (confortable). Conteneur max **1400px**. Sidebar **240px**.

### Échelle d'espacement
| Token | Valeur | Usage |
|---|---|---|
| `space-1` | 4px | Gap icône/texte, padding badge |
| `space-2` | 8px | Gap éléments inline, gap boutons, items nav |
| `space-3` | 12px | Padding cellule tableau, gap chips |
| `space-4` | 16px | Padding card `p-4`, gap champs formulaire |
| `space-5` | 20px | Padding page horizontal intérieur, panel |
| `space-6` | 24px | Padding card large, gap entre KPIs |
| `space-8` | 32px | Padding page `py-8`, margin entre sections |
| `space-10` | 40px | Padding page `px-10`, gap majeur |

### Densité — hauteur de ligne
- **Compacte — 36px** : défaut pour la saisie intensive
- **Confortable — 48px** : toggle utilisateur, mémorisé par utilisateur
- Recommandé pour les tableaux de 50+ lignes (élèves, paiements, absences)
- Ne jamais descendre sous **32px**

### Grille & conteneur
- Sidebar : **240px** (56px réduite)
- Conteneur max : **1400px**
- Padding page : `px-10 py-8` (40/32px)
- KPI grid : 4 × 1fr, gap 12px
- Formulaire : 2 × 1fr, gap 16px
- Border radius : 4 / 6 / 8 / 12 / 16px

---

## 04 — Contraste & Accessibilité

WCAG **AA minimum** (4.5:1 texte normal, 3:1 texte large). Focus visible : anneau halo doré, outline 2px. Navigation clavier complète.

| Combinaison | Ratio | WCAG | Usage |
|---|---|---|---|
| `#111827` sur `#FFFFFF` | 18.1:1 | AAA | Texte principal sur surface |
| `#374151` sur `#FFFFFF` | 10.7:1 | AAA | Texte secondaire sur surface |
| `#6B7280` sur `#FFFFFF` | 5.1:1 | AA | Labels et descriptions |
| `#FFFFFF` sur `#2D6EE8` | 4.7:1 | AA | Bouton primaire |
| `#15803D` sur `#F0FDF4` | 5.3:1 | AA | Badge succès sur fond wash |
| `#DC2626` sur `#FEF2F2` | 4.8:1 | AA | Badge danger sur fond wash |
| `#D97706` sur `#FFFBEB` | 4.6:1 | AA | Badge warning sur fond wash |

### Focus clavier — anneau halo (seul usage de l'effet doré)
```css
outline: 2px solid #C9A84C;
outline-offset: 2px;
```
- Identique pour le focus clavier et l'item actif de la sidebar
- Le halo doré ne s'utilise nulle part ailleurs
- Sidebar : `box-shadow: inset 2px 0 0 var(--color-halo)` sur le bord gauche

### Raccourcis clavier
| Touche | Action |
|---|---|
| `/` ou `Ctrl+K` | Recherche globale |
| Flèches | Navigation dans les tableaux |
| `Entrée` | Ouvrir le détail |
| `Échap` | Fermer le drawer |

---

## 05 — Composants

Toujours vérifier `src/components/ui/` avant toute création. Toute variante manquante s'ajoute au composant partagé, jamais en doublon local.

### Boutons
**Variantes** : primaire (`btn-p`), secondaire (`btn-s`), danger (`btn-d`), fantôme (`btn-g`), icône seul (`btn-ico`)
**Tailles** : `btn-sm`, standard, `btn-lg`
**Désactivé** : `opacity: 0.42; pointer-events: none`

### Badges
- **Présence** : Présent (ok) · Absent (danger) · Retard (warning) · Dispensé (info) · Non renseigné (neutre)
- **Paiement** : Payé (ok) · Partiel (warning) · Impayé (danger) · En attente (info)
- **Rôles** : Élève · Enseignant · Administration · Personnel
- Un seul badge coloré par ligne de tableau. Les `-wash` sont utilisés en fond, jamais pour du texte seul.

### Chips (filtres actifs retirables)
Affichés sous la barre de recherche, visibles en permanence quand ≥ 1 filtre est actif — pas de filtre caché dans un menu fermé.

### Formulaires
- Validation **inline au `blur`** — l'erreur apparaît sous le champ dès que l'utilisateur le quitte
- Bandeau d'erreur global réservé aux erreurs API sans champ cible
- Champs groupés par paires (`grid-cols-2, gap-4`)
- Distinction `ink-faint` (non renseigné) vs `ink-disabled` (non modifiable)

### Toast (retour d'action)
- Position : bas à droite, auto-disparaissant en **4s**
- Suppression : action « Annuler » visible pendant **5s**
- **Jamais** de `confirm()` navigateur, jamais de modal bloquante pour une confirmation de succès
- Ton neutre et factuel : « Élève créé avec succès. » — pas d'exclamation, pas d'enjouement

### Fil d'Ariane (breadcrumb)
Dès 2+ niveaux de navigation. Le compteur entre parenthèses (ex. « Notes & évaluations (12) ») oriente la lecture avant le clic.

### Chargement — squelette vs spinner
- **Squelette de lignes** : préféré pour les tableaux (perçu plus rapide, évite le saut de layout)
- **Spinner** : uniquement pour les soumissions de formulaire et téléchargements ponctuels

---

## 06 — Tableaux & Listes

- En-tête sticky au scroll
- Tri par clic sur colonne
- Sélection multiple (cases à cocher)
- Barre d'actions de masse (apparaît dès ≥ 1 ligne cochée, disparaît à 0)
- Un badge coloré max par ligne
- Pagination en pied de tableau (`Affichage de X à Y sur Z`)

**Actions de masse disponibles** : exporter, changer de classe, supprimer (avec toast + annulation 5s)

---

## 07 — Structure de page (App shell)

- **Sidebar** 240px : logo + nom école, navigation groupée par section (Scolarité / Comptabilité / Administration), badge de notification sur les items concernés, profil utilisateur en pied de sidebar
- **Topbar** : recherche globale (`/` ou `Ctrl+K`), notifications
- **Corps de page** : fil d'Ariane → titre + description + action principale (haut droite) → grille de KPIs → contenu principal (tableau / formulaire / détail)

### Règle KPI
Toujours accompagnés d'une **période de référence explicite** (`aujourd'hui`, `ce mois-ci`, `année en cours`). Jamais un chiffre nu dont la fenêtre temporelle est ambiguë — critique pour les données financières. Valeur en Fraunces 600, 28–30px. Période en `ink-faint`, 10px. **Aucune donnée simulée — règle non négociable.**

---

## 08 — Règles de décision (référence rapide)

| Sujet | Règle |
|---|---|
| **Couleur** | Uniquement quand elle porte un sens (statut, alerte, action primaire, rôle). 90% de l'écran en gris neutre. Un seul badge coloré par ligne. |
| **Typographie** | Titres de page : Inter 600, 24px. Fraunces réservé à l'écran de connexion, l'en-tête sidebar, et les KPI dashboard. Jamais `font-bold` dans l'UI. |
| **Densité** | 36–40px par défaut. Toggle compacte/confortable mémorisé par utilisateur pour les modules 50+ lignes. Jamais sous 32px. |
| **Focus** | `outline: 2px solid #C9A84C; outline-offset: 2px`. Jamais en décoration sur avatars/cartes. |
| **Feedback** | Toast bas-droite, fond `#111827`, 4s. Suppression : annulation 5s. Jamais `confirm()` navigateur ni modal bloquante de succès. |
| **Formulaires** | Validation au `blur`. Bandeau global réservé aux erreurs API sans champ cible. `Échap` ferme le drawer (confirmation si modifié), `Ctrl+Entrée` soumet. |
| **Chargement** | Squelette pour les tableaux, spinner pour les soumissions ponctuelles. |
| **KPI** | Toujours une période de référence explicite. Jamais de donnée simulée. |
| **Sélection multiple** | Dès qu'une action de masse a un sens. Barre contextuelle au-dessus du tableau. |
| **Icônes** | `lucide-react` uniquement, `strokeWidth={1.75}` partout. 14–16px inline, 18px dans les boutons icon-only. Jamais de SVG custom si l'équivalent existe dans Lucide. |

### Retiré de v1 → v2 → v3
- Fraunces dans les titres de page courants → remplacé par Inter 600
- Halo doré sur avatars/décoration → réservé au focus/actif uniquement
- Hauteur de ligne 48px par défaut → 36–40px en mode compacte
- `confirm()` navigateur pour suppressions → toast avec annulation
- Filtres cachés dans un menu uniquement → chips retirables visibles
- Chiffres KPI sans période → période de référence obligatoire
- Spinner centré pour les tableaux → skeleton de lignes

---

*v3.0 — Août 2026*
