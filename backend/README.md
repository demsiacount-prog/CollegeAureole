# Backend Scolarité — College Aureole Management API

## 🛠️ Corrections appliquées (v2.2)

Cette version corrige les incohérences identifiées dans l'audit du backend :

### 1. Sécurité / authentification (le plus important)
- **Le JWT est maintenant réellement vérifié.** Auparavant, `/api/auth/connexion` générait
  un token, mais aucune route ne le contrôlait : tout était ouvert. Chaque router
  business déclare désormais `dependencies=[Depends(get_current_user)]` : un token
  `Authorization: Bearer <token>` valide est requis pour **toute** requête.
- **Contrôle par rôle sur les écritures.** Les routes de création/modification/suppression
  sont en plus protégées par `require_role(...)` :
  - `admin` seul : gestion des comptes (`/api/utilisateurs`), suppressions, années
    scolaires, clôtures, passage d'année.
  - `admin` + `directeur` : CRUD pédagogique (classes, cours, élèves, enseignants,
    tuteurs, notes, bulletins, absences, inscriptions, séances, salles, résultats).
  - `admin` + `directeur` + `comptable` : paiements et dépenses (création/modification).
  - Lecture (`GET`) : accessible à tout utilisateur authentifié, quel que soit son rôle.
  - `POST /api/auth/connexion` reste public (évidemment). Un nouvel endpoint
    `GET /api/auth/moi` permet au frontend de vérifier un token et récupérer le profil.
  - Le changement de mot de passe (`PUT /api/auth/utilisateurs/{id}/mot-de-passe`)
    exige désormais d'être connecté, et seul le titulaire du compte ou un admin peut
    l'effectuer (avant : accessible à n'importe qui connaissant l'ID).
- **Clé JWT** : une vraie valeur aléatoire est générée dans `.env` (`JWT_SECRET_KEY`),
  au lieu de dépendre du défaut `"changez-moi-en-production"` codé en dur dans
  `security.py`. **Régénérez-la avant toute mise en production.**

### 2. Router "Résultats de passage" manquant
`routers/resultats.py` existait mais n'était **pas inclus** dans `main.py` : toutes ses
routes (`/api/resultats/...`) étaient invisibles. Il est maintenant importé et inclus.

### 3. Incohérences de routes
- `routers/utilisateurs.py` avait un préfixe `/api/utilisateurs` **et** un sous-chemin
  `/utilisateurs/{id}` sur GET/PUT/DELETE, ce qui donnait des URLs dupliquées
  (`/api/utilisateurs/utilisateurs/{id}`) incohérentes avec le reste de l'API. Corrigé :
  toutes les routes suivent maintenant le même pattern REST que les autres routers
  (`/api/utilisateurs/`, `/api/utilisateurs/{id}`).
- Le README mentionnait des routes qui n'existaient pas telles quelles
  (`/api/auth/inscription`, `/api/auth/utilisateurs`) : la gestion des comptes est bien
  sur `/api/utilisateurs`, désormais documentée correctement ci-dessous.

### 4. Bug fonctionnel : `PUT /api/utilisateurs/{id}`
Le schéma `UtilisateurUpdate.actif` avait une valeur par défaut (`True`), donc un
`PUT` qui omettait ce champ réactivait silencieusement un compte désactivé. La route
utilise maintenant `model_dump(exclude_unset=True)` : seuls les champs explicitement
envoyés sont modifiés.

### 5. Pagination
Toutes les listes susceptibles de grossir significativement (élèves, notes, absences,
inscriptions, bulletins, paiements, dépenses, séances, cours, enseignants, tuteurs,
classes, utilisateurs) acceptent désormais `?skip=&limit=` avec une limite par défaut
raisonnable, au lieu de charger la table entière à chaque appel. Les tables
structurellement petites (années scolaires, trimestres, salles) n'ont pas été
modifiées : leur volume ne justifie pas la pagination.

### 6. Dépendances
- `requirement.txt` → renommé `requirements.txt` (convention standard), et **toutes
  les versions sont désormais épinglées** (`~=`) pour des installations reproductibles.
- `python-jose` retiré : le code utilise en réalité `PyJWT` (`import jwt`) dans
  `security.py`, `python-jose` n'était jamais importé nulle part — dépendance morte.
- `faker` dans `requirements.txt` : requis par `seed.py`, appelé par
  l'assistant de première configuration (`POST /api/setup/run`).
- `alembic` ajouté pour les migrations de schéma (voir section dédiée plus bas).

### 7. CORS
Les origines autorisées viennent maintenant de la variable d'environnement
`CORS_ORIGINS` (liste séparée par des virgules), avec un fallback sur les ports Vite
de développement (`5173`/`5174`) — plus besoin de modifier `main.py` pour déployer
sur un autre domaine.

