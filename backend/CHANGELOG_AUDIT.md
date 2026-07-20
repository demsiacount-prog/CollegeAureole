# Audit backend — juillet 2026

Résumé des changements apportés lors de la revue complète du backend
(68 fichiers Python lus intégralement, app testée en conditions réelles avec
des scénarios de bout en bout : auth, inscription, notes, bulletins, paiements).

## Bugs fonctionnels corrigés

- **`GET /api/eleves/{matricule}/dossier` manquant.** Le schéma
  `DossierEleveResponse` existait et était importé, mais aucun endpoint ne
  l'exposait (un commentaire indiquait "à reprendre tel quel", sans que le
  code soit présent). Implémenté : profil élève + historique d'inscriptions
  enrichi (finances, moyennes par trimestre/année) + notes + absences +
  bulletins.
- **`GET /api/inscriptions/{id}` et `GET /api/inscriptions/eleve/{matricule}/historique`**
  déclaraient `InscriptionDetailResponse` (montant payé, reste à payer,
  moyennes...) mais renvoyaient l'objet brut : ces champs calculés
  retombaient silencieusement à leurs valeurs par défaut (0 / null / []),
  jamais aux vraies valeurs. Corrigé en réutilisant la même logique
  d'enrichissement que le dossier élève.

## Performance (N+1 queries)

Plusieurs endpoints de liste sérialisaient des relations imbriquées sans
`joinedload`, ce qui déclenchait une requête SQL supplémentaire par ligne et
par relation (donc jusqu'à des centaines de requêtes pour une seule réponse
sur les tables les plus utilisées) :

- `notes` (liste + détail) : eleve, cours, classe, enseignant, trimestre
- `cours` (liste + détail) : enseignant, classes affectées
- `bulletins` (liste + détail) : détails de bulletin → cours
- `eleves` (liste + détail) : tuteur, classe
- `inscriptions` (détail + historique) : classe, année scolaire, paiements,
  échéances

Toutes ces relations sont désormais chargées en une seule requête via
`joinedload`.

## Garde-fous de production

- **Pagination non bornée** : plusieurs endpoints de liste acceptaient un
  `limit` sans plafond (`?limit=999999999`), permettant de charger une table
  entière en un appel. Plafonné à 500 partout (`Query(..., le=500)`).
- **`Query.get()` déprécié** (API SQLAlchemy legacy) remplacé par une requête
  batch dans `bulletins.py`.
- **`@app.on_event("startup")`** (déprécié) remplacé par un `lifespan`
  FastAPI moderne.
- **`Base.metadata.create_all()`** exécuté à chaque démarrage, y compris en
  production, ce qui masque les migrations manquantes. Rendu conditionnel via
  `AUTO_CREATE_TABLES` (activé par défaut pour ne pas casser l'usage
  dev/démo ; à mettre à `false` en production, où Alembic doit piloter le
  schéma).
- **Health check `/`** renvoyait `"database": "connected"` en dur, sans
  jamais interroger la base. Fait maintenant un vrai `SELECT 1`.
- **Gestionnaire d'exceptions global** ajouté : une exception non prévue ne
  renvoie plus de stack trace au client (fuite d'information), et est
  journalisée côté serveur.
- **`JWT_SECRET_KEY`** : si absent, l'app utilisait silencieusement une
  valeur par défaut documentée dans le code source
  (`changez-moi-en-production`) — un secret prévisible en production permet
  de forger des tokens. Désormais :
  - avertissement explicite dans les logs si la valeur par défaut est utilisée ;
  - démarrage refusé (`RuntimeError`) si `ENVIRONMENT=production` et que le
    secret est absent, par défaut, ou trop court (< 32 caractères).

## Nettoyage

- Imports inutilisés supprimés (`security.py`, plusieurs routeurs, un modèle,
  `seed.py`).
- ⚠️ Attention : `schemas/dossierEleves.py` importe des schémas
  (`ClasseResponse`, `CoursResponse`, `TrimestreResponse`) qui semblent
  inutilisés à la lecture du fichier mais sont en réalité nécessaires : ils
  résolvent les références différées (forward refs) des modèles imbriqués via
  `model_rebuild()`. Un outil de lint généraliste les signalerait à tort comme
  morts — ne pas les retirer.

## Non modifié — points à surveiller côté opérationnel (hors code)

- **`.env` fourni** contient des identifiants Postgres et un secret JWT à
  l'aspect réel. Le fichier est bien exclu par `.gitignore`, mais puisqu'il a
  transité en dehors de votre machine dans cette archive, il est recommandé
  de **régénérer ces identifiants** avant toute mise en production.
- Le stockage des rôles en base (`Enum` SQLAlchemy) utilise les noms Python
  (`ADMIN`, `DIRECTEUR`, `COMPTABLE`) plutôt que les valeurs (`admin`,
  `directeur`, `comptable`). Ce n'est pas un bug — le round-trip ORM gère
  la conversion correctement — mais toute requête SQL manuelle sur la colonne
  `role` doit utiliser les libellés en majuscules.
