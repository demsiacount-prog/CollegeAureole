from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.annees_scolaires import AnneeScolaireResponse


class TrimestreBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    type: Literal["TRIMESTRE", "COMPOSITION"] = "TRIMESTRE"
    date_debut: date
    date_fin: date

    @model_validator(mode="after")
    def verifier_dates(self):
        if self.date_fin <= self.date_debut:
            raise ValueError("Date de fin invalide")
        return self


class TrimestreCreate(TrimestreBase):
    annee_scolaire_id: int


class TrimestreResponse(TrimestreBase):
    id: int
    annee_scolaire_id: int
    verrouille: bool = False
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TrimestreDetailResponse(TrimestreResponse):
    annee_scolaire: "AnneeScolaireResponse"


class TrimestresGenererRequest(BaseModel):
    annee_scolaire_id: int


class TrimestresGenererResponse(BaseModel):
    cree: int
    annee_scolaire_id: int
