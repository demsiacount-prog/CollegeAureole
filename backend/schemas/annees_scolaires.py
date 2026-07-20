from datetime import date
from pydantic import BaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.trimestres import TrimestreResponse


class AnneeScolaireBase(BaseModel):
    libelle: str
    date_debut: date
    date_fin: date


class AnneeScolaireCreate(AnneeScolaireBase):
    active: bool = False


class AnneeScolaireResponse(AnneeScolaireBase):
    id: int
    active: bool
    cloturee: bool = False
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}


class AnneeScolaireDetailResponse(AnneeScolaireResponse):
    trimestres: List["TrimestreResponse"] = []
