from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse
    from schemas.cours import CoursResponse

from schemas.salles import SalleResponse


class ClasseBase(BaseModel):
    niveau: str = Field(min_length=1, max_length=50)
    nom: str = Field(min_length=1, max_length=100)
    frais_inscription: float = Field(default=0.0, ge=0)
    mensualite: float = Field(default=0.0, ge=0)
    id_salle: Optional[int] = None


class ClasseCreate(ClasseBase):
    pass


class ClasseResponse(ClasseBase):
    id: int
    code_classe: Optional[str] = None
    salle: Optional["SalleResponse"] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class ClasseDetailResponse(ClasseResponse):
    eleves: List["EleveResponse"] = []
    cours: List["CoursResponse"] = []
    effectif_actuel: int = 0
