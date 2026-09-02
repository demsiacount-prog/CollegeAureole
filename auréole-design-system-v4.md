# Auréole — Système de Design v4.1

> Système de design pour l'application de gestion scolaire Auréole. La v4.1 ajoute trois nouvelles sections **Pré-lancement** (installation Windows, démarrage, configuration initiale), trois nouveaux composants (barre de progression, indicateur d'état, toasts) et la page Type J. Tout le contenu v4.0 est maintenu sans modification.

---

## Composants (suite)

> Les sections §15 à §21 couvrent les composants référencés dans les sections précédentes mais non encore formalisés. Ils complètent la bibliothèque pour rendre le design system exhaustif et implémentable sans ambiguïté.

---

### 15 · Champs de Formulaire `NEW v4.1`

Les champs de formulaire partagent une anatomie commune et quatre états. Ils sont utilisés dans les drawers (§11), le wizard setup (§02), l'installeur (§00) et les pages dédiées.

#### Anatomie commune

```
[Label Inter 600 12px ink-dim]          [Hint optionnel Inter 12px ink-faint]
[                   Input / Contenu                   ]
[Message d'erreur Inter 12px danger — visible au blur]
```

#### États

| État | Bordure | Fond | Curseur |
|---|---|---|---|
| Idle | 1px `--surface-3` | `--surface-2` | text |
| Focus | 1px `--action` + outline 2px `--action` 25% opacity | `--surface-2` | text |
| Rempli (valide) | 1px `--surface-3` | `--surface-2` | text |
| Erreur | 1px `--danger` + outline 2px `--danger` 25% opacity | `--surface-2` | text |
| Désactivé | 1px `--surface-3` 50% opacity | `--surface-3` 50% opacity | not-allowed |
| Read-only | 1px `--surface-3` dashed | `--base` | default |

Radius : 6px · Padding : 10px 12px · Hauteur : 38px (textarea exclue).

#### Variante — Input texte

Champ texte simple. Peut contenir un préfixe (icône ou texte) ou un suffixe (icône, bouton).

