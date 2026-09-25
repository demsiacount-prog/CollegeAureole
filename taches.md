# Tâches — Audits & corrections

## Contexte

Signalement utilisateur : « les informations des parents saisies lors d'une nouvelle
inscription ne s'affichent pas dans le dossier de l'élève ».

Un audit systématique a été mené sur **tous les formulaires de création et de
modification de données** de l'application pour vérifier que chaque donnée saisie
est bien **stockée en base** :

- parcours frontend : état du formulaire → payload envoyé (`frontend/src/**/api.ts`)
- parcours backend : endpoint (`backend/routers/*.py`) → schéma Pydantic (`backend/schemas/*.py`) → modèle SQLAlchemy (`backend/models/*.py`) → lecture retour.
- Pydantic v2 a un comportement par défaut `extra='ignore'` : **toute clé envoyée mais
  non déclarée dans le schéma de requête est silencieusement ignorée** (aucune erreur,
  aucune écriture). C'est la source de la perte de données ci-dessous.

---

## BUG 1 — ÉLEVÉ : infos parents perdues lors de l'inscription (dossier-complet)

**Symptôme** : nom/prenom/fonction du père et de la mère saisis à l'étape 1 du
wizard « Nouvelle inscription » ne sont jamais enregistrés ; le dossier élève les
affiche vides.

**Cause racine** : le backend jette les 6 champs avant écriture.

- Frontend envoie bien les champs : `frontend/src/features/inscriptions/InscriptionWizard.tsx:151-156`
  (payload `eleve` → `POST /api/inscriptions/dossier-complet`).
- Schéma de requête `DossierCompletEleve` **ne déclare pas** les 6 champs :
  `backend/schemas/inscriptions.py:87-101` → Pydantic les ignore.
- L'endpoint reconstruit l'élève à partir de `model_dump()` :
  `backend/routers/inscriptions.py:175-179` → les colonnes restent `NULL`.
- Les colonnes existent pourtant : `backend/models/eleves.py:24-29`.
- La lecture/affichage, elle, est correcte : `backend/routers/eleves.py:458-463`,
  `backend/schemas/dossierEleves.py:20`, `frontend/src/features/eleves/EleveDetailPage.tsx:258-259`.
- Autres voies d'écriture conformes : `POST /api/eleves/` et `PUT /api/eleves/{matricule}`
  (`backend/schemas/eleves.py:25-30, 43-68`).

**Correctif** : déclarer les 6 champs dans `DossierCompletEleve`
(`nom_pere`, `prenom_pere`, `fonction_pere`, `nom_mere`, `prenom_mere`, `fonction_mere`,
`Optional[str]`, miroir de `EleveBase`) + test de régression.

- [x] Corrigé
- [x] Test ajouté : `backend/tests/test_routers_inscriptions.py` (`test_dossier_complet_persiste_infos_parents`) — OK, 22 tests inscriptions

---

## BUG 2 — ÉLEVÉ : `lien_parente` du tuteur effacé à NULL à chaque édition

**Symptôme** : le « lien de parenté » saisi lors de la création du tuteur (volet
élève) disparaît dès que le tuteur est modifié via l'écran Tuteurs.

**Cause racine** : formulaire d'édition incomplet + `PUT` qui écrase tous les champs.

- `lien_parente` n'est saisissable que via la création inline d'un tuteur dans
  `frontend/src/features/eleves/EleveFormDrawer.tsx:171-179`.
- L'écran Tuteurs ne le gère pas : `frontend/src/features/tuteurs/TuteurFormDrawer.tsx`
  — `emptyForm` lignes 20-27, préremplissage lignes 40-47 (champ absent).
- L'édition envoie donc un objet sans `lien_parente` → le schéma `TuteurCreate`
  (`backend/schemas/tuteurs.py:32`) le remplace par `None` → `update_tuteur`
  (`backend/routers/tuteurs.py:67-68`) fait `setattr` sur **tous** les champs → la
  valeur stockée est écrasée à `NULL`.
- Le champ n'est pas non plus affiché dans le dossier tuteur :
  `frontend/src/features/tuteurs/TuteurDetailPage.tsx:96-103`.

**Correctif** : ajouter `lien_parente` au `TuteurFormDrawer` (état initial,
préremplissage, champ de saisie) + affichage dans le dossier tuteur + test backend
(le PUT doit préserver `lien_parente`).

