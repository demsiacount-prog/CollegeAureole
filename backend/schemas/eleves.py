from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING
from schemas.tuteurs import TuteurResponse

if TYPE_CHECKING:
    from schemas.classes import ClasseResponse

class EleveBase(BaseModel):
    nom: str
    prenom: str
    photo: Optional[str] = None
    date_de_naissance :str
    lieu_de_naissance : str
    sexe: str
    adresse: Optional[str] = None
    statut: str

class EleveCreate(EleveBase):
    tuteur_id: int
    classe_id: Optional[int] = None

class EleveResponse(EleveBase):
    matricule: str
    created_at: str
    updated_at: str

    tuteur: TuteurResponse

    # Pydantic lit 'classe_relation' dans l'objet SQLAlchemy
    classe: Optional["ClasseResponse"] = Field(None, validation_alias="classe_relation")

    model_config = {"from_attributes": True}

# NE PAS appeler model_rebuild() ici — ClasseResponse pas encore défini à ce stade