- **Préfixe icône** : 16px · `--ink-faint` · padding-left ajusté à 36px.
- **Suffixe bouton** : Ghost sm (ex : bouton « Parcourir… » dans l'installeur, bouton œil pour mot de passe).
- **Placeholder** : `--ink-faint` · Inter 400.

#### Variante — Textarea

Hauteur min 80px · `resize: vertical` (jamais horizontal). Même états que l'input.

#### Variante — Select

```
[Label]
[  Valeur sélectionnée              ▾ ]
```

La flèche `▾` est une icône SVG `--ink-dim` 12px. Au focus, la flèche pivote à 180° (200ms ease). Le dropdown est un `<ul>` positionné en `position: absolute` sous le champ :

- Fond `--surface` · border 1px `--surface-3` · radius 6px · `box-shadow: 0 8px 24px rgba(0,0,0,0.4)` · `z-index: 50`.
- Hauteur max 240px · `overflow-y: auto`.
- Chaque option : Inter 14px · padding 10px 14px · hover fond `--surface-3` · sélectionnée fond `--action` 10% opacity + texte `--action`.
- Séparateur de groupe optionnel : 1px `--surface-3` + label Inter 600 11px uppercase `--ink-faint` en padding 6px 14px.

#### Variante — Checkbox

```
[  ☐  ]  [Label Inter 14px ink]
         [Description optionnelle Inter 13px ink-dim]
```

Case : 16px × 16px · radius 4px · fond `--surface-2` · bordure 1px `--surface-3`.
- **Cochée** : fond `--action` · bordure `--action` · icône ✓ blanc SVG 10px.
- **Indéterminée** : fond `--action` 50% · tiret blanc.
- **Focus** : outline 2px `--halo` 2px offset.
- **Désactivée** : opacity 40% · `cursor: not-allowed`.

Animation de coche : `scale 0 → 1` · 120ms ease-out.

#### Variante — Switch / Toggle

Utilisé dans le wizard setup (activation des modules) et les paramètres.

```
[ ●──── ]  ON   /   [ ────● ]  OFF
```

| Propriété | ON | OFF |
|---|---|---|
| Fond | `--action` | `--surface-3` |
| Thumb | Blanc · 18px · radius 9px | Blanc · 18px |
| Piste | 36px × 20px · radius 10px | 36px × 20px |
| Transition thumb | `translateX(0 → 16px)` · 180ms ease | — |
| Transition fond | `--surface-3 → --action` · 180ms ease | — |

Focus : outline 2px `--halo` 2px offset autour de la piste.
Désactivé : opacity 40% · `cursor: not-allowed`.

Le label texte (ON/OFF ou libellé personnalisé) se place toujours à droite du switch, Inter 14px `--ink`.

#### Variante — Date Picker

Champ texte avec format `JJ/MM/AAAA` + icône calendrier en suffixe (`--ink-dim`). Au clic sur l'icône ou focus du champ :

**Popup calendrier** (position absolute) :
- Fond `--surface` · border 1px `--surface-3` · radius 8px · `box-shadow: 0 8px 24px rgba(0,0,0,0.4)`.
- Largeur 280px · padding 16px.
- **En-tête** : chevrons `<` `>` Ghost pour changer de mois · mois + année en Inter 600 14px `--ink` centré.
- **Grille jours** : 7 colonnes · labels jours en Inter 600 11px `--ink-faint` uppercase.
- **Cellule jour** : 32px × 32px · radius 4px · hover fond `--surface-3` · Inter 400 13px `--ink`.
- **Jour sélectionné** : fond `--action` · texte blanc · radius 6px.
- **Aujourd'hui** (non sélectionné) : texte `--halo-bright` · point 4px `--halo` dessous.
- **Jours hors mois** : `--ink-faint` · non cliquables.
- **Jours désactivés** (ex : antérieurs à la date de début) : `--surface-3` · `cursor: not-allowed`.

Plages rapides (utilisées dans Type F) : boutons Ghost sm horizontaux au-dessus de la grille — « Aujourd'hui » · « Cette semaine » · « Ce mois ».

#### Variante — Indicateur de force du mot de passe

Utilisé dans le wizard setup étape 3.

Barre à 4 segments sous le champ mot de passe · hauteur 3px · gap 3px entre segments :

| Force | Segments colorés | Couleur | Label |
|---|---|---|---|
| Vide | 0/4 | — | — |
| Très faible | 1/4 | `--danger` | « Très faible » |
| Faible | 2/4 | `--warning` | « Faible » |
| Bon | 3/4 | `--halo` | « Bon » |
| Fort | 4/4 | `--success` | « Fort » |

Label de force : Inter 600 12px · couleur correspondante · affiché à droite de la barre.

---

### 16 · Zone d'Upload `NEW v4.1`

Utilisée dans le wizard setup (logo, données initiales). Deux tailles.

#### Variante — Standard (Données)

Hauteur min 120px · fond `--surface` · bordure dashed 1px `--surface-3` · radius 8px · centrage flex.

Contenu (état vide) :
- Icône upload SVG 32px · `--ink-faint` · marge-bottom 12px.
- Titre : Inter 600 14px `--ink` · « Glissez votre fichier ici ».
- Sous-titre : Inter 13px `--ink-dim` · « ou cliquez pour parcourir ».
- Formats acceptés : Inter 12px `--ink-faint` · ex : « .xlsx, .csv · max 10 Mo ».

États :
- **Drag-over** : bordure solid 1px `--action` · fond `--action` 5% opacity · icône en `--action`.
- **Fichier sélectionné** : icône fichier 24px + nom du fichier Inter 14px `--ink` + poids Inter 12px `--ink-faint` à droite + bouton ✕ Ghost pour supprimer.
- **Erreur de format/taille** : bordure `--danger` + message danger 12px dessous.
- **Upload en cours** : Barre de progression §12 variante A à l'intérieur de la zone + pourcentage centré.

#### Variante — Compact (Logo)

Hauteur 80px · largeur 200px · même styles. Après upload, affiche la preview de l'image (object-fit: contain) + bouton « Supprimer » Ghost Danger sm superposé au hover.

---

### 17 · Modal / Dialog `NEW v4.1`

Utilisé pour les confirmations critiques (quitter une page avec modifications non sauvegardées, suppressions irréversibles, clôture d'année scolaire).

**À ne pas confondre avec le Drawer (§11)** : le drawer est pour les formulaires d'édition. Le modal est pour les confirmations et alertes courtes uniquement.

#### Structure

```
[Overlay fond noir 50% opacity, z-index 100]
  ┌──────────────────────────────────┐
  │ [Titre Inter 600 18px]     [ ✕ ] │
  │ [Message Inter 14px ink-dim]     │
  │                                  │
  │ [Bouton Ghost]  [Bouton Primaire]│
  └──────────────────────────────────┘
```

| Propriété | Valeur |
|---|---|
| Fond modal | `--surface` |
| Border | 1px `--surface-3` |
| Radius | 10px |
| Padding | 24px |
| Largeur | max-w-sm (384px) — jamais plus large |
| Centrage | `position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%)` |

#### Variante — Confirmation standard

- Titre Inter 600 18px `--ink`.
- Message Inter 14px `--ink-dim`.
- Deux boutons : **Ghost** « Annuler » · **Primaire** « Confirmer ».

#### Variante — Confirmation danger (irréversible)

- Icône ⚠ `--danger` 24px en haut du modal.
- Titre Inter 600 18px `--danger`.
- Message Inter 14px `--ink-dim` + phrase explicite sur l'irréversibilité.
- Champ de confirmation : Input texte avec placeholder « Tapez [MOT] pour confirmer » · Inter 13px. Bouton **Danger** désactivé jusqu'à la saisie exacte.
- Bouton **Ghost** « Annuler ».

#### Animation

- **Entrée overlay** : `opacity 0 → 0.5` · 150ms.
- **Entrée modal** : `scale(0.95) opacity(0) → scale(1) opacity(1)` · 200ms ease-out.
- **Sortie** : inverse · 150ms ease-in.

> **Règle** — Maximum 1 modal ouvert à la fois. Le modal bloque l'interaction avec le reste de l'interface (trap focus). Fermeture : clic sur overlay, touche Escape, bouton ✕, ou bouton « Annuler ».

---

### 18 · Pagination `NEW v4.1`

Utilisée en bas de toutes les pages Type B (listes paginées).

```
[ ← Précédent ]  [ 1 ]  [ 2 ]  [ 3 ]  …  [ 12 ]  [ Suivant → ]
                  Affichage de 1–25 sur 312 résultats
```

| Élément | Spec |
|---|---|
| Boutons Précédent / Suivant | Ghost sm · désactivés aux bornes |
| Numéro actif | Inter 600 14px `--ink` · fond `--surface-3` · radius 4px · 32px × 32px |
| Numéros inactifs | Inter 400 14px `--ink-dim` · radius 4px · hover fond `--surface-3` · 32px × 32px |
| Ellipse | Inter 14px `--ink-faint` · non-cliquable |
| Comptage | Inter 13px `--ink-faint` · centré sous la pagination · ex : « Affichage de 1–25 sur 312 résultats » |

Fenêtre d'affichage : toujours visible — page 1, [2 pages autour de l'active], dernière page. Le reste en ellipses.

Sélecteur de taille de page (optionnel, dans les tableaux denses) : Select sm (§15) · options : 25 · 50 · 100 · placé à droite du comptage.

---

### 19 · États Vides & Squelettes `NEW v4.1`

#### Squelette de chargement (Skeleton)

Règle v4 : **jamais de spinner centré dans un tableau ou une liste**. Toujours des lignes squelettes à la hauteur réelle du contenu.

Implémentation :
- Rectangle fond `--surface-3` · radius 4px · animation shimmer.
- Animation shimmer : dégradé linéaire `--surface-3 → --surface-2 → --surface-3` se déplaçant de gauche à droite · 1.4s · `ease-in-out` · `infinite`.

Skeleton d'une ligne de tableau (40px) :
```
[ ●●  ████████████  ]  [ ██████  ]  [ ████████  ]  [ ██  ]
  avatar  nom             ref          montant        badge
```

Les rectangles squelettes imitent la largeur approximative du contenu réel. Générer entre 5 et 8 lignes squelettes (jamais moins, jamais plus que la `pageSize`).

Skeleton d'une KPI card : rectangle 100% × 80px.

#### État vide — Liste sans résultat (recherche active)

```
        [ Icône loupe 48px ink-faint ]
        Aucun élève ne correspond à « [terme] »
        [ Bouton Ghost "Effacer la recherche" ]
```

- Centré verticalement dans la zone du tableau.
- Icône : `--ink-faint` · 48px.
- Message : Inter 400 · 15px · `--ink-dim` · le terme de recherche entre guillemets en `--ink`.
- Bouton : Ghost sm.

#### État vide — Liste native (aucune donnée)

```
        [ Icône contextuelle 48px ink-faint ]
        Aucun élève enregistré pour le moment
        Ajoutez votre premier élève pour commencer.
        [ Bouton Primaire "+ Ajouter un élève" ]
```

- Icône adaptée au contenu (élève, enseignant, cours…).
- Titre : Inter 600 · 16px · `--ink`.
- Description : Inter 400 · 14px · `--ink-dim`.
- CTA : bouton **Primaire**.

---

### 20 · Fil d'ariane & Navigation contextuelle `NEW v4.1`

Utilisé dans les pages Type C (Dossier/Détail) et partout où l'utilisateur navigue vers une sous-page.

```
Élèves  /  Aminata Diallo  /  Résultats
```

| Élément | Spec |
|---|---|
| Segments cliquables | Inter 400 · 13px · `--ink-dim` · hover `--ink` · underline au hover |
| Séparateur `/` | Inter 400 · 13px · `--ink-faint` · padding 0 6px |
| Segment actif (dernier) | Inter 600 · 13px · `--ink` · non-cliquable |

Positionnement : au-dessus du hero card ou du PageHeader · marge-bottom 12px.

> **Règle** — Maximum 3 niveaux de profondeur dans le fil d'ariane. Si la hiérarchie est plus profonde, tronquer les niveaux intermédiaires avec « … ».

---

### 21 · Avatar `NEW v4.1`

Utilisé dans les tableaux (colonne identité), les hero cards (Type C), la topbar (menu utilisateur), et la sidebar (nom de l'utilisateur connecté).

#### Tailles

| Alias | Dimension | Usage |
|---|---|---|
| `xs` | 24px | Ligne de tableau compacte |
| `sm` | 32px | Ligne de tableau standard |
| `md` | 40px | Topbar, commentaires |
| `lg` | 64px | Hero card (Type C) |
| `xl` | 80px | Hero card élargi |

#### États

**Avec photo** : image circulaire `object-fit: cover` · radius 50%.

**Sans photo (initiales)** :
- Fond : couleur dérivée du nom (hash déterministe → l'une des 8 couleurs de modules/sémantiques prédéfinies).
- Initiales : 1 ou 2 caractères · Inter 600 · blanc · taille proportionnelle au diamètre.

**En ligne dans un tableau** : l'avatar `sm` est accompagné du nom en Inter 500 14px `--ink` et d'une métadonnée optionnelle en Inter 400 12px `--ink-dim` (ex : matricule).

**En ligne dans la sidebar** (utilisateur connecté, bas de sidebar) :
- Avatar `sm` + Prénom Nom Inter 600 13px `--ink` + rôle Inter 400 12px `--ink-dim` + icône menu `⋮` Ghost à droite.

---

## Interactions & Animations `NEW v4.1`

### Principes

1. **Utilitaire avant tout** — Une animation justifie son existence par l'information qu'elle transmet (changement d'état, direction de navigation, hiérarchie). Jamais décorative.
2. **Rapidité** — Les interactions de l'interface métier (tableaux, formulaires) doivent être quasi-instantanées. Durées courtes.
3. **Cohérence des easing** — Deux easings seulement dans toute l'application.

### Référentiel de durées

| Cas | Durée | Easing |
|---|---|---|
| Hover (fond, couleur) | 100ms | `ease-out` |
| Apparition d'un élément court (badge, tooltip) | 150ms | `ease-out` |
| Ouverture d'un dropdown ou popover | 150ms | `ease-out` |
| Fermeture d'un dropdown ou popover | 100ms | `ease-in` |
| Ouverture du drawer | 220ms | `cubic-bezier(0.25, 0, 0, 1)` |
| Fermeture du drawer | 180ms | `cubic-bezier(0.4, 0, 1, 1)` |
| Ouverture d'un modal | 200ms | `ease-out` |
| Toast entrée | 200ms | `ease-out` |
| Toast sortie | 150ms | `ease-in` |
| Barre de progression | 300ms par incrément | `ease-out` |
| Transition switch/toggle | 180ms | `ease` |
| Splash screen — halo pulse | 2000ms | `ease-in-out` · infinite |
| Skeleton shimmer | 1400ms | `ease-in-out` · infinite |

### États interactifs des éléments cliquables

Tous les éléments interactifs (boutons, items nav, lignes de tableau, cellules calendrier) respectent cette séquence d'état :

| État | Transformation |
|---|---|
| Idle | Aucune |
| Hover | `background: var(--surface-3)` (si applicable) · 100ms |
| Active / Pressed | `scale(0.98)` · instantané |
| Focus-visible | `outline: 2px solid var(--halo)` · `outline-offset: 2px` · instantané |
| Disabled | `opacity: 0.4` · `cursor: not-allowed` · transitions désactivées |

> **Règle focus-visible** — L'outline halo or s'affiche **uniquement** sur `:focus-visible` (navigation clavier), jamais sur `:focus` seul. Les utilisateurs souris ne voient jamais l'outline.

### Transitions de page (navigation dans l'app)

Navigation entre modules : fade out/in du contenu principal (pas de la sidebar ni de la topbar).
- **Sortie** : `opacity 1 → 0` · 80ms.
- **Entrée** : `opacity 0 → 1` + `translateY(4px → 0)` · 120ms · `ease-out`.
- Déclenché uniquement au changement de route principale (pas pour les tabs ou les filtres).

### Ouverture du Drawer

- Le drawer entre depuis la droite : `translateX(100% → 0)` · 220ms.
- L'overlay s'assombrit simultanément : `opacity 0 → 0.5` · 220ms.
- Le contenu de la page ne se décale pas (le drawer se superpose).

### Chargement de données (tableaux)

1. Le skeleton s'affiche immédiatement à la navigation.
2. Si les données arrivent en moins de 300ms, le skeleton disparaît sans transition visible.
3. Si plus de 300ms : skeleton affiché · puis `opacity 0 → 1` du tableau réel · 150ms.
4. Jamais de flash « skeleton → vide → données » : le skeleton doit rester jusqu'à ce que les données soient prêtes.

---

## Accessibilité `NEW v4.1`

### Contraste minimum

| Contexte | Ratio minimum |
|---|---|
| Texte courant (`--ink` sur `--surface`) | 7.1 : 1 — WCAG AAA ✓ |
| Texte secondaire (`--ink-dim` sur `--surface`) | 4.6 : 1 — WCAG AA ✓ |
| Texte faint (`--ink-faint` sur `--surface`) | 3.2 : 1 — décoratif uniquement, jamais porteur d'information critique |
| Texte `--halo-bright` sur `--surface` | 4.8 : 1 — WCAG AA ✓ |
| Texte blanc sur `--action` | 4.5 : 1 — WCAG AA ✓ |
| Texte blanc sur `--danger` | 4.6 : 1 — WCAG AA ✓ |

> **Règle** — `--ink-faint` ne peut jamais être le seul porteur d'une information critique (montant, statut, date). Il est réservé aux métadonnées et icônes qui doublent une information textuelle.

### Navigation clavier

Ordre de tabulation logique sur toutes les pages :
1. Sidebar (items nav dans l'ordre visuel).
2. Topbar (indicateur année → menu utilisateur).
3. PageHeader (bouton primaire).
4. Toolbar (recherche → filtres).
5. Tableau (lignes dans l'ordre visuel · actions dans la ligne au tab).
6. Pagination.
7. Actions de masse (si présentes).

**Raccourcis clavier globaux** (à documenter dans l'interface via un panneau `?`) :

| Raccourci | Action |
|---|---|
| `Ctrl + K` | Ouvrir la recherche globale |
| `Escape` | Fermer drawer / modal / dropdown actif |
| `Tab` / `Shift+Tab` | Navigation entre champs |
| `Espace` | Activer une checkbox ou un switch focus |
| `Entrée` | Confirmer / soumettre le formulaire actif |
| `←` `→` | Naviguer entre les tabs actifs |

### Attributs ARIA obligatoires

| Composant | Attributs requis |
|---|---|
| Sidebar nav | `role="navigation"` · `aria-label="Navigation principale"` |
| Item nav actif | `aria-current="page"` |
| Drawer | `role="dialog"` · `aria-modal="true"` · `aria-labelledby` → id du titre |
| Modal | `role="alertdialog"` (confirmation) ou `role="dialog"` · `aria-modal="true"` |
| Table | `role="grid"` si éditable (Type D) · `<caption>` présent mais visuellement masqué |
| Colonne triable | `aria-sort="ascending|descending|none"` |
| Badge statut | `aria-label` explicite (ex : `aria-label="Statut : Absent"`) |
| Barre de progression | `role="progressbar"` · `aria-valuenow` · `aria-valuemin="0"` · `aria-valuemax="100"` |
| Toast | `role="alert"` · `aria-live="polite"` (success/info) ou `aria-live="assertive"` (danger) |
| Switch | `role="switch"` · `aria-checked="true|false"` |
| Tabs | `role="tablist"` → `role="tab"` → `role="tabpanel"` · `aria-selected` |

### Gestion du focus (Focus Management)

**Ouverture du drawer** : le focus se déplace vers le premier champ du drawer. À la fermeture, le focus retourne sur l'élément qui a déclenché l'ouverture.

**Ouverture d'un modal** : trap focus à l'intérieur du modal (Tab cycle entre les éléments interactifs du modal uniquement). À la fermeture, focus retourne sur l'élément déclencheur.

**Navigation wizard** : à chaque changement d'étape, le focus se déplace sur le titre de l'étape (`tabIndex="-1"` + `focus()` programmatique).

**Toast** : ne reçoit pas le focus automatiquement. S'il contient un bouton d'action, il doit être atteignable au clavier sans interrompre le flux principal.

### Réduction de mouvement

Respecter `prefers-reduced-motion: reduce` :
- Désactiver toutes les transitions `transform` et les animations `opacity`.
- Conserver les changements d'état instantanés (couleur, fond).
- L'animation halo du splash screen et le shimmer des squelettes sont désactivés.
- Implémenter via un media query global dans `globals.css` :

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Implémentation CSS `NEW v4.1`

### Variables CSS — Référentiel complet

À placer dans `:root` de `globals.css` (ou équivalent) :

```css
:root {
  /* === Surfaces === */
  --base:       #0e0f13;
  --surface:    #16181f;
  --surface-2:  #1d1f28;
  --surface-3:  #262932;

  /* === Ink === */
  --ink:        #f1eee4;
  --ink-dim:    #a7a9b4;
  --ink-faint:  #6b6e7a;

  /* === Halo === */
  --halo:        #d9a75c;
  --halo-bright: #f0c98a;
  --halo-dim:    #8a6a3c;

  /* === Action === */
  --action:      #2d6ee8;
  --action-dk:   #1e58c4;
  --action-w:    rgba(45, 110, 232, 0.10);

  /* === Sémantique === */
  --success:     #a3c05f;
  --success-w:   rgba(163, 192, 95, 0.10);
  --warning:     #c98a4a;
  --warning-w:   rgba(201, 138, 74, 0.10);
  --danger:      #e0707f;
  --danger-w:    rgba(224, 112, 127, 0.10);
  --info:        #5b9dc4;
  --info-w:      rgba(91, 157, 196, 0.10);

  /* === Modules === */
  --mod-vie:     #7c9a3f;
  --mod-ped:     #2d6ee8;  /* = --action */
  --mod-res:     #5b9dc4;  /* = --info */
  --mod-fin:     #c98a4a;  /* = --warning */

  /* === Bordures === */
  --border:      rgba(255, 255, 255, 0.06);
  --border-soft: rgba(255, 255, 255, 0.03);

  /* === Polices === */
  --font-sans:   'Inter', system-ui, sans-serif;
  --font-serif:  'Fraunces', Georgia, serif;
  --font-mono:   'IBM Plex Mono', 'Courier New', monospace;

  /* === Radius === */
  --radius-sm:   4px;
  --radius:      6px;
  --radius-md:   8px;
  --radius-lg:   10px;
  --radius-xl:   12px;

  /* === Ombres === */
  --shadow-sm:   0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow:      0 4px 16px rgba(0, 0, 0, 0.4);
  --shadow-lg:   0 8px 32px rgba(0, 0, 0, 0.5);

  /* === Z-index === */
  --z-dropdown:  50;
  --z-sticky:    40;
  --z-overlay:   80;
  --z-drawer:    90;
  --z-modal:     100;
  --z-toast:     110;
}
```

### Classes utilitaires personnalisées (hors Tailwind)

```css
/* Eyebrow de module */
.eyebrow-module {
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  line-height: 1;
}

/* Valeur mono (montants, IDs) */
.value-mono {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--ink-dim);
}

/* Valeur mono grande (montants dans tableaux Finances) */
.value-mono-lg {
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 500;
  color: var(--ink);
  text-align: right;
}

/* Animation shimmer pour les squelettes */
@keyframes shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--surface-3) 25%,
    var(--surface-2) 50%,
    var(--surface-3) 75%
  );
  background-size: 800px 100%;
  animation: shimmer 1.4s ease-in-out infinite;
  border-radius: var(--radius-sm);
}

/* Halo ring (logo page connexion et splash screen) */
.halo-ring {
  box-shadow: 0 0 0 3px var(--halo-dim),
              0 0 0 6px rgba(217, 167, 92, 0.15);
  border-radius: 50%;
}

/* Bandeau de module (border-top de la TableContainer) */
.mod-band-vie { border-top: 2px solid var(--mod-vie); }
.mod-band-ped { border-top: 2px solid var(--mod-ped); }
.mod-band-res { border-top: 2px solid var(--mod-res); }
.mod-band-fin { border-top: 2px solid var(--mod-fin); }
```

### Configuration Tailwind étendue

```js
// tailwind.config.js (extrait)
module.exports = {
  theme: {
    extend: {
      colors: {
        base:        'var(--base)',
        surface:     'var(--surface)',
        'surface-2': 'var(--surface-2)',
        'surface-3': 'var(--surface-3)',
        ink:         'var(--ink)',
        'ink-dim':   'var(--ink-dim)',
        'ink-faint': 'var(--ink-faint)',
        halo:        'var(--halo)',
        'halo-bright':'var(--halo-bright)',
        'halo-dim':  'var(--halo-dim)',
        action:      'var(--action)',
        'action-dk': 'var(--action-dk)',
        success:     'var(--success)',
        warning:     'var(--warning)',
        danger:      'var(--danger)',
        info:        'var(--info)',
      },
      fontFamily: {
        sans:  'var(--font-sans)',
        serif: 'var(--font-serif)',
        mono:  'var(--font-mono)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        DEFAULT: 'var(--radius)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        DEFAULT: 'var(--shadow)',
        lg: 'var(--shadow-lg)',
      },
    },
  },
};
```

---

## Changelog

### v4.1 (actuelle)

**Pré-lancement — Ajouts**
- `§00` Assistant d'Installation Windows : fenêtre Electron 760×500px, panneau gauche permanent, 5 étapes (Bienvenue → Licence → Répertoire → Installation → Finalisation), gestion des erreurs d'installation.
- `§01` Splash Screen & Démarrage : spécification visuelle complète, séquence de messages d'état, arbre de décision (première utilisation / instance existante), écran d'erreur de démarrage.
- `§02` Wizard de Configuration Initiale : 6 étapes (Établissement → Année scolaire → Compte admin → Modules → Données → Résumé), layout full-screen, états post-lancement.

**Composants — Ajouts**
- `§12` Barre de Progression : 3 variantes (Installer, Splash screen, Wizard).
- `§13` Indicateur d'État : 5 états (en attente, en cours, succès, erreur, ignoré).
- `§14` Toast & Notifications : 4 variantes, empilement, auto-dismiss, animation.
- `§15` Champs de Formulaire : Input, Textarea, Select, Checkbox, Switch/Toggle, Date Picker, Indicateur de force du mot de passe.
- `§16` Zone d'Upload : variante standard et compacte.
- `§17` Modal / Dialog : variante confirmation standard et danger irréversible.
- `§18` Pagination : anatomie, fenêtre d'affichage, sélecteur de taille.
- `§19` États Vides & Squelettes : skeleton, empty state recherche, empty state natif.
- `§20` Fil d'ariane : 3 niveaux max, règles de troncature.
- `§21` Avatar : 5 tailles, avec photo, avec initiales, en tableau, en sidebar.

**Sections transversales — Ajouts**
- Interactions & Animations : référentiel de durées, états interactifs, transitions de page, focus management, ouverture drawer.
- Accessibilité : ratios de contraste, navigation clavier, raccourcis globaux, attributs ARIA obligatoires, gestion du focus, prefers-reduced-motion.
- Implémentation CSS : variables complètes, classes utilitaires, configuration Tailwind.
- Annexe flux complet utilisateur.

**Typographie — Extension**
- Ajout des styles Pré-lancement : titres installeur/splash, message d'état système, titres wizard setup, eyebrow setup.

**Espacement & Grilles — Extension**
- Ajout des dimensions Pré-lancement : fenêtre installeur, panneau gauche, pied de page wizard.

**Pages — Ajouts**
- `Type J` Premier Tableau de Bord : bandeau de bienvenue, règles de transition vers Type A.

**Identité — Extension**
- Précision sur l'absence de couleur de module dans le Wizard de Configuration Initiale.

---

### v4.0

- Refonte complète de la palette (suppression des tokens `--color-brand-*`).
- Introduction du système d'identité des modules (`--mod-*`).
- Fraunces étendu à tous les titres h1.
- Fix des Tabs : remplacement du bleu action par le halo or.
- Ajout du Type D (Saisie de Notes) et du Type I (Connexion).
- Sidebar : point de couleur module, compteur de badge, devise Fraunces italic.
- Topbar : indicateur d'année scolaire active.