### 8. Migrations de base de données
`Base.metadata.create_all()` ne crée que les tables manquantes ; il ne modifie jamais
un schéma existant (ajout de colonne, changement de type...). Un scaffold **Alembic**
a été ajouté (`alembic/`, `alembic.ini`) et branché sur les mêmes modèles que
l'application. Avant toute évolution de modèle en production :

```bash
alembic revision --autogenerate -m "description du changement"
alembic upgrade head
```

⚠️ Sur une base déjà peuplée par `create_all()` (pas encore suivie par Alembic), la
première révision doit être générée puis marquée comme déjà appliquée
(`alembic stamp head`) plutôt que rejouée, pour ne pas tenter de recréer des tables
existantes.

---

## Ce qui a été ajouté avant cette version

Le projet contenait déjà un CRUD complet pour : `Tuteurs`, `Enseignants`, `Classes`,
`Cours`, `Eleves`, `Notes`. Ont été ajoutés : authentification administrative,
années scolaires & trimestres, bulletins, absences, inscriptions & paiements,
séances/salles, dépenses, résultats de passage. Voir le code de chaque router pour
le détail fonctionnel (commentaires conservés).

## Rôles

| Rôle        | Lecture | Écriture pédagogique | Paiements/Dépenses | Gestion des comptes | Années scolaires |
|-------------|:-------:|:---------------------:|:-------------------:|:--------------------:|:------------------:|
| `admin`     | ✅ | ✅ | ✅ | ✅ | ✅ |
| `directeur` | ✅ | ✅ | ✅ | ❌ | ❌ |
| `comptable` | ✅ | ❌ | ✅ (pas de suppression) | ❌ | ❌ |

## Démarrage

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configurez votre .env (déjà présent, à adapter) :
# DATABASE_URL, JWT_SECRET_KEY, CORS_ORIGINS

# Peupler la base avec des données de démonstration (⚠️ supprime tout) :
python3 seed.py

# Lancer le serveur seul (mode dev) :
uvicorn main:app --reload --port 3000
# ou le serveur de production (interface + API, écoute réseau) :
./scripts/start_server.sh
```

Après `seed.py`, trois comptes de démonstration sont créés :
- `admin@collegeaureole.ml` / `Password123!` (rôle admin)
- `directeur@collegeaureole.ml` / `Password123!` (rôle directeur)
- `comptable@collegeaureole.ml` / `Password123!` (rôle comptable)

Pour appeler l'API après connexion, ajoutez l'en-tête
`Authorization: Bearer <access_token>` (récupéré via `POST /api/auth/connexion`)
à chaque requête.

La documentation interactive Swagger est disponible sur `http://localhost:3000/docs`.

## Déploiement multi-poste (une école, plusieurs postes)

L'application fonctionne en **mode serveur** : une seule machine à l'école
porte PostgreSQL + l'API + l'interface, et chaque poste ouvre un **navigateur**
sur `http://<ip-du-serveur>:3000`. Aucune installation sur les postes ; tous
les postes partagent la même base (écritures concurrentes gérées par
PostgreSQL, codes identifiants protégés par verrou advisory).

**Modes de base de données**
- **PostgreSQL (serveur / multi-poste)** : via `DATABASE_URL` dans `.env`.
- **SQLite (desktop Tauri, mono-poste/portable)** : utilisé uniquement quand
  `DATABASE_URL` n'est pas défini — pas adapté au multi-poste.

**Mise en place du serveur**

```bash
# 1. Base PostgreSQL prête ; appliquer les révisions Alembic :
cd backend
alembic upgrade head                    # base vierge
# ou, pour une base existante déjà migrée par l'ancienne chaîne :
#   psql -c "DELETE FROM alembic_version" # si révision obsolète non reconnue
#   alembic stamp 37c410820056 && alembic upgrade head

# 2. Lancer le serveur (interface + API, écoute réseau) :
./scripts/start_server.sh               # http://0.0.0.0:3000

# 3. Sauvegardes quotidiennes (cron) :
15 1 * * * PGHOST=localhost PGUSER=demsi PGDATABASE=collegeaureole \
  PGPASSWORD='...' /chemin/scripts/backup_pg.sh
```

**Sécurité avant mise en service** : changer le mot de passe PostgreSQL et la
`JWT_SECRET_KEY` du `.env`, changer le mot de passe du compte admin à la
première connexion, et ouvrir uniquement le port 3000 sur le réseau local.

## Prochaines étapes suggérées
- Ajouter une suite de tests (pytest + base de test dédiée, ex. SQLite en mémoire ou
  conteneur Postgres jetable) — aucun test automatisé n'existe pour l'instant.
- Générer un PDF de bulletin à partir de `BulletinDetailFullResponse`.
- Envisager un refresh token / une rotation de clé JWT si la durée de session
  (8h actuellement) doit être raccourcie pour les rôles sensibles.
