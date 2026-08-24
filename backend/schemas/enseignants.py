from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class EnseignantBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str = Field(min_length=8, max_length=30, pattern=r"^\+?[\d\s\-()]{7,}$")
    adresse: str = Field(default="", max_length=300)
    specialite: str = Field(min_length=1, max_length=100)


class EnseignantCreate(EnseignantBase):
    pass


class EnseignantResponse(EnseignantBase):
    matricule: str
    # Tolère les champs vides ou absents en sortie : l'import de reprise
    # peut stocker '' (colonne NOT NULL) pour un enseignant sans email/téléphone.
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    specialite: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
