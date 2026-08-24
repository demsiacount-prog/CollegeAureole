from datetime import date
from pydantic import BaseModel, Field
from typing import Optional

from schemas.echeances import ModePaiement


class RemiseCreate(BaseModel):
    montant: float = Field(gt=0)
    motif: Optional[str] = Field(default=None, max_length=500)
    date: date


class RemiseResponse(BaseModel):
    id: int
    id_echeance: int
    montant: float
    motif: Optional[str] = None
    utilisateur_id: Optional[int] = None
    utilisateur_nom: Optional[str] = None
    utilisateur_prenom: Optional[str] = None
    date: date
    model_config = {"from_attributes": True}


class PaiementGroupeCreate(BaseModel):
    id_tuteur: int
    montant_total: float = Field(gt=0)
    date: date
    mode: Optional[ModePaiement] = None
    observation: Optional[str] = Field(default=None, max_length=500)


class PaiementGroupeResponse(BaseModel):
    nb_enfants: int
    nb_paiements_crees: int
    reste_total: float
    model_config = {"from_attributes": True}
