from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UtilisateurBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: EmailStr


class UtilisateurConnexion(BaseModel):
    email: EmailStr
    mot_de_passe: str

    model_config = {"extra": "forbid"}


class UtilisateurChangerMotDePasse(BaseModel):
    ancien_mot_de_passe: str = Field(min_length=1)
    nouveau_mot_de_passe: str = Field(..., min_length=8)

    model_config = {"extra": "forbid"}


class UtilisateurCreate(UtilisateurBase):
    mot_de_passe: str = Field(..., min_length=8)
    role: str = Field(default="ADMIN", min_length=1, max_length=30)

    model_config = {"extra": "forbid"}


class UtilisateurStatutUpdate(BaseModel):
    actif: bool

    model_config = {"extra": "forbid"}


class UtilisateurReinitialiserMotDePasse(BaseModel):
    nouveau_mot_de_passe: str = Field(..., min_length=8)

    model_config = {"extra": "forbid"}


class UtilisateurResponse(UtilisateurBase):
    id: int
    role: str
    actif: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    utilisateur: UtilisateurResponse
