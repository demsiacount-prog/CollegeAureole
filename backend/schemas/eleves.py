from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional, TYPE_CHECKING
from schemas.tuteurs import TuteurResponse

if TYPE_CHECKING:
    from schemas.classes import ClasseResponse


class EleveBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    photo: Optional[str] = None
    date_de_naissance: date
    lieu_de_naissance: str = Field(min_length=1, max_length=200)
    sexe: Literal["M", "F"]
    adresse: Optional[str] = Field(default=None, max_length=300)
    statut: Literal["actif", "inactif"] = "actif"
    acte_naissance: bool = False
    carnet_sante: bool = False
    numero_acte: Optional[str] = Field(default=None, max_length=100)
    jugement_suppletif: Optional[str] = Field(default=None, max_length=100)
    date_acte: Optional[date] = None
    delivre_par: Optional[str] = Field(default=None, max_length=200)
    nom_pere: Optional[str] = Field(default=None, max_length=100)
    prenom_pere: Optional[str] = Field(default=None, max_length=100)
    fonction_pere: Optional[str] = Field(default=None, max_length=100)
    nom_mere: Optional[str] = Field(default=None, max_length=100)
    prenom_mere: Optional[str] = Field(default=None, max_length=100)
    fonction_mere: Optional[str] = Field(default=None, max_length=100)


class EleveCreate(EleveBase):
    tuteur_id: int
    # Classe optionnelle : un élève peut être inscrit sans classe (pré-inscription
    # en attente d'affectation) ; l'inscription est alors créée avec id_classe=None.
    classe_id: Optional[int] = None
    # Année scolaire d'inscription : sert au matricule AU{année}. Non persistée
    # sur l'élève (l'inscription reste la source). Repli : année active.
    annee_scolaire_id: Optional[int] = None


class EleveUpdate(BaseModel):
    """Modification partielle d'un élève (PUT par matricule).

    Champs facultatifs, validés comme à la création. Le matricule n'est JAMAIS
    modifiable : il est le numéro d'ordre annuel généré à la création."""
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    prenom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    photo: Optional[str] = None
    date_de_naissance: Optional[date] = None
    lieu_de_naissance: Optional[str] = Field(default=None, min_length=1, max_length=200)
    sexe: Optional[Literal["M", "F"]] = None
    adresse: Optional[str] = Field(default=None, max_length=300)
    statut: Optional[Literal["actif", "inactif"]] = None
    acte_naissance: Optional[bool] = None
    carnet_sante: Optional[bool] = None
    numero_acte: Optional[str] = Field(default=None, max_length=100)
    jugement_suppletif: Optional[str] = Field(default=None, max_length=100)
    date_acte: Optional[date] = None
    delivre_par: Optional[str] = Field(default=None, max_length=200)
    nom_pere: Optional[str] = Field(default=None, max_length=100)
    prenom_pere: Optional[str] = Field(default=None, max_length=100)
    fonction_pere: Optional[str] = Field(default=None, max_length=100)
    nom_mere: Optional[str] = Field(default=None, max_length=100)
    prenom_mere: Optional[str] = Field(default=None, max_length=100)
    fonction_mere: Optional[str] = Field(default=None, max_length=100)
    classe_id: Optional[int] = None


class EleveResponse(EleveBase):
    matricule: str
    created_at: datetime
    updated_at: datetime

    tuteur: TuteurResponse

    # Pydantic lit 'classe_relation' dans l'objet SQLAlchemy
    classe: Optional["ClasseResponse"] = Field(None, validation_alias="classe_relation")

    # Classe et statut de l'INSCRIPTION de l'année demandée (GET /api/eleves/
    # avec id_annee_scolaire, ou dossier avec année). Nuls sinon : signale que
    # l'élève n'est pas inscrit dans l'année consultée / qu'aucune année n'est
    # demandée. Ne reflète PAS l'état actuel (Eleves.classe_id / statut).
    classe_annee: Optional["ClasseResponse"] = None
    statut_annee: Optional[str] = None

    model_config = {"from_attributes": True}

# NE PAS appeler model_rebuild() ici — ClasseResponse pas encore défini à ce stade
