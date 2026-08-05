from datetime import date
from pydantic import BaseModel
from typing import Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.annees_scolaires import AnneeScolaireResponse


class TrimestreBase(BaseModel):
    nom: str
    type: Literal["TRIMESTRE", "COMPOSITION"] = "TRIMESTRE"
    date_debut: date
    date_fin: date


class TrimestreCreate(TrimestreBase):
    annee_scolaire_id: int


class TrimestreResponse(TrimestreBase):
    id: int
    annee_scolaire_id: int
    verrouille: bool = False
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}


class TrimestreDetailResponse(TrimestreResponse):
    annee_scolaire: "AnneeScolaireResponse"


class TrimestresGenererRequest(BaseModel):
    annee_scolaire_id: int


class TrimestresGenererResponse(BaseModel):
    cree: int
    annee_scolaire_id: int
