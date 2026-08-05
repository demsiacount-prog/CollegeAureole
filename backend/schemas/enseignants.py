from pydantic import BaseModel, EmailStr
from typing import Optional


class EnseignantBase(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    telephone: str
    adresse: str
    specialite: str
    heures_hebdo_max: Optional[float] = None


class EnseignantCreate(EnseignantBase):
    pass


class EnseignantResponse(EnseignantBase):
    matricule: str
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}
