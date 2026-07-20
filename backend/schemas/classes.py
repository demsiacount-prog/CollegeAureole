from pydantic import BaseModel
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse
    from schemas.cours import CoursResponse


class ClasseBase(BaseModel):
    niveau: str
    nom: str
    frais_inscription: float = 0.0
    mensualite: float = 0.0
    capacite_max: Optional[int] = None


class ClasseCreate(ClasseBase):
    pass


class ClasseResponse(ClasseBase):
    id: int
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}


class ClasseDetailResponse(ClasseResponse):
    eleves: List["EleveResponse"] = []
    cours: List["CoursResponse"] = []
    effectif_actuel: int = 0
    places_restantes: Optional[int] = None
