from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enums import RoleUtilisateur


class UtilisateurBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: EmailStr


class UtilisateurInscription(UtilisateurBase):
    mot_de_passe: str = Field(..., min_length=8)
    role: RoleUtilisateur = RoleUtilisateur.COMPTABLE


class UtilisateurConnexion(BaseModel):
    email: EmailStr
    mot_de_passe: str


class UtilisateurUpdate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: RoleUtilisateur
    actif: bool = True


class UtilisateurChangerMotDePasse(BaseModel):
    ancien_mot_de_passe: str = Field(min_length=1)
    nouveau_mot_de_passe: str = Field(..., min_length=8)


class UtilisateurResponse(UtilisateurBase):
    id: int
    role: RoleUtilisateur
    actif: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    utilisateur: UtilisateurResponse
