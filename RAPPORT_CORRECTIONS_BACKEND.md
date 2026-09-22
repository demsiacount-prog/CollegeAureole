# Rapport de corrections backend — Lot A (notes, bulletins, résultats, clôture, moyennes)

Date : 2026-09-21 — Suite : `venv/bin/python -m pytest tests/ -q` → **498 passed**.

Les 11 bugs identifiés sont corrigés. Aucun modèle de base de données, aucun schéma de trimestres, ni le router trimestres n'ont été modifiés (hors périmètre du lot).

---

## 1. Fichiers modifiés

| Fichier | Objet |
|---|---|
| `backend/schemas/notes.py` | Bascules NULL (bug 1), `id_trimestre` requis (bug 2), `peut_saisir`, endpoint d'état de saisie |
| `backend/routers/notes.py` | Verrous d'écriture trimestre + année clôturée, garde de persistance, état de saisie |
| `backend/schemas/bulletins.py` | réponse structurée génération (bug 3), `moyenne_generale` nullable (bug 6) |
| `backend/routers/bulletins.py` | génération structurée, 409 publier/dépublier, rangs PUBLIE, refus moyenne None |
| `backend/routers/resultats.py` | `peut_decider` (bug 7), diplôme ADMIS fin de cycle (bug 8) |
| `backend/routers/cloture.py` | diplômés détachés de la classe (bug 10), 409 structuré (bug 9), fin de cycle = diplôme |
| `backend/services/moyennes.py` | moyennes calculées sur bulletins PUBLIÉS uniquement (bug 11) |
| `backend/tests/test_routers_notes.py`, `test_bulletins.py`, `test_cloture_jardin.py`, `test_moyennes.py`, `test_rapports.py`, `test_routers_resultats.py` | adaptations + nouveaux tests (15 nouveaux) |

---

## 2. Bugs corrigés

### Bug 1 — Note « composition » seule acceptée au schéma mais refusée.
- `schemas/notes.py` : `note` devient `Optional[float]` + validator `au_moins_une_note` (422 si `note` ET `note_classe` sont absents).
- La persistance de `note=None` reste **hors périmètre** : `models/notes.py` déclare `note = Column(... nullable=False)` (non éditable). `_exiger_note_persistable` (`routers/notes.py:117`) lève alors un 422 explicite. Voir « Hors périmètre ».

### Bug 2 — Écriture d'une note sans trimestre / sur trimestre verrouillé ou année clôturée.
- `id_trimestre` désormais **requis** dans `NoteCreate`/`NoteBulkItem` (et accepté dans `NotePatch`).
- `_verifier_trimestre_ecriture` (`routers/notes.py:26`) appliquée à toute écriture : 422 si absent, 404 introuvable, **423** si trimestre verrouillé **ou** année clôturée.
- Suppression de note : refuse pareillement verrouillage et clôture.
- Patch : `exclude_unset=True` (ne blanchit plus `note` avec `None`), garde défensive `id_trimestre`.
- Upsert (`_creer_note`) reconstruit la clé par `(matricule, id_trimestre, id_cours)`.

### Bug 3 — Génération par classe : les élèves en échec étaient perdus.
- `POST /api/bulletins/generer-classe` retourne désormais une réponse structurée :
  ```json
  { "bulletins": [BulletinResponse...], "erreurs": [{"matricule_eleve", "motif"}...],
    "nb_succes": int, "nb_erreurs": int }
  ```
  (`schemas/BulletinGenerationClasseResponse`). 400 uniquement si AUCUN bulletin généré (message listant les motifs). **Contrat front cassé à migrer** (avant : liste seule).

### Bug 4 — Publier/dépublier possible sur année clôturée.
- `_verifier_trimestre_pas_cloture` (`routers/bulletins.py:364`) : 404 trimestre introuvable, **409** si l'année du trimestre est clôturée (avant le changement de statut).

### Bug 5 — Rangs affichés sur les brouillons.
- `_calculer_rangs_classe` (`routers/bulletins.py:248`) : seul un bulletin **PUBLIE** reçoit un rang ; les brouillons sont remis à `rang=None`. Publication/dépublication recalcule avec la même règle.

### Bug 6 — Moyenne générale falsifiée à 0.0.
- `_calculer_bulletin` (`routers/bulletins.py:173/175`) : `moyenne_generale` = `None` si aucune matière coefficientée (ex. coefficients 0), `appreciation` = `None` alors.
- `_upsert_bulletin` refuse l'enregistrement (400 explicite) car la colonne est NOT NULL (`models/bulletins.py` non éditable) — jamais de 0.0 fallacieux au bulletin.

