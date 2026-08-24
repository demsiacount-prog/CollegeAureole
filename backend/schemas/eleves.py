from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Literal, Optional, TYPE_CHECKING
from schemas.tuteurs import TuteurResponse

if TYPE_CHECKING:
    from schemas.classes import ClasseResponse


class EleveBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    photo: Optional[str] = Field(default=None, max_length=500)
    date_de_naissance: date
    lieu_de_naissance: str = Field(min_length=1, max_length=200)
    sexe: Literal["M", "F"]
    adresse: Optional[str] = Field(default=None, max_length=300)
    statut: Literal["actif", "inactif"] = "actif"
    acte_naissance: bool = False
    carnet_sante: bool = False


class EleveCreate(EleveBase):
    tuteur_id: int
    classe_id: Optional[int] = None
    # Année scolaire d'inscription : sert au matricule EL{année}. Non persistée
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
