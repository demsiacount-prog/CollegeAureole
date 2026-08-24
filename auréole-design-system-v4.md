# Auréole — Système de Design v4.0

> Système de design pour l'application de gestion scolaire Auréole. Ce document synthétise les fondations, l'identité visuelle, les composants et les spécifications de pages de la v4.

---

## Sommaire

- [Fondations](#fondations)
  - [01 · Palette & Tokens](#01--palette--tokens)
  - [02 · Typographie](#02--typographie)
  - [03 · Espacement & Grilles](#03--espacement--grilles)
- [Identité](#identité)
  - [04 · Système d'identité des Modules](#04--système-didentité-des-modules-v4-new)
  - [05 · Shell & Topbar](#05--shell--topbar)
  - [06 · Sidebar](#06--sidebar)
- [Composants](#composants)
  - [07 · Boutons](#07--boutons)
  - [08 · Badges](#08--badges)
  - [09 · Tableaux](#09--tableaux)
  - [10 · Tabs](#10--tabs-fix-v4)
  - [11 · Drawer / Formulaires](#11--drawer--formulaires)
- [Pages](#pages)
  - [Type A · Dashboard](#type-a--dashboard)
  - [Type B · Liste paginée](#type-b--liste-paginée)
  - [Type C · Dossier / Détail](#type-c--dossier--détail)
  - [Type D · Saisie de Notes (NOUVEAU)](#type-d--saisie-de-notes-nouveau)
  - [Type E · Wizard d'Inscription](#type-e--wizard-dinscription)
  - [Type F · Finances](#type-f--finances--paiements--dépenses)
  - [Type G · Emploi du Temps](#type-g--emploi-du-temps)
  - [Type H · Paramètres](#type-h--paramètres)
  - [Type I · Connexion](#type-i--connexion)

---

## Fondations

### 01 · Palette & Tokens

La palette v4 simplifie le désordre de v3 : `--color-brand-blue`, `--color-brand-dim`, `--color-brand-border` sont supprimés. Il reste **un seul token d'action** (`--action`) et **un seul or signature** (`--halo`). Les 5 nouveaux tokens `--mod-*` marquent l'identité des modules.

#### Surfaces & Ink

| Token | Hex | Usage |
|---|---|---|
| `base` | `#0e0f13` | Fond app (body) |
| `surface` | `#16181f` | Carte, sidebar, panel |
| `surface-2` | `#1d1f28` | En-tête th, fond input |
| `surface-3` | `#262932` | Badge neutre, hover |
| `ink` | `#f1eee4` | Texte principal |
| `ink-dim` | `#a7a9b4` | Labels, secondaire |
| `ink-faint` | `#6b6e7a` | Métadonnées, icônes |

#### Halo & Action

| Token | Hex | Usage |
|---|---|---|
| `halo` | `#d9a75c` | Focus clavier, nav actif |
| `halo-bright` | `#f0c98a` | Texte actif sidebar |
| `halo-dim` | `#8a6a3c` | Bordure logo sidebar |
| `action` | `#2d6ee8` | Bouton primaire, CTA |
| `action-dark` | `#1e58c4` | Hover/pressed bouton |

> **Règle clé v4** — Le halo doré s'utilise *exclusivement* pour le focus clavier (outline) et l'élément actif de la sidebar. Jamais sur un bouton, jamais comme couleur d'accent de section. L'action bleue est la seule couleur de CTA.

#### Sémantique

| Token | Hex | Usage |
|---|---|---|
| `success` | `#a3c05f` | Présent, payé, actif |
| `warning` | `#c98a4a` | Retard, partiel, alerte |
| `danger` | `#e0707f` | Absent, impayé, erreur |
| `info` | `#5b9dc4` | Info, dispensé |

#### Tokens supprimés en v4 — `BREAKING`

| Token supprimé | Remplacé par | Raison |
|---|---|---|
| `--color-brand-blue` | `--action` | Alias confus d'un même bleu |
| `--color-brand-blue-bright` | — | Inutilisé en pratique |
| `--color-brand-blue-dim` | `var(--action-dk)` | Redondant |
| `--color-brand-blue-wash` | `var(--action-w)` | Redondant |
| `--color-brand-dim` | `var(--action-dk)` | Redondant |
| `--color-brand-border` | `var(--border)` | Jamais utilisé distinctement |
| `--color-brand-bright` | — | Inutilisé après refactor |

---

### 02 · Typographie

**Changement majeur en v4 :** Fraunces passe de « KPI seulement » à « tous les titres de page (h1) ». Chaque page gagne ainsi une signature typographique immédiate, sans alourdir le reste du contenu. Inter reste pour tout ce qui est actionnable ou tabulaire.

#### Échelle complète

| Style | Police / Taille | Usage |
|---|---|---|
| Titre de page (h1) | Fraunces 600 · 28px | `NEW v4` |
| Valeur KPI | Fraunces 600 · 36px | Dashboard |
| Titre de section / card | Inter 600 · 15px | — |
| Corps, valeurs tableau | Inter 400 · 14px | — |
| Métadonnées, labels | Inter 400 · 12px | — |
| IDs, notes, montants | IBM Plex Mono 400 · 12px | — |

> **Règle d'emphase en tableau** — Sur une seule ligne : `font-medium` pour le nom uniquement · `mono` pour les identifiants · `badge` pour le statut · pas d'autres emphases. Jamais de `font-bold`.

Fraunces italic *(opsz 9..144)* est disponible mais réservé aux devises et citations d'établissement dans la sidebar. Ne pas l'utiliser dans les données.

---

### 03 · Espacement & Grilles

| Zone | Valeur | Note |
|---|---|---|
| Sidebar | 240px | Fixe — ne se réduit pas (pas de mode iconique en v4) |
| Topbar | 56px | h-14 — contient année active + user menu |
| Contenu max-width | 1320px | Centré si l'écran est plus large |
| Padding page | px-10 py-8 | 40px / 32px |
| Gap entre sections | gap-6 | 24px — entre PageHeader, toolbar, table |
| Hauteur ligne tableau | 40px | py-2.5 px-5 — densité standard |
| Hauteur ligne compacte | 34px | Mode « dense » activable par l'utilisateur |

---

## Identité

### 04 · Système d'identité des Modules `v4 NEW`

Chaque zone fonctionnelle reçoit une couleur signature appliquée à **trois points de contact seulement** :
1. le point coloré devant le titre de section dans la sidebar
2. le bandeau de 2px en haut du conteneur principal de la page
3. le texte « eyebrow » du PageHeader

Tout le reste reste neutre.

| Module | Couleur | Pages | Notes |
|---|---|---|---|
| **Vie Scolaire** | `#7c9a3f` olive | Élèves · Inscriptions · Absences · Tuteurs | Évoque la croissance |
| **Pédagogie** | `#2d6ee8` (= action) | Cours · Notes · Bulletins · Résultats | Seul module où la couleur du module = couleur action. Tabs des pages Notes/Bulletins = halo (pas action) |
| **Ressources & Temps** | `#5b9dc4` bleu-ciel | Enseignants · Salles · Emploi du temps · Séances | EDT : couleurs par matière (pas couleur module) |
| **Finances** | `#c98a4a` ambre | Paiements · Dépenses · Clôture | Montants en mono, alignés à droite, text-[15px]. Ligne de total en pied de tableau |

> **Admin & Paramètres** — Pas de couleur de module. Surfaces neutres, pas de bandeau coloré. C'est intentionnel : les paramètres ne sont pas un espace de travail opérationnel, ils ne doivent pas attirer l'attention.

#### Implémentation concrète

1. **TableContainer** — ajouter `style="border-top: 2px solid var(--mod-vie)"` selon le module. Le radius de la carte masque les coins, la bande apparaît uniquement en haut.
2. **PageHeader** — ajouter un prop `eyebrow` (ex. « Vie scolaire ») rendu en `text-xs uppercase tracking-wider` avec la couleur du module, au-dessus du titre h1.
3. **Sidebar NAV_SECTIONS** — chaque section reçoit une prop `moduleColor`. Le label de section affiche un point coloré 5px avant le texte en ink-faint.
4. **Jamais en dehors de ces 3 points.** Pas de fond coloré sur les cartes, pas de texte de données coloré, pas de bordure colorée sur les inputs. La couleur de module est un signal de navigation, pas une décoration.

---

### 05 · Shell & Topbar

La Topbar v4 ajoute un indicateur contextuel de l'année scolaire active, visible de partout. Cela évite les sélecteurs d'année répétés sur chaque page. `UPDATE`

1. **Indicateur d'année** — Toujours visible dans la topbar. Format : point vert + « Année 2024–2025 · Active » en mono. Si aucune année active : « Aucune année active » en warning.
2. **Bandeau module** — Le border-top coloré est sur le conteneur principal de la page (TableContainer ou Card principale), pas sur la topbar.

---

### 06 · Sidebar

Changements v4 `UPDATE` :

1. **Point de couleur module** avant chaque label de section (5px dot).
2. **Compteur de badge** — Certains items nav affichent un count (ex : absences non justifiées). Rendu comme un badge neutre à droite du label, disparaît si = 0.
3. **Devise en Fraunces italic** — « L'excellent n'a pas de concurrent » sous le nom de l'école, taille 11px, color halo-dim. C'est le seul usage autorisé de Fraunces italic.
4. **Pas de collapse** en v4 — La sidebar reste à 240px fixe. Un collapse serait utile uniquement sur tablet/mobile, hors scope de la v4.

---

## Composants

### 07 · Boutons

Variantes : **Primaire**, **Secondaire**, **Danger**, **Ghost**, **Désactivé**.

1. **Primaire** — 1 seul par vue (action principale du PageHeader). Toujours à droite, toujours un verbe d'action.
2. **Secondaire dans les tableaux** — Apparaît uniquement au hover de la ligne (`opacity-0 group-hover:opacity-100`). Taille sm (h-8).
3. **Actions de masse** — Barre fixe en bas de page, fond surface-2, apparaît quand ≥ 1 ligne cochée. Contient : « X sélectionné(s) » + actions contextuelles.

---

### 08 · Badges

Tons disponibles : `Actif` / `Payé` / `Présent` (success) · `Partiel` / `Retard` / `Redoublant` (warning) · `Impayé` / `Absent` / `Inactif` (danger) · `Dispensé` / `Directeur` (info) · `Non renseigné` / `Inscrit` (neutre).

> **Règle absolue** — Jamais plus d'un badge coloré par ligne de tableau. Le badge de statut prime sur tout. Si une ligne a plusieurs états (absent + impayé), n'afficher que le plus critique.

---

### 09 · Tableaux

#### Anatomie d'une ligne — types de colonnes

| Type de colonne | Style | Exemple |
|---|---|---|
| Identité primaire | Avatar + font-medium ink | Amadou Koné |
| Identifiant structuré | mono text-xs ink-dim | 2025-0847 |
| Référence contextuelle | text-sm ink-dim | 3e B — Mathématiques |
| Valeur numérique / montant | mono text-[15px] ink, right-align | 1 450 000 FCFA |
| Date | mono text-xs ink-dim | 14 janv. 2025 |
| Statut | Badge (1 seul par ligne) | Actif |
| Actions | opacity-0, group-hover:opacity-100 | Modifier · Supprimer |

> **En-tête sticky** — Sur toutes les listes de plus de 10 lignes, l'en-tête thead doit être sticky (`position: sticky; top: 0; z-index: 1`) pour rester visible lors du scroll.

---

### 10 · Tabs `FIX v4`

En v3, les onglets actifs utilisaient `--color-brand` (bleu action). C'est incohérent : le bleu est réservé aux CTAs. En v4, l'onglet actif utilise le **halo or** — cohérent avec la signature de navigation.

**v3 (incorrect)** : onglet actif en bleu action `#2d6ee8`
**v4 (correct)** : onglet actif en halo or, texte `halo-bright`, bordure `halo`

> Modifier dans `Tabs.tsx` : remplacer `text-[var(--color-brand)]` et `bg-[var(--color-brand)]` par `text-[var(--color-halo-bright)]` et `bg-[var(--color-halo)]`.

---

### 11 · Drawer / Formulaires

1. **Header du drawer** — Titre en Inter 600 18px · Description optionnelle en ink-dim 13px. Pas de Fraunces (ce n'est pas un titre de page).
2. **Groupes de champs** — Titres de groupe en Inter 600 12px uppercase + letter-spacing, bordure-bottom soft. Champs en grid-cols-2, gap-4.
3. **Validation au blur** — L'erreur s'affiche sous le champ dès que l'utilisateur le quitte. Texte danger 12px, pas de bandeau global.
4. **Footer fixe** — Toujours : Annuler (ghost) + Enregistrer (primary). Le bouton primaire prend l'état de chargement pendant la mutation.
5. **Largeur max-w-md** (448px). Trop étroit pour des formulaires complexes → utiliser une page dédiée (ex : wizard inscription).

---

## Pages

### Type A · Dashboard

Deux variantes selon le rôle : **Direction** (KPIs pédagogiques) et **Comptable** (KPIs financiers). Pas de bandeau de module — le dashboard est hors-module.

**Layout Direction** — Salutation (« Bonjour, » + prénom en Fraunces 24px + rôle/date), puis 4 KPI cards :
- Effectif total — 312 (↑ +8 vs an dernier)
- Présences ce mois — 91% (↓ -2% vs mois préc.)
- Revenus perçus — 24,6M FCFA
- Alertes actives — 7 absences non justifiées

Puis layout 2/3 + 1/3 : chart principal (moyennes par classe) à gauche, activité récente à droite.

1. **Salutation Fraunces** — « Bonjour, » en Inter dim 10px · Prénom en Fraunces 24px · Rôle + date en Inter dim 10px.
2. **KPI cards** — Valeur en Fraunces 32–36px. Tendance : ↑ success ou ↓ danger avec variation chiffrée.
3. **Layout 2/3 + 1/3** pour les charts. Chart principal (moyennes, évolution) à gauche, flux d'activité à droite.
4. **Dashboard Comptable** — Mêmes règles. KPIs : Total encaissé | Attendu ce mois | Impayés (danger si > 0) | Dépenses. Chart : Répartition par mode de paiement (donut).

---

### Type B · Liste paginée

Le type de page le plus fréquent. Élèves, enseignants, tuteurs, salles, cours, absences, inscriptions. Structure identique, seul le contenu de la table change.

Structure : eyebrow module + titre Fraunces + sous-titre comptage → toolbar (recherche + filtres pills) → tableau → pagination.

1. **Eyebrow module** + Fraunces h1 + sous-titre comptage dans le container à bordure colorée.
2. **Toolbar** — Barre de recherche pleine largeur + filtres en pills. Les filtres actifs s'affichent sous la toolbar en chips retirables.
3. **Skeleton au chargement** — Jamais de spinner centré. Lignes squelettes (shimmer) à la hauteur réelle du tableau.
4. **Empty state** — Si recherche active : « Aucun élève ne correspond à « [terme] ». » + bouton « Effacer la recherche ». Si vide natif : message d'invitation + bouton d'action primaire.

---

### Type C · Dossier / Détail

Élève, enseignant, tuteur. Hero card en haut, bande de KPIs secondaires, puis tabs Fraunces → content.

Structure : fil d'ariane → hero card (avatar, nom Fraunces, badge statut, matricule mono, métadonnées) → bande de 4 KPIs secondaires (Classe, Inscriptions, Absences, Moyenne) → tabs (Profil, Inscriptions, Résultats, Absences, Documents) → contenu en 2 colonnes.

1. **Hero card** — Avatar large + Fraunces pour le nom + badge statut + mono pour le matricule. C'est le seul endroit où Fraunces est utilisé dans une card (car c'est un titre de personne).
2. **Bande de 4 KPIs** — entre la hero card et les tabs. Valeurs en font-semibold. Si alerte (absences), coloration en warning.
3. **Onglet actif = halo**. Compteur d'onglet : fond neutre si 0, fond warning si l'élément mérite attention.

---

### Type D · Saisie de Notes `NOUVEAU`

Page unique dans l'application : c'est une grille de saisie matricielle, pas une liste. Les sélecteurs de contexte sont en haut, le tableau est une grille éditable avec cellules colorées selon le score.

Structure : barre de contexte (Classe → Cours → Trimestre + barème + bouton Enregistrer) → grille (Élève | Note /20 | Appréciation) → ligne de moyenne classe en pied de tableau.

1. **Barre de contexte sticky** — 3 selects (Classe → Cours → Trimestre) + affichage du barème + bouton Enregistrer. Reste visible lors du scroll si la table est longue.
2. **Couleur des cellules** — Fond wash (pas plein) coloré selon le score : vert si ≥ 12 (≥ 60%), orange si 8–12, rouge si < 8. L'appréciation est calculée automatiquement et affichée en read-only.
3. **Cellule en édition** — Outline action blue sur la cellule active (pas un drawer, pas un modal — édition directe dans la grille). Tab pour passer à la cellule suivante.
4. **Ligne de moyenne** — Pied de tableau en surface-2, valeur auto-calculée en mono, colorée selon le même seuil. Se met à jour en temps réel.
5. **Enregistrement groupé** — Un seul bouton « Enregistrer » pour toutes les notes. Pas de save par ligne. Confirm si on quitte la page avec des modifications non enregistrées.

---

### Type E · Wizard d'Inscription

Barre d'étapes à 4 points : Élève ✓ → Classe (actif) → Frais → Confirmer.

1. **4 étapes** : Choisir l'élève → Choisir la classe → Définir les frais → Confirmer & enregistrer.
2. **Ligne de progression** — Fills left-to-right en bleu action. Les étapes complétées affichent un ✓ blanc sur fond action.
3. **Pas de retour arrière vers une étape ultérieure** — on peut revenir mais pas sauter. Évite les états incohérents.

---

### Type F · Finances — Paiements & Dépenses

Structure : eyebrow « Finances » + titre + comptage → toolbar (recherche + plage de dates) → tableau (Élève, Mode, Montant, Date, Statut) → ligne de total en pied de tableau, couleur ambre.

1. **Montants en mono text-[15px]**, gras, alignés à droite. C'est la colonne principale — elle mérite plus de présence typographique que les autres colonnes.
2. **Ligne de total** — Pied de tableau (fond surface-2), toujours visible pour le filtre actuel. Couleur ambre (module finances). Mention : « Total affiché (filtre actuel) ».
3. **Filtres date** — Date début + date fin en ligne dans la toolbar. Format local (JJ/MM/AAAA). Plage rapide : Aujourd'hui · Cette semaine · Ce mois.

---

### Type G · Emploi du Temps

Grille calendrier 6 jours × N créneaux. Chaque cellule est une séance colorée **par matière** (pas par module). Toggle Vue classe / Vue enseignant.

1. **Couleurs par matière** — Un registre de 8–10 couleurs prédéfinies assignées automatiquement à la création d'un cours. Pas lié aux couleurs de modules. Fond wash + bordure gauche 2px saturée.
2. **Vue double** — Toggle « Vue classe » / « Vue enseignant ». En vue enseignant, chaque ligne = un enseignant.
3. **Click sur cellule** → drawer de détail de la séance (cours, enseignant, salle, modifier/supprimer). Pas de drag pour l'instant.
4. **Cellule vide** — Légèrement assombrie. Hover : icône « + » pour créer une séance directement.

---

### Type H · Paramètres

Layout à 2 colonnes : navigation latérale (Établissement, Années scolaires, Clôture, Comptes, Import/Export, Zone de danger) + contenu.

1. **Pas de bandeau module** — Les paramètres sont hors-module. Surface neutre, sans couleur de section.
2. **Zone de danger** — Card avec bordure danger légère (opacity 30%). Bouton danger uniquement. Précédée d'une phrase explicite sur l'irréversibilité.
3. **Onglet actif = halo** dans la sidebar des paramètres. Cohérent avec les autres tabs de l'app.

---

### Type I · Connexion

Écran centré : logo avec halo ring, nom de l'établissement en Fraunces, devise en Fraunces italic, formulaire e-mail/mot de passe, bouton primaire pleine largeur.

1. **Halo ring autour du logo** — Le seul moment où le halo or est utilisé comme décoration de surface. C'est la signature visuelle de la marque à l'entrée de l'app.
2. **Devise en Fraunces italic** sous le nom. Fond : `--base` (pas de sidebar, pas de topbar).
3. **Erreur de connexion** — Bandeau rouge sous le formulaire : « Identifiants incorrects. Vérifiez votre e-mail et votre mot de passe. » Pas de toast (l'utilisateur n'est pas encore dans l'app).

