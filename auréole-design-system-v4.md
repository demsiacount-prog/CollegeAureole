# Auréole — Système de Design v4.1

> Système de design pour l'application de gestion scolaire Auréole. La v4.1 ajoute trois nouvelles sections **Pré-lancement** (installation Windows, démarrage, configuration initiale), trois nouveaux composants (barre de progression, indicateur d'état, toasts) et la page Type J. Tout le contenu v4.0 est maintenu sans modification.

---

## Sommaire

- [Pré-lancement](#pré-lancement) ← `NEW v4.1`
  - [00 · Assistant d'Installation Windows](#00--assistant-dinstallation-windows-new-v41)
  - [01 · Splash Screen & Démarrage](#01--splash-screen--démarrage-new-v41)
  - [02 · Wizard de Configuration Initiale](#02--wizard-de-configuration-initiale-new-v41)
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
  - [12 · Barre de Progression](#12--barre-de-progression-new-v41) ← `NEW v4.1`
  - [13 · Indicateur d'État](#13--indicateur-détat-new-v41) ← `NEW v4.1`
  - [14 · Toast & Notifications](#14--toast--notifications-new-v41) ← `NEW v4.1`
- [Pages](#pages)
  - [Type A · Dashboard](#type-a--dashboard)
  - [Type B · Liste paginée](#type-b--liste-paginée)
  - [Type C · Dossier / Détail](#type-c--dossier--détail)
  - [Type D · Saisie de Notes](#type-d--saisie-de-notes-nouveau)
  - [Type E · Wizard d'Inscription](#type-e--wizard-dinscription)
  - [Type F · Finances](#type-f--finances--paiements--dépenses)
  - [Type G · Emploi du Temps](#type-g--emploi-du-temps)
  - [Type H · Paramètres](#type-h--paramètres)
  - [Type I · Connexion](#type-i--connexion)
  - [Type J · Premier Tableau de Bord](#type-j--premier-tableau-de-bord-new-v41) ← `NEW v4.1`

---

## Pré-lancement

> Ces trois sections couvrent tout ce qui se passe **avant** que l'utilisateur atteigne l'écran de connexion (Type I) : l'installation sur Windows, le démarrage de l'application, et la configuration de la première instance.

---

### 00 · Assistant d'Installation Windows `NEW v4.1`

#### Contexte technique

Auréole est distribuée sous Windows comme application **Electron packagée** — l'installateur est un exécutable `Auréole-Setup-x.x.x.exe` (généré par Electron Forge / electron-builder avec NSIS custom). La fenêtre de l'assistant est une **fenêtre Electron non-redimensionnable** rendue en HTML/CSS, ce qui permet d'appliquer l'intégralité du design system.

#### Dimensions et structure globale

| Propriété | Valeur |
|---|---|
| Taille de la fenêtre | 760 × 500 px — fixe, non-redimensionnable |
| Cadre natif | `frame: false` — barre de titre personnalisée |
| Fond global | `--base` (#0e0f13) |
| Police de base | Inter (embarquée dans le bundle) |

La fenêtre est divisée en **deux colonnes fixes** :

| Zone | Largeur | Fond | Rôle |
|---|---|---|---|
| **Panneau gauche** | 220 px | `--surface` | Logo, nom, indicateur d'étapes |
| **Zone principale** | 540 px | `--base` | Contenu de l'étape active |

Un **pied de page** de 56 px (`--surface-2`) occupe toute la largeur en bas et contient exclusivement les boutons de navigation.

#### Panneau gauche — Anatomie permanente

1. **Barre de titre custom** (24 px, `--surface`) — icône app 16 px + « Auréole Setup » en Inter 12px `--ink-dim` + boutons minimiser / fermer (croix uniquement, pas de maximiser).
2. **Logo + halo ring** — Identique à la page de connexion (Type I). Taille : 48 px. Marge-top : 40 px.
3. **Nom de l'app** — Fraunces 600 · 18 px · `--ink`.
4. **Numéro de version** — `vX.X.X` en IBM Plex Mono 400 · 11 px · `--ink-faint`. Marge-bottom : 32 px.
5. **Séparateur** — 1 px `--surface-3`.
6. **Indicateur d'étapes** (liste verticale) — voir spécification ci-dessous.
7. **Copyright** — En bas du panneau. Inter 400 · 10 px · `--ink-faint`.

#### Indicateur d'étapes (panneau gauche)

Chaque étape est une ligne avec :
- Un **marqueur circulaire** (20 px) à gauche.
- Le **libellé de l'étape** en Inter 13 px à droite.

| État | Marqueur | Libellé |
|---|---|---|
| Complétée | Fond `--action`, icône ✓ blanc | `--ink-dim` |
| Active | Bordure 2 px `--halo`, fond transparent, point central 6 px `--halo` | `--halo-bright`, Inter 600 |
| À venir | Bordure 1 px `--surface-3`, fond transparent | `--ink-faint` |

Les marqueurs sont reliés par une ligne verticale de 1 px `--surface-3` entre eux.

#### Étape 0 — Bienvenue

| Élément | Spec |
|---|---|
| Titre | Fraunces 600 · 28 px · `--ink` · « Bienvenue dans Auréole » |
| Sous-titre | Inter 400 · 14 px · `--ink-dim` · « L'installation prend moins de 2 minutes. » |
| Bloc d'information | Card `--surface` · border `--surface-3` · radius 8 px · padding 16 px |

Le **bloc d'information** contient trois lignes en Inter 13 px :
- **Version** : `vX.X.X` en mono.
- **Espace requis** : `XXX Mo` en mono.
- **Système requis** : `Windows 10 / 11 (64-bit)` — badge `danger` si non satisfait, badge `success` si compatible.

CTA unique : bouton **Primaire** pleine largeur → « Commencer l'installation ».

#### Étape 1 — Contrat de Licence

| Élément | Spec |
|---|---|
| Titre | Inter 600 · 18 px · « Contrat de licence utilisateur final » |
| Zone CLUF | `overflow-y: scroll` · fond `--surface` · border `--surface-3` · radius 6 px · padding 16 px · Inter 400 · 12 px · `--ink-dim` · hauteur 260 px |
| Checkbox | Composant Checkbox standard + label « J'accepte les termes du contrat de licence » Inter 13 px `--ink` |

> **Règle** — Le bouton « Suivant » du pied de page est désactivé (`opacity-0.4`, `pointer-events: none`) jusqu'à ce que la checkbox soit cochée.

#### Étape 2 — Répertoire d'installation

| Élément | Spec |
|---|---|
| Titre | Inter 600 · 18 px · « Répertoire d'installation » |
| Champ + bouton | Input texte pleine largeur (fond `--surface-2`) + bouton **Ghost** « Parcourir… » à droite |
| Info espace | Inter 12 px · `--ink-faint` · en dessous du champ : « Espace requis : 380 Mo · Disponible : X Go » en mono |
| Répertoire par défaut | `C:\Program Files\Auréole` |

États du champ de répertoire :
- **Valide** : bordure `--border` par défaut.
- **Espace insuffisant** : bordure `--danger` + badge `danger` « Espace insuffisant » sous le champ.
- **Chemin invalide** : bordure `--danger` + message « Ce chemin est invalide ou inaccessible. »

#### Étape 3 — Installation en cours

> C'est la seule étape sans bouton « Précédent » ni « Suivant ». Le pied de page affiche uniquement un bouton **Annuler** (Ghost), désactivé après 50 % de progression.

| Élément | Spec |
|---|---|
| Titre | Inter 600 · 18 px · « Installation en cours… » |
| Barre de progression principale | Composant §12 · variante Installer · `--action` · 8 px de hauteur · pleine largeur · animée |
| Pourcentage | Inter 600 · 24 px · `--ink` · centré sous la barre |
| Tâche actuelle | IBM Plex Mono 400 · 12 px · `--ink-faint` · ex : « Copie des fichiers de l'application… » |
| Liste de vérification | Composant §13 (Indicateur d'État) · détail des sous-tâches |

Sous-tâches affichées dans l'Indicateur d'État :
1. Copie des fichiers de l'application
2. Installation du moteur de base de données
3. Configuration du service Windows
4. Création des raccourcis
5. Finalisation

#### Étape 4 — Finalisation

| Élément | Spec |
|---|---|
| Icône de succès | Cercle 64 px · fond `--success` (opacity 15 %) · icône ✓ 32 px · `--success` |
| Titre | Fraunces 600 · 28 px · « Auréole est installé ! » |
| Message | Inter 400 · 14 px · `--ink-dim` |
| Options | Deux checkboxes : « Lancer Auréole maintenant » (coché par défaut) · « Créer un raccourci sur le Bureau » (coché par défaut) |

Pied de page : un seul bouton **Primaire** → « Terminer ». Pas de « Précédent ».

#### Gestion des erreurs d'installation

Si une étape échoue, l'étape 3 bascule en état d'erreur :
- Icône ✗ `--danger` remplace la barre de progression.
- Titre passe à « Échec de l'installation » en `--danger`.
- Zone texte scrollable avec le log d'erreur en mono 11 px `--ink-faint`.
- Pied de page : bouton **Danger** « Annuler » + bouton **Secondaire** « Réessayer ».

---

### 01 · Splash Screen & Démarrage `NEW v4.1`

#### Rôle

Le splash screen apparaît à chaque lancement d'Auréole (installé). Il effectue en arrière-plan les vérifications nécessaires et oriente l'utilisateur vers la bonne destination : **Setup Wizard** (première utilisation) ou **Page de Connexion** (instance existante).

#### Spécification visuelle

| Élément | Spec |
|---|---|
| Fond | `--base` plein écran (pas de sidebar, pas de topbar) |
| Logo + halo ring | Identique à Type I · 80 px · centré horizontalement |
| Animation halo | Pulse doux : `opacity 0.6 → 1 → 0.6` · durée 2 s · `ease-in-out` · `infinite`. S'arrête quand le chargement est terminé. |
| Nom de l'app | Fraunces 600 · 32 px · `--ink` · sous le logo, marge-top 24 px |
| Devise | Fraunces italic · 13 px · `--halo-dim` · sous le nom |
| Barre de progression | Barre de 2 px · fixée en bas de l'écran · fond `--surface-2` · progression en `--halo` |
| Message d'état | IBM Plex Mono 400 · 12 px · `--ink-faint` · centré · 24 px au-dessus de la barre de progression |
| Version | Inter 400 · 10 px · `--ink-faint` · coin inférieur droit · 16 px de marge |

#### Séquence de démarrage et messages d'état

```
[0 %]  "Démarrage d'Auréole…"
[15 %] "Vérification de la base de données…"
[35 %] "Connexion au serveur local…"
[55 %] "Chargement des configurations…"
[75 %] "Vérification de l'instance…"
[90 %] "Préparation de l'interface…"
[100%] "Prêt !"
```

> Les messages s'affichent en fondu enchaîné (`cross-fade` 150 ms). Ne jamais afficher de pourcentage chiffré pendant le splash — la barre seule suffit.

#### Arbre de décision au lancement

```
Lancement de l'app
  │
  ├─► Première utilisation (aucune instance DB) ?
  │       └─► → Wizard de Configuration Initiale (§02)
  │
  ├─► Instance existante, DB accessible ?
  │       └─► → Page de Connexion (Type I)
  │
  └─► Erreur critique (DB inaccessible, port occupé, etc.)
          └─► → Écran d'erreur de démarrage
```

#### Écran d'erreur de démarrage

S'affiche à la place du splash screen en cas d'échec. Ce n'est **pas** un modal — c'est un écran complet.

| Élément | Spec |
|---|---|
| Fond | `--base` |
| Icône | ✗ dans un cercle · 64 px · couleur `--danger` |
| Titre | Inter 600 · 20 px · `--danger` · « Impossible de démarrer Auréole » |
| Message | Inter 400 · 14 px · `--ink-dim` · explication lisible (ex : « Le port 3000 est déjà utilisé par une autre application. ») |
| Détails techniques | Zone scrollable · fond `--surface` · mono 11 px · `--ink-faint` · label « Détails techniques » en Inter 600 12 px au-dessus |
| Actions | Trois boutons en colonne centrée : **Primaire** « Réessayer » · **Secondaire** « Voir le journal complet » · **Ghost** « Quitter » |

> **Règle** — Le message d'erreur doit toujours contenir une phrase d'action en langage naturel avant les détails techniques. Ex : « Fermez l'application qui utilise le port 3000 et relancez Auréole. »

---

### 02 · Wizard de Configuration Initiale `NEW v4.1`

#### Contexte

Ce wizard apparaît **une seule fois**, à la toute première utilisation, après le splash screen. Il configure l'instance Auréole : établissement, année scolaire, compte administrateur, modules et données initiales. Il est **distinct** du Wizard d'Inscription (Type E) qui lui reste dans l'app courante.

#### Layout global

Pas de sidebar, pas de topbar de l'application. Le wizard est un écran plein entier avec sa propre structure :

| Zone | Spec |
|---|---|
| **Barre supérieure** | 56 px · fond `--surface` · Logo 24 px + « Configuration initiale » Inter 600 14 px `--ink` à gauche · « Étape X sur 6 » Inter 400 13 px `--ink-dim` + indicateur de points à droite |
| **Zone centrale** | Fond `--base` · contenu centré · max-w-lg (512 px) · padding py-10 |
| **Pied de page** | 64 px · fond `--surface-2` · Bouton **Ghost** « Précédent » à gauche · Bouton **Primaire** « Suivant » ou « Lancer Auréole » à droite |

#### Indicateur de points (barre supérieure)

Six points de 8 px : complétés = `--action` plein, actif = `--halo` plein (12 px), à venir = `--surface-3`. Reliés par une ligne 1 px `--surface-3`.

#### Étape 1 — Informations de l'établissement

**Eyebrow** : « CONFIGURATION · 1/6 » en Inter 600 11 px uppercase `--ink-faint`.
**Titre** : Fraunces 600 · 24 px · « Votre établissement ».
**Description** : Inter 400 · 14 px · `--ink-dim`.

Champs du formulaire (grid-cols-1, gap-4) :
| Champ | Type | Requis |
|---|---|---|
| Nom de l'établissement | Text input | ✓ |
| Type d'établissement | Select (École primaire / Collège / Lycée / Université / Autre) | ✓ |
| Pays | Select | ✓ |
| Ville | Text input | ✓ |
| Adresse | Textarea (2 lignes) | — |
| Logo | Zone d'upload (voir ci-dessous) | — |

**Zone d'upload du logo** : Rectangle 200 × 80 px · fond `--surface` · bordure dashed 1 px `--surface-3` · radius 8 px · icône upload + texte « Glissez votre logo ici ou cliquez pour parcourir » Inter 12 px `--ink-dim`. Formats acceptés : PNG, JPG, SVG. Après upload : preview du logo + bouton « Supprimer » (Ghost Danger, sm).

#### Étape 2 — Année scolaire initiale

**Titre** : Fraunces 600 · 24 px · « Année scolaire ».

Champs (grid-cols-2, gap-4) :
| Champ | Type |
|---|---|
| Date de début | Date picker |
| Date de fin | Date picker |
| Libellé | Text input (auto-rempli ex : « 2024–2025 », modifiable) |

**Card de prévisualisation** : Fond `--surface` · radius 8 px · padding 16 px. Affiche le libellé en Inter 600 15 px + badge `success` « Sera définie comme année active ».

> **Règle** — La date de fin doit être postérieure à la date de début. Validation inline au blur. L'année active peut être changée ultérieurement dans Paramètres.

#### Étape 3 — Compte administrateur principal

**Titre** : Fraunces 600 · 24 px · « Compte administrateur ».
**Note contextuelle** : Card `--surface` · bordure gauche 2 px `--halo` · padding 12 px · Inter 13 px `--ink-dim` · « Ce compte aura accès à toutes les fonctionnalités. Vous pourrez créer d'autres comptes depuis les Paramètres. »

Champs (grid-cols-2, gap-4 pour prénom/nom, sinon grid-cols-1) :
| Champ | Type |
|---|---|
| Prénom | Text input |
| Nom | Text input |
| Adresse e-mail | Email input |
| Mot de passe | Password input + toggle visibilité |
| Confirmer le mot de passe | Password input |

**Indicateur de force du mot de passe** : Barre 4 segments sous le champ mot de passe. Rouge (1) → Orange (2) → Vert clair (3) → Vert (4). Labels : Très faible · Faible · Bon · Fort. Règles listées en dessous en Inter 12 px `--ink-dim` avec ✓ coloré ou ○ gris : ≥ 8 caractères · au moins une majuscule · au moins un chiffre.

#### Étape 4 — Activation des modules

**Titre** : Fraunces 600 · 24 px · « Modules actifs ».
**Description** : « Vous pouvez activer ou désactiver des modules à tout moment depuis les Paramètres. »

Quatre **cartes de module** empilées (grid-cols-1, gap-3) :

| Module | Couleur | Activable |
|---|---|---|
| Vie Scolaire | `#7c9a3f` olive | Non — toujours actif (requis) |
| Pédagogie | `#2d6ee8` action | Toggle |
| Ressources & Temps | `#5b9dc4` bleu-ciel | Toggle |
| Finances | `#c98a4a` ambre | Toggle |

Anatomie d'une carte de module :
- Fond `--surface` · radius 8 px · padding 16 px.
- Bandeau gauche 3 px couleur du module.
- Point coloré 8 px + Nom du module Inter 600 15 px `--ink`.
- Description Inter 13 px `--ink-dim` (1 ligne max).
- Toggle ON/OFF à droite (composant Switch standard).
- Si désactivé (Vie Scolaire) : toggle grisé + tooltip « Ce module est requis ».

#### Étape 5 — Données initiales

**Titre** : Fraunces 600 · 24 px · « Données de départ ».

Trois options en **radio cards** (grid-cols-1, gap-3) :

**Option A — Base vide** (sélectionné par défaut)
- Label : « Commencer avec une base vide » Inter 600 14 px.
- Description : « Recommandé pour les nouveaux établissements. » Inter 13 px `--ink-dim`.
- Icône : document vierge.

**Option B — Import CSV/Excel**
- Label : « Importer des données existantes ».
- Description : « Importez vos élèves, enseignants et cours depuis un fichier Excel ou CSV. »
- Si sélectionné : zone d'upload s'affiche en dessous en expansion animée (`height: 0 → auto`, 200 ms ease-out). Fond `--surface` · dashed border · icône upload · « .xlsx, .csv · max 10 Mo ».
- Lien « Télécharger le modèle Excel » en `--action` 13 px sous la zone.

**Option C — Migration Auréole**
- Label : « Migrer depuis une ancienne version d'Auréole ».
- Description : « Importez un export de sauvegarde (.aur) d'une version précédente. »
- Si sélectionné : zone d'upload `.aur` s'affiche.

Radio card anatomy : Fond `--surface` · radius 8 px · padding 16 px · bordure 1 px `--surface-3`. Si sélectionnée : bordure 1 px `--action` + fond `--action` 5 % opacity. Pastille radio 18 px à gauche.

#### Étape 6 — Résumé & Confirmation

**Titre** : Fraunces 600 · 24 px · « Tout est prêt ! ».

**Bloc récapitulatif** : Fond `--surface` · radius 8 px · padding 20 px. Cinq lignes :
| Label | Valeur |
|---|---|
| Établissement | Nom saisi |
| Type | Type sélectionné |
| Année scolaire | Libellé généré |
| Administrateur | Prénom Nom · e-mail |
| Modules | Liste des modules actifs en badges neutres |

Chaque ligne : label Inter 12 px `--ink-faint` à gauche · valeur Inter 14 px `--ink` à droite. Séparateur 1 px `--surface-3` entre les lignes.

**Lien de correction** : « Modifier » en `--action` 12 px à côté de chaque bloc, qui ramène à l'étape correspondante.

**Note finale** : Card `--surface` · bordure gauche 2 px `--halo` · padding 12 px · Inter 13 px `--ink-dim` · « Après le lancement, vous serez automatiquement connecté en tant qu'administrateur. »

Bouton du pied de page : **Primaire** → « Lancer Auréole » (remplace « Suivant »). État de chargement pendant la création de l'instance (spinner + texte « Création de votre instance… »). Durée estimée : 5–15 secondes.

#### États post-lancement

**Succès** → Transition directe vers le Type J (Premier Tableau de Bord) avec l'utilisateur déjà connecté. Pas de retour vers la connexion.

**Échec** → Écran d'erreur inline dans l'étape 6 : icône ✗ `--danger` + message + détails techniques + bouton « Réessayer ».

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
| `halo` | `#d9a75c` | Focus clavier, nav actif, progression splash screen |
| `halo-bright` | `#f0c98a` | Texte actif sidebar |
| `halo-dim` | `#8a6a3c` | Bordure logo sidebar |
| `action` | `#2d6ee8` | Bouton primaire, CTA, progression installer |
| `action-dark` | `#1e58c4` | Hover/pressed bouton |

> **Règle clé v4** — Le halo doré s'utilise *exclusivement* pour le focus clavier (outline), l'élément actif de la sidebar, et la barre de progression du splash screen. Jamais sur un bouton, jamais comme couleur d'accent de section. L'action bleue est la seule couleur de CTA.

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

#### Extensions v4.1 — Pré-lancement

| Style | Police / Taille | Usage |
|---|---|---|
| Titre installeur / splash | Fraunces 600 · 28–32px | Écrans 0 et 4 de l'installeur, splash screen |
| Message d'état système | IBM Plex Mono 400 · 12px | Splash screen, logs d'erreur, détails techniques |
| Titre setup wizard | Fraunces 600 · 24px | Étapes du wizard de configuration |
| Eyebrow setup | Inter 600 · 11px uppercase + tracking-wider | Ex : « CONFIGURATION · 1/6 » |

> **Règle d'emphase en tableau** — Sur une seule ligne : `font-medium` pour le nom uniquement · `mono` pour les identifiants · `badge` pour le statut · pas d'autres emphases. Jamais de `font-bold`.

Fraunces italic *(opsz 9..144)* est disponible mais réservé aux devises et citations d'établissement dans la sidebar et le splash screen. Ne pas l'utiliser dans les données.

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

#### Extensions v4.1 — Pré-lancement

| Zone | Valeur | Note |
|---|---|---|
| Fenêtre installeur | 760 × 500px | Fixe, non-redimensionnable |
| Panneau gauche installeur | 220px | Fixe |
| Pied de page installeur | 56px | |
| Contenu wizard setup | max-w-lg (512px) | Centré |
| Pied de page wizard | 64px | Plus haut que le footer standard |

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
>
> **Wizard de Configuration Initiale** — Pas de couleur de module non plus. Le wizard est un espace neutre de mise en place, pas un module opérationnel. Il hérite du fond `--base` et de l'accent `--halo` pour l'étape active.

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
3. **Devise en Fraunces italic** — « L'excellent n'a pas de concurrent » sous le nom de l'école, taille 11px, color halo-dim. C'est le seul usage autorisé de Fraunces italic dans l'interface principale.
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

### 12 · Barre de Progression `NEW v4.1`

Utilisée dans l'installeur (§00) et le splash screen (§01). Deux variantes selon le contexte.

#### Variante A — Installeur (déterminée)

| Propriété | Valeur |
|---|---|
| Hauteur | 8px |
| Fond de piste | `--surface-3` |
| Couleur de remplissage | `--action` |
| Radius | 4px |
| Transition | `width` · 300ms · `ease-out` |
| Positionnement | Pleine largeur dans la zone principale |

Comportement : la barre progresse de 0 à 100 % en fonction des sous-tâches complétées. Ne jamais simuler une progression — elle doit refléter l'état réel.

#### Variante B — Splash screen (fine, indéterminée puis déterminée)

| Propriété | Valeur |
|---|---|
| Hauteur | 2px |
| Fond de piste | `--surface-2` |
| Couleur de remplissage | `--halo` |
| Radius | 0 (pleine largeur bord à bord) |
| Positionnement | `position: fixed; bottom: 0; left: 0; right: 0` |

Phase indéterminée (0–15 %) : animation shimmer de gauche à droite. Phase déterminée (15–100 %) : progression réelle.

#### Variante C — Wizard de configuration (étapes)

Barre horizontale en haut du wizard setup, sous la barre supérieure. Hauteur 3px · couleur `--action`. Progresse par incréments d'étape (1/6 → 2/6 → … → 6/6). Transition 400ms ease-in-out.

> **Règle** — Ne jamais afficher la barre de progression en `--halo` dans un contexte de CTA ou d'action. Le halo est réservé à la navigation passive (splash screen). L'action est la couleur des progressions actives (installeur, wizard).

---

### 13 · Indicateur d'État `NEW v4.1`

Composant liste verticale utilisé pendant l'installation (§00, étape 3) et les vérifications de démarrage (§01).

#### Anatomie d'un item

```
[Icône 16px]  [Libellé Inter 13px]  [Durée optionnelle mono 11px ink-faint]
```

#### États des items

| État | Icône | Couleur libellé |
|---|---|---|
| En attente | Cercle vide 12px · `--ink-faint` | `--ink-faint` |
| En cours | Spinner animé 14px · `--action` | `--ink` |
| Succès | ✓ plein 14px · `--success` | `--ink-dim` |
| Erreur | ✗ plein 14px · `--danger` | `--danger` |
| Ignoré / Optionnel | — tiret 14px · `--ink-faint` | `--ink-faint` · italic |

#### Comportement

- Les items s'activent séquentiellement — un seul item est « En cours » à la fois.
- La durée (ex : « 1,2 s ») s'affiche uniquement pour les items terminés (succès ou erreur).
- En cas d'erreur : l'item suivant ne démarre pas, et tous les suivants restent « En attente ».
- Le composant peut être utilisé seul ou imbriqué dans l'étape 3 de l'installeur.

---

### 14 · Toast & Notifications `NEW v4.1`

Utilisé dans l'application principale, après le setup. Absent des écrans pré-lancement (installeur, splash, wizard) car l'utilisateur n'est pas encore dans l'app.

#### Position et empilement

- Coin inférieur droit de l'interface principale (par-dessus la sidebar et le contenu).
- `position: fixed; bottom: 24px; right: 24px`.
- Maximum 3 toasts visibles simultanément. Le 4e « pousse » le 1er hors de l'écran vers le bas.
- Les toasts s'empilent vers le haut.

#### Anatomie d'un toast

```
[Icône 18px]  [Titre Inter 600 14px ink]      [Bouton ✕ Ghost 16px]
              [Message optionnel Inter 13px ink-dim]
```

Fond `--surface` · bordure gauche 3px (couleur selon variante) · radius 8px · padding 14px 16px · `box-shadow: 0 4px 16px rgba(0,0,0,0.4)`.

#### Variantes

| Variante | Icône | Couleur bordure | Auto-dismiss |
|---|---|---|---|
| Succès | ✓ `--success` | `--success` | 4 secondes |
| Info | ℹ `--info` | `--info` | 4 secondes |
| Warning | ⚠ `--warning` | `--warning` | 8 secondes |
| Danger | ✗ `--danger` | `--danger` | Persistant (fermeture manuelle) |

#### Animation

- **Entrée** : `translateX(+16px) → 0` + `opacity 0 → 1` · 200ms ease-out.
- **Sortie** : `opacity 1 → 0` + légère réduction de hauteur · 150ms ease-in.
- La barre de progression de l'auto-dismiss s'affiche en bas du toast : 2px `--surface-3`, remplissage de la couleur de la variante, se vide de gauche à droite sur la durée.

> **Règle** — Jamais de toast pour les erreurs critiques (DB inaccessible, etc.) — utiliser un écran d'erreur dédié. Les toasts sont pour les confirmations et alertes légères intra-session.

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

1. **Halo ring autour du logo** — Le seul moment où le halo or est utilisé comme décoration de surface dans l'app courante. C'est la signature visuelle de la marque à l'entrée de l'app.
2. **Devise en Fraunces italic** sous le nom. Fond : `--base` (pas de sidebar, pas de topbar).
3. **Erreur de connexion** — Bandeau rouge sous le formulaire : « Identifiants incorrects. Vérifiez votre e-mail et votre mot de passe. » Pas de toast (l'utilisateur n'est pas encore dans l'app).

---

### Type J · Premier Tableau de Bord `NEW v4.1`

#### Contexte

L'écran affiché immédiatement après la finalisation du Wizard de Configuration Initiale (§02). L'utilisateur est automatiquement connecté en tant qu'administrateur. Ce n'est pas le Type A standard — c'est une version augmentée du dashboard avec un **bandeau de bienvenue** et une **checklist de mise en route**.

#### Différences avec le Type A standard

Le Type J s'affiche **une seule fois** — jusqu'à ce que l'utilisateur ferme le bandeau de bienvenue et complète au moins 3 tâches de la checklist. Après, il bascule vers le Type A normal.

#### Structure de la page

```
Bandeau de bienvenue (fermable)
Checklist de mise en route
Dashboard standard (KPIs + charts)
```

#### Bandeau de bienvenue

Card pleine largeur · fond `--surface` · bordure top 2px `--halo` · padding 20px · radius 8px.

| Élément | Spec |
|---|---|
| Icône halo | Ring doré 40px à gauche |
| Titre | Fraunces 600 · 22px · « Auréole est prêt ! Bienvenue, [Prénom]. » |
| Message | Inter 400 · 14px · `--ink-dim` · « Votre instance est configurée. Commencez par ajouter vos premiers élèves ou configurez l'emploi du temps. » |
| Bouton fermer | Icône ✕ Ghost · coin supérieur droit · ferme le bandeau définitivement (préférence persistée) |

#### Checklist de mise en route

Titre de section : Inter 600 · 15px · « Par où commencer ? » — sous le bandeau.

**Cards de tâches** en grille 3 colonnes, gap-4. Chaque card :
- Fond `--surface` · radius 8px · padding 16px · hauteur fixe 112px.
- Point de couleur du module concerné 8px + label Inter 600 · 14px `--ink`.
- Description Inter 13px · `--ink-dim` (1 ligne).
- Lien « Commencer → » en `--action` 13px en bas de la card.
- **Complétée** : fond `--surface` opacity 60% · icône ✓ `--success` 20px · texte barré en `--ink-faint`.

| Tâche | Module | Priorité |
|---|---|---|
| Ajouter le premier élève | Vie Scolaire | 1 |
| Créer les classes | Vie Scolaire | 1 |
| Ajouter les enseignants | Ressources & Temps | 2 |
| Créer les cours | Pédagogie | 2 |
| Configurer l'emploi du temps | Ressources & Temps | 3 |
| Enregistrer un paiement | Finances | 3 |

Compteur de progression sous le titre : « X / 6 tâches complétées » · Composant §12 variante C (barre 3px `--action`). Quand 6/6 : badge `success` « Mise en route terminée ! » + le bloc disparaît au prochain chargement.

> **Règle** — La checklist ne reapparaît jamais une fois masquée, même si l'utilisateur n'a pas complété toutes les tâches. Un lien « Guide de démarrage » dans le menu utilisateur (topbar) permet d'y revenir volontairement.

#### Toast de bienvenue

Au premier chargement du Type J, un toast **Succès** (§14) s'affiche en bas à droite :
- Titre : « Instance créée avec succès ».
- Message : « Vous êtes connecté en tant qu'administrateur. »
- Auto-dismiss : 6 secondes.

---

## Annexe — Flux complet utilisateur (vue d'ensemble)

```
┌─────────────────────────────────────────────────────────────────┐
│  INSTALLATION WINDOWS (§00)                                     │
│  setup.exe → Bienvenue → Licence → Répertoire → Progression    │
│  → Finalisation                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ Lancer Auréole
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  SPLASH SCREEN (§01)                                            │
│  Logo + halo ring animé → vérifications en arrière-plan         │
└──────┬────────────────────────────────┬──────────────────────────┘
       │ Première utilisation           │ Instance existante
       ▼                                ▼
┌──────────────────────┐    ┌───────────────────────┐
│  WIZARD SETUP (§02)  │    │  PAGE CONNEXION (I)   │
│  6 étapes            │    │  Email + mot de passe │
│  Établissement       │    └──────────┬────────────┘
│  Année scolaire      │               │
│  Compte admin        │               │
│  Modules             │               │
│  Données init.       │               │
│  Résumé & lancement  │               │
└──────────┬───────────┘               │
           │ Auto-connecté             │ Connecté
           ▼                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  PREMIER TABLEAU DE BORD (Type J) — première fois               │
│  → puis DASHBOARD standard (Type A) pour les visites suivantes  │
│  → et toutes les autres pages de l'application                  │
└──────────────────────────────────────────────────────────────────┘
```