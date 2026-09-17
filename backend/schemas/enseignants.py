from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class EnseignantBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str = Field(min_length=8, max_length=30, pattern=r"^\+?[\d\s\-()]{7,}$")
    adresse: str = Field(default="", max_length=300)
    specialite: str = Field(min_length=1, max_length=100)
    genre: Optional[str] = Field(default=None, max_length=10)
    nina: Optional[str] = Field(default=None, max_length=20)
    date_naissance: Optional[date] = None
    categorie: Optional[str] = Field(default=None, max_length=100)
    echelon: Optional[str] = Field(default=None, max_length=50)
    fonction: Optional[str] = Field(default=None, max_length=100)
    sf_nombre_enfants: Optional[str] = Field(default=None, max_length=50)
    date_contrat: Optional[date] = None
    classe_tenue: Optional[str] = Field(default=None, max_length=100)
    dernier_poste: Optional[str] = Field(default=None, max_length=150)
    date_arrivee_cap: Optional[date] = None
    diplome: Optional[str] = Field(default=None, max_length=150)
    observations: Optional[str] = Field(default=None, max_length=300)


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