### Bug 7 — Le front n'a aucun drapeau unique pour la prise de décision.
- `GET /api/resultats/{id_classe}` renvoie `peut_decider: bool` (`routers/resultats.py`) = `not annee.cloturee`, aux côtés de `annee_cloturee`. Le front branche **tous** ses contrôles de modification sur `peut_decider`.

### Bug 8 — Le diplôme ne suit pas le statut en fin de cycle.
- `PUT /api/resultats/statut/{inscription_id}` : `insc.diplome = (statut == "ADMIS") and (niveau_ordre(classe) == 9)`.
- `routers/cloture.py` : nouveau `_est_diplome(insc)` = `ADMIS` ET (`diplome` déjà posé OU fin de cycle 9ème). Utilisé dans le preview, `_action_prevue` et l'exécution : un ADMIS en 9ème est **diplômé au lieu de déclencher une erreur « classe suivante introuvable »**.

### Bug 9 — Le 409 de clôture était un simple string.
- `POST /api/cloture/executer` : le 409 « élèves en attente » est structuré :
  ```json
  { "message": "...", "eleves": [{"matricule","nom","prenom","statut_passage"}...], "nb_bloquants": int }
  ```

### Bug 10 — Un diplômé restait « effectif » de sa classe après clôture.
- À la clôture, un diplômé (`_est_diplome`) est désormais **détaché** : `eleve.classe_id = None` (comme les exclus), sinon il apparaissait encore au registre, effectifs et bulletins. (Les inscrits de l'année restent consultables via `Inscriptions`.)

### Bug 11 — Les moyennes annuelles incluaient les brouillons.
- `services/moyennes.py` : `calculer_moyenne_annuelle` et `calculer_moyennes_par_trimestre` ne retiennent que les bulletins `statut == "PUBLIE"`. Test `test_moyennes.py` adapté en conséquence.

---

## 3. Contrat API front à respecter (résumé)

| Endpoint | Changement |
|---|---|
| `POST /api/notes/` , `/api/notes/batch`, `/api/notes/{id}` (PATCH) , `/api/notes/{id}` (DELETE) | exigent `id_trimestre` (sinon 422) ; 404 trimestre inconnu ; **423** verrouillé/clôturé |
| `GET /api/notes/saisie-autorisee` | **nouveau** : `{ annee_id, annee_libelle, annee_cloturee, trimestres: [{id, nom, type, verrouille, annee_cloturee, peut_saisir}], peut_saisir }` — à préférer au blocage note par note |
| `NoteResponse` | champ ajouté `peut_saisir: bool\|null` |
| `POST /api/bulletins/generer-classe` | **réponse changée** : objet `{bulletins, erreurs, nb_succes, nb_erreurs}` au lieu d'une liste (bug 3) |
| `POST /api/bulletins/publier` / depublier | **409** si année du trimestre clôturée |
| `BulletinResponse.moyenne_generale` | peut être `null` (brouillon sans matière coefficientée — jamal persisté) |
| `GET /api/resultats/{id_classe}` | champ ajouté `peut_decider: bool` — le front active/désactive ses contrôles sur CE champ |
| `PUT /api/resultats/statut/{id}` | `diplome` recalculé (ADMIS fin de cycle → `true`) |
| `POST /api/cloture/executer` | 409 structuré (voir bug 9) |

---

## 4. Hors périmètre (signalés, non corrigés — modèles non éditables)

- **`models/notes.py`** : `note` NOT NULL → une note « classe seule » (note=`None`) est acceptée au niveau schéma mais **refusée à la persistance** (422 explicite). Migration modèle requise pour la lever.
- **`models/bulletins.py`** : `moyenne_generale` NOT NULL → on refuse explicitement l'enregistrement d'une moyenne `None` (400) plutôt que de stocker un 0.0. Migration requise pour l'autoriser (cas coefficients nuls).
- `routers/trimestres.py` / `schemas/trimestres.py` (non édités) : l'état de saisie est exposé via le router **notes** (`GET /api/notes/saisie-autorisee`) et non via `/api/trimestres/`.

---

## 5. Tests

- 15 tests ajoutés : trims requis/introuvable/clôturé (423), note classe seule non persistable, deux notes nulles 422, `saisie-autorisee` ouvert/verrouillé, patch effacement composition 422, batch sans trimestre 422, suppression trimestre verrouillé 423, coefficient nul → moyenne None + refus, génération partielle structurée, rangs PUBLIE uniquement, publier/dépublier année clôturée 409, `peut_decider` actif/clôturé, ADMIS fin de cycle diplômé, 409 de clôture structuré, diplômé détaché de sa classe.
- **Résultat global : 498 passed (0 échec)** sur toute la suite backend.