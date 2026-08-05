from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse
    from schemas.cours import CoursResponse


class ClasseBase(BaseModel):
    niveau: str
    nom: str
    frais_inscription: float = Field(default=0.0, ge=0)
    mensualite: float = Field(default=0.0, ge=0)


class ClasseCreate(ClasseBase):
    pass


class ClasseResponse(ClasseBase):
    id: int
    code_classe: Optional[str] = None
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}


class ClasseDetailResponse(ClasseResponse):
    eleves: List["EleveResponse"] = []
    cours: List["CoursResponse"] = []
    effectif_actuel: int = 0
