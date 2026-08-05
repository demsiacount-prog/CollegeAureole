# Système de Gestion des Erreurs - Backend

## Vue d'ensemble

Le backend utilise un système centralisé de gestion des erreurs pour fournir des messages clairs et cohérents aux utilisateurs.

## Structure des réponses d'erreur

Toutes les erreurs sont retournées dans un format standardisé :

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Données invalides : email",
  "details": {
    "field": "email",
    "reason": "Format d'email invalide"
  }
}
```

## Classes d'exception disponibles

### `AureoleException` (base)
Classe de base pour toutes les exceptions métier.

**Usage :**
```python
raise AureoleException(
    error_code="CUSTOM_CODE",
    message="Message utilisateur",
    status_code=status.HTTP_400_BAD_REQUEST,
    details={"extra": "info"}
)
```

### `NotFoundError` (404)
Ressource non trouvée.

**Usage :**
```python
raise NotFoundError("Élève", "ELV001")
# → "Élève non trouvée : ELV001"

# Ou sans identifiant :
raise NotFoundError("Classe")
# → "Classe non trouvée"
```

### `ValidationError` (422)
Données invalides.

**Usage :**
```python
raise ValidationError("email", "Format d'email invalide")
raise ValidationError("montant", "Le montant doit être positif")
```

### `DuplicateError` (409)
Doublon détecté.

**Usage :**
```python
raise DuplicateError("Élève", "email", "jean@example.com")
```

### `UnauthorizedError` (401)
Authentification requise.

**Usage :**
```python
raise UnauthorizedError("Email ou mot de passe incorrect")
```

### `ForbiddenError` (403)
Accès refusé / permissions insuffisantes.

**Usage :**
```python
raise ForbiddenError("Vous n'avez pas la permission de modifier cet élève")
raise ForbiddenError("Rôle insuffisant. Rôles requis : admin, directeur")
```

### `ConflictError` (409)
Conflit d'état.

**Usage :**
```python
raise ConflictError(
    "Impossible de modifier l'année scolaire une fois clôturée",
    details={"year": 2024}
)
```

### `InvalidStateError` (409)
État invalide pour l'opération.

**Usage :**
```python
raise InvalidStateError("BROUILLON", "PUBLIE")
# → "État invalide : BROUILLON" avec détails sur l'état requis
```

### `BusinessLogicError` (409)
Violation de règle métier.

**Usage :**
```python
raise BusinessLogicError(
    "Un élève ne peut pas être inscrit deux fois dans la même classe cette année",
    details={"classe_id": 1, "annee_id": 2}
)
```

### `ConstraintError` (400)
Violation de contrainte de données.

**Usage :**
```python
raise ConstraintError("Clé étrangère", {"table": "inscriptions"})
```

### `InternalError` (500)
Erreur interne du serveur.

**Usage :**
```python
raise InternalError("génération du bulletin", {"trimestre_id": 1})
```

## Fonctions utilitaires (`validators.py`)

### `assert_found(obj, resource_type, identifier="")`
Vérifie qu'une ressource existe.

**Usage :**
```python
eleve = db.query(models.Eleves).filter_by(matricule=matricule).first()
assert_found(eleve, "Élève", matricule)  # Lève NotFoundError si None
```

### `assert_unique(db, query_result, resource_type, field, value)`
Vérifie l'unicité d'un champ.

**Usage :**
```python
existing = db.query(models.Utilisateurs).filter_by(email=email).first()
assert_unique(db, existing, "Utilisateur", "email", email)
```

### `assert_valid_email(email)`
Valide le format d'un email.

### `assert_valid_phone(phone)`
Valide le format d'un numéro de téléphone.

### `assert_active_school_year(db)`
Récupère et vérifie qu'une année scolaire active existe.

### `assert_user_can_write(user, required_roles)`
Vérifie les permissions d'écriture.

**Usage :**
```python
assert_user_can_write(current_user, ["admin", "directeur"])
```

### `assert_valid_status(status_value, valid_statuses)`
Valide qu'un statut fait partie des valeurs acceptées.

**Usage :**
```python
assert_valid_status(
    payload.statut,
    ["Inscrit", "Exclu", "Transféré"]
)
```

## Exemple complet

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from exceptions import (
    NotFoundError,
    ValidationError,
    ForbiddenError,
    DuplicateError,
)
from validators import assert_found, assert_valid_email
import models
import schemas

router = APIRouter()

@router.post("/eleves")
def creer_eleve(
    payload: schemas.EleveCreate,
    db: Session = Depends(get_db),
    current_user: models.Utilisateurs = Depends(get_current_user),
):
    # Validation
    assert_valid_email(payload.email)
    
    # Vérifier les doublons
    existing = db.query(models.Eleves).filter_by(email=payload.email).first()
    if existing:
        raise DuplicateError("Élève", "email", payload.email)
    
    # Vérifier la ressource liée
    classe = db.query(models.Classes).filter_by(id=payload.classe_id).first()
    assert_found(classe, "Classe", str(payload.classe_id))
    
    # Créer l'élève
    eleve = models.Eleves(**payload.dict())
    db.add(eleve)
    db.commit()
    
    return eleve
```

## Bonnes pratiques

1. **Toujours utiliser les exceptions personnalisées** plutôt que `HTTPException` brute
2. **Fournir des identifiants** pour `NotFoundError` quand c'est possible
3. **Inclure les détails pertinents** dans le champ `details`
4. **Valider les données** dès le début de la fonction
5. **Vérifier les permissions** avant les opérations
6. **Utiliser les assertions helper** pour les vérifications communes
7. **Journaliser les erreurs** importantes (l'exception handler le fait automatiquement)

## Codes d'erreur standard

| Code | HTTP | Signification |
|------|------|---|
| `NOT_FOUND` | 404 | Ressource introuvable |
| `VALIDATION_ERROR` | 422 | Données invalides |
| `DUPLICATE_ERROR` | 409 | Doublon détecté |
| `UNAUTHORIZED` | 401 | Authentification manquante ou incorrecte |
| `FORBIDDEN` | 403 | Accès refusé |
| `CONFLICT` | 409 | Conflit d'état |
| `INVALID_STATE` | 409 | État invalide |
| `BUSINESS_LOGIC_ERROR` | 409 | Violation de règle métier |
| `CONSTRAINT_ERROR` | 400 | Violation de contrainte |
| `INTERNAL_ERROR` | 500 | Erreur serveur |
| `INTERNAL_SERVER_ERROR` | 500 | Erreur interne (catch-all) |