- [x] Corrigé — `TuteurFormDrawer.tsx` (champ ajouté), `TuteurDetailPage.tsx` (affichage),
      `backend/routers/tuteurs.py` (`model_dump(exclude_unset=True)` : seuls les champs
      envoyés sont mis à jour — évite d'écraser les champs omis)
- [x] Test ajouté : `backend/tests/test_routers_tuteurs.py`
      (`test_modifier_conserve_lien_parente_omis`, `test_modifier_peut_effacer_lien_parente_explicitement`)
      — OK, 21 tests tuteurs

---

## BUG 3 — MOYEN (lecture) : l'échéance d'un paiement invisible

**Symptôme** : impossible de savoir sur quelle échéance un paiement a été imputé,
tant en liste qu'en édition (l'édition ne réaffiche pas l'échéance).

**Cause racine** : colonne FK persistée mais jamais exposée.

- Le modèle stocke bien `id_echeance` : `backend/models/paiements.py` (FK).
- Absent de la réponse : `backend/schemas/paiements.py:13-24` (`PaiementResponse`).
- Absent de la mise à jour : `backend/schemas/echeances.py:68-74` (`PaiementUpdate`).
- Absent du type frontend : `frontend/src/features/shared/types.ts:122-133` ;
  l'édition remet `ids_echeances` à `[]` : `frontend/src/features/paiements/PaiementFormDrawer.tsx:56`.

**Correctif** : exposer `id_echeance` dans `PaiementResponse` + type frontend +
affichage dans la liste des paiements.

- [x] Corrigé — `backend/schemas/paiements.py` (`id_echeance`),
      `frontend/src/features/shared/types.ts` (type `Paiement`),
      `frontend/src/features/paiements/PaiementListPage.tsx` (colonne « Échéance »)

---

## Formulaires vérifiés OK (stockage conforme)

Chaîne complète payload → schéma → colonne → lecture vérifiée :

- Élèves via API directe : `EleveFormDrawer` (create/update) ↔ `EleveCreate`/`EleveUpdate`.
- Inscriptions (hors dossier-complet) : `InscriptionFormDrawer` ↔ `InscriptionCreate`,
  `PUT /api/inscriptions/{id}`.
- Tuteurs (création hors BUG 2) ↔ `TuteurCreate`.
- Classes & salles ↔ `ClasseCreate`/`SalleCreate`.
- Cours & affectations ↔ `CoursCreate` ; séances ↔ `SeanceCreate`/`SeanceUpdate`.
- Enseignants (27 champs, dont `observations`) ↔ `EnseignantCreate`.
- Absences ↔ `AbsenceCreate` / justification.
- Paiements individuels/groupés, remises ↔ `PaiementEcheanceCreate`/`PaiementGroupeCreate`/`RemiseCreate`.
- Dépenses ↔ `DepenseCreate`/`DepenseUpdate`.
- Notes (saisie, patch, bulk) ↔ `NoteCreate`/`NotePatch`/`NoteBulkRequest`.
- Trimestres, utilisateurs, années scolaires ↔ schémas respectifs.
- Bulletins, résultats, établissement, documents (FormData), clôture, setup, auth.

## Omissions volontaires (pas des bugs)

Clés gérées côté serveur ou non modifiables par conception, absentes des schémas :
`tuteur_id` (eleve PUT), `id_annee_scolaire` (seance PUT), `cloturee` (année),
`verrouille` (trimestre), `actif` (utilisateur create), `statut_passage`/`diplome`/
`credit_disponible` (inscription), `date` (note), `justifiee_par_id`/`date_justification`
(absence), `code_*`/`matricule`/`date_initialisation` (générés auto).
Métadonnées absentes des réponses (non saisies utilisateur) : `tentatives_echouees`,
`verrouille_jusqua`, `created_at`/`updated_at` sur certaines réponses.

## Données passées

Les infos parents des élèves inscrits via le wizard **avant** la correction sont
**définitivement perdues** (jamais écrites en base) : non récupérables
automatiquement. Réédition via le dossier élève requise pour les élèves concernés.

## Durcissement : politique `extra='forbid'`

- [x] Documenté
- [x] **Appliqué** : `model_config = {"extra": "forbid"}` sur tous les schémas de
      requête d'écriture du backend : `schemas/{eleves,tuteurs,inscriptions,classes,
      salles,annees_scolaires,enseignants,trimestres,utilisateurs,auth,echeances,
      remises,notes,absences,seances,cours,depenses,etablissement,documents,cloture,
      bulletins}.py` + schémas inline `routers/{resultats,setup}.py`.

**Dépendance respectée** : appliqué **après** correction du BUG 1 (les 6 clés parents
sont désormais déclarées → plus de rejet).

**Conséquences de l'application**
- `PUT /api/tuteurs/{id}` : passage à `model_dump(exclude_unset=True)` pour ne plus
  écraser les champs omis (correctif BUG 2).
- Séances : le drawer d'édition n'envoyait `id_annee_scolaire` (exclu volontairement
  de `SeanceUpdate`). Le frontend l'omet désormais en édition
  (`SeanceUpdateInput = Omit<SeanceCreateInput, 'id_annee_scolaire'>`) pour rester cohérent
  avec `forbid`.

**Vérification**
- [x] Backend : `pytest` — **520 tests OK** (aucun payload de test n'envoie de clé non déclarée).
- [x] Frontend : `npm run lint` OK ; `npx tsc -b` OK.

---

# Chantier : PostgreSQL uniquement (fin du support SQLite)

## Objectif

L'application (et sa suite de tests) utilise **uniquement PostgreSQL**. Plus
aucun chemin SQLite ne demeure dans le code applicatif ni dans les migrations.

## Historique / motivation

- SQLite ne survit qu'en tant que résidu : `database.py` avait conservé un
  branche SQLite (PRAGMA, pool, listener) jamais réellement utilisée en dev/prod,
  et la suite de tests tournait sur `sqlite:///:memory:` **sans contraintes
  d'intégrité référentielle** (FK désactivées).
