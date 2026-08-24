from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.trimestres import TrimestreResponse


class AnneeScolaireBase(BaseModel):
    libelle: str = Field(min_length=1, max_length=100)
    date_debut: date
    date_fin: date

    @model_validator(mode="after")
    def verifier_dates(self):
        if self.date_fin <= self.date_debut:
            raise ValueError("Date de fin invalide")
        return self


class AnneeScolaireCreate(AnneeScolaireBase):
    active: bool = False


class AnneeScolaireResponse(AnneeScolaireBase):
    id: int
    active: bool
    cloturee: bool = False
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class AnneeScolaireDetailResponse(AnneeScolaireResponse):
    trimestres: List["TrimestreResponse"] = []
