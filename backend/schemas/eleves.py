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
    classe_id: int
    # Année scolaire d'inscription : sert au matricule AU{année}. Non persistée
    # sur l'élève (l'inscription reste la source). Repli : année active.
    annee_scolaire_id: Optional[int] = None


class EleveResponse(EleveBase):
    matricule: str
    created_at: datetime
    updated_at: datetime

    tuteur: TuteurResponse

    # Pydantic lit 'classe_relation' dans l'objet SQLAlchemy
    classe: Optional["ClasseResponse"] = Field(None, validation_alias="classe_relation")

    model_config = {"from_attributes": True}

# NE PAS appeler model_rebuild() ici — ClasseResponse pas encore défini à ce stade