- La suite passe donc sur PostgreSQL, où les FK sont **réellement appliquées** :
  c'est ce qui a mis au jour et corrigé une insertion d'orphelins dans un test
  (`test_routers_cours.py`) et une purge illégale dans un autre
  (`test_dashboard_annee_active.py`).

## Modifications

- [x] `backend/database.py` réécrit : PostgreSQL seul. Refus explicite (`RuntimeError`)
      si `DATABASE_URL` n'est pas `postgres://` / `postgresql://` ; pool applicatif
      conservé (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`) ; suppression
      de la branche SQLite, du listener PRAGMA et des variables `SQLITE_*`.
- [x] `backend/tests/conftest.py` réécrit : base PostgreSQL de test dédiée
      (`collegeaureole_test`, dérivée de `DATABASE_URL` ou surchargée par
      `TEST_DATABASE_URL`), **créée automatiquement** si absente (connexion de
      maintenance), moteur `NullPool` (connexion neuve par test), purge complète du
      schéma public entre chaque test (`DROP SCHEMA public CASCADE` / `CREATE SCHEMA
      public` / `create_all`), et rollback de sécurité côté client si une requête a
      avorté la transaction.
- [x] Tests adaptés pour tourner sur PostgreSQL :
      - `test_identifiants.py` : dialecte simulé `postgresql` (branche du verrou
        advisory réellement exercée) ; sessions sur la base de test (fixture
        `db_session_avec_annee`) ; plus de moteur SQLite dédié.
      - `test_robustesse_sauvegardes.py` : suppression du test de PRAGMA ;
        libellés/docstrings mis à jour.
      - `test_routers_cours.py` : le test « cours avec notes » crée désormais les
        références FK valides (tuteur/élève/enseignant réels) au lieu de matricules
        orphelines.
      - `test_smoke.py` : renommage du test (`msqlite` → correction de frappe).
- [x] Migrations alignées sur le modèle `notes` :
      - `a6c8e0f2b4d6` (solidifier_unicite_notes_fk_enseignant) neutralisée en no-op :
        le modèle cible correspond exactement à la baseline (contrainte UNIQUE
        `uq_note_eleve_cours_trimestre` + FK `matricule_enseignant` NOT NULL
        ON DELETE CASCADE). Elle reste dans la chaîne pour préserver les historiques.
      - Nouvelles révision `5c1d7e9f0a3b` : corrige la FK `absences.matricule_eleve`
        (créée par la baseline sans `ON DELETE CASCADE`, alors que le modèle en
        déclare une).
      - Branches SQLite mortes supprimées des révisions `a1b2c3d4e5f6`,
        `9b1a2c3d4e5f`, `e3f2a9c1b4d7` (logique PostgreSQL appliquée sans condition).
- [x] CI (`build-windows.yml`) : service `postgres:17-alpine` + `TEST_DATABASE_URL`
      sur le job pytest.
- [x] Nettoyage : fichiers SQLite résiduels (`test_aureole.db-shm` / `.db-wal`)
      supprimés ; mentions SQLite retirées de `identifiants.py`, `sauvegardes.py`,
      `README.md`.

## Vérification

- [x] `pytest` — **519 tests OK sur PostgreSQL** (base `collegeaureole_test`).
- [x] Base vierge → `alembic upgrade head` → `alembic check` → **zéro dérive**
      (aller-retour downgrade/upgrade de `5c1d7e9f0a3b` également vérifié).
- [x] Frontend : `npm run lint` OK (1 avertissement préexistant,
      `SeanceListPage.tsx`) ; `npx tsc -b` OK.
- [x] Démarrage de la phase suivante : **audit & correctifs financiers** (voir plan
      approuvé : mensualités Oct→Juin conservées, création+dépenses correctibles,
      liste des 17 constats critique/moyen/faible).

# Chantier : audit & correctifs financiers (17 constats)

## Objectif

Appliquer les 17 constats de l'audit (6 critiques, 8 moyens, 3 faibles) sur le
module finances, tout en conservant **9 mensualités Oct→Juin** (décision express,
documentée ci-dessous) et en permettant la **création et la correction des
dépenses** (y compris sur une année clôturée, par choix). Un point de
réconciliation financière a été créé en plus : `GET /api/finances/recapitulatif`
(décision « créer l'endpoint », sans câblage frontend).

## Décisions

- **9 mensualités conservées** : l'échéancier facture Oct→Juin (9 mois). L'audit
  suggérait Oct→Mai (8) ; la demande pédagogique du collège prime. Aucun code n'a
  été changé sur ce point, la documentation de l'échéancier l'acte.
- **Dépenses correctibles** : suppression des gardes PUT/DELETE liées à
  `_dans_annee_cloturee` — une dépense reste modifiable/supprimable même sur une
  année clôturée (c'est le comportement voulu par l'école, pas un constat d'audit).
- **C3 — nature réelle du bug** : dans `_reporter_impayes`, un crédit couvrant des
  arriérés ne faisait que décrémenter les variables locales `reste`/`credit` : il
  n'était **jamais inscrit dans `ech.montant_paye`**. Corrigé.

## Correctifs critiques

- [x] **C1** — `montant_total` retiré des schémas d'entrée `InscriptionBase` /
      `InscriptionUpdate` ; ajouté en lecture seule sur `InscriptionResponse`
      (déjà renvoyé). Le champ optionnel `montant_total?` du type frontend
      `InscriptionCreateInput` (que rien ne fixait) est supprimé.
- [x] **C2** — `_appliquer_changement_classe(db, inscription)` extrait dans
      `routers/inscriptions.py` : échéances REPORTE portées (`id_echeance_origine
      IS NOT NULL`) et inscriptions SOLDE/REPORTE inchangées ; les autres sont
      recalculées (prix rechargés, surplus en crédit, `montant_total` recompté).
      Utilisé par `modifier_inscription` **et** par la création d'inscription via
      l'API `POST /api/eleves` (`_inscrire_eleve`).
- [x] **C3** — `_reporter_impayes` enregistre `ech.montant_paye += couvert` quand
      le crédit couvre l'arriéré ; le surplus part toujours en crédit. Test :
      `ech_attente.montant_paye == 3000`, `ech_octobre.montant_paye == 5000`.
- [x] **C4** — `reste_a_payer` du dossier élève ne somme que les échéances
      payables (EN_ATTENTE / PARTIEL + REPORTE portées), en excluant les sources
      et les échéances d'autres années.
- [x] **C5** — modification d'un paiement rattaché : **400** si
      `montant_paye + delta` dépasse `montant_du` ou devient négatif (la branche
      « surplus mis en crédit » est supprimée). Modification d'un trop-perçu :
      **400** si `credit + delta < 0`.
- [x] **C6** — suppression d'un paiement rattaché : `montant_paye =
      max(montant_paye - montant, 0)` + révocation du surplus hérité de l'ancien
      stationnement (crédit). Suppression d'un trop-perçu : **400** si le crédit
      deviendrait négatif (trop-perçu déjà consommé).

## Correctifs moyens

- [x] **M1** — `_mettre_a_jour_statut` : une échéance dont `montant_du <= 0`
      (remise à zéro) passe bien à **SOLDE**.
- [x] **M2** — le point de relances est restreint aux inscriptions de **l'année
      active** et aux échéances payables (réutilise `_filtre_echeances_payables`).
- [x] **M3** — dashboard : `paiements_annee` joint les inscriptions de l'année
      active (les versements d'impayés d'anciennes années ne gonflent plus
      l'encaissé de l'année).
- [x] **M4** — inscription générée par `POST /api/eleves` : échéancier recalculé
      via `_appliquer_changement_classe` (plus de prix figés à la classe d'origine).
- [x] **M5** — remises inline d'un paiement : `utilisateur_id = user.id`
      (endpoint `enregistrer_paiement` reçoit désormais `Depends(get_current_user)`).
- [x] **M6** — `with_for_update()` sur le chargement de l'inscription et des
      échéances de `_distribuer_paiement` (verrouillage de la distribution).
- [x] **M7** — `id_classe=None` accepté à l'inscription (pré-inscription) :
      `_verifier_existence`; `POST /api/inscriptions` sans classe → 201,
      `montant_total=0`, échéances SOLDE.
- [x] **M8** — passage-année (valence, bascule) : ciblage des élèves via le join
      sur les `Inscriptions` de l'année d'origine (plus de dépendance à
      `Eleves.classe_id`, qui reflète la classe courante).

## Correctifs faibles

- [x] **F1** — passage des élèves d'une année à l'autre : sélection via les
      inscriptions de l'année d'origine (`Inscriptions`), plus de dépendance à
      `Eleves.classe_id` (détail commun avec M8).
- [x] **F2** — pré-inscription sans classe gérée (détail ci-dessus, M7).
- [x] **F3** — catégories `CHARGES` et `MAINTENANCE` ajoutées au Literal
      `CategorieDepense` (backend) et aux options frontend
      (`CATEGORIES`/`CATEGORIE_LABELS`).

## Point de réconciliation financière

- [x] `GET /api/finances/recapitulatif` :
      `historique` (tout l'historique) + `annee` (année active, `null` sinon) —
      encaissé, dépenses, solde, impayé (montant + nombre d'échéances, sources
      REPORTE exclues) et échéances soldées. L'encaissé de l'année ne compte que
      les versements des inscriptions de cette année.
- [x] Route montée dans `main.py`, schémas `RecapitulatifLocal` /
      `RecapitulatifFinancier` dans `schemas/finances.py`, test dédié.

## Tests

- [x] `TestChangementClasse` : + test qu'une échéance REPORTE portée (dette
      héritée) n'est pas recalculée lors d'un changement de classe.
- [x] `TestPreInscription` : inscription sans classe acceptée, échéancier nul.
- [x] `TestTropPerçuTraçable` : nouvelles assertions 400 sur suppression /
      modification d'un trop-perçu déjà consommé ; test `montant_paye` inchangé
      et `credit_disponible` intact sur le refus de dépassement de cap.
- [x] `TestRelances` : seuls les impayés payables de l'année active remontent
      (ni source REPORTE, ni impayé d'ancienne année).
- [x] `test_finances_recapitulatif.py` : vide (année `None`) puis année active +
      inscription + impayés + dépenses, avec un impayé d'ancienne année réglé
      dans l'année (exclu de l'encaissé, inclus en historique).
- [x] `test_routers_depenses.py` : PUT/DELETE désormais **permis** sur une année
      clôturée (200/204).

## Vérification

- [x] Backend : `pytest` — **526 tests OK sur PostgreSQL** (~15 min).
- [x] Frontend : `npm run lint` OK (1 avertissement préexistant,
      `SeanceListPage.tsx`) ; `npx tsc -b` OK.
- [x] Décision de périmètre actée : pas de câblage frontend pour
      `/api/finances/recapitulatif` (endpoint seul, consommables via API).