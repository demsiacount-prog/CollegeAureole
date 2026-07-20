from datetime import date
from pydantic import BaseModel
from typing import Optional


class PaiementBase(BaseModel):
    date: date
    montant: float
    numero_recu: Optional[str] = None
    mode: Optional[str] = None
    observation: Optional[str] = None


class PaiementCreate(PaiementBase):
    id_inscription: int


class PaiementResponse(PaiementBase):
    id: int
    id_inscription: int
    model_config = {"from_attributes": True}