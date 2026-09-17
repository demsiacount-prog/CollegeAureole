from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field


class EtablissementUpdate(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    sigle: str | None = Field(default=None, max_length=50)
    devise: str | None = Field(default=None, max_length=200)
    adresse: str | None = Field(default=None, max_length=300)
    academie: str | None = Field(default=None, max_length=200)
    cap: str | None = Field(default=None, max_length=20)
    telephone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    logo: str | None = Field(default=None, max_length=500)
    village_quartier: str | None = Field(default=None, max_length=200)
    commune: str | None = Field(default=None, max_length=200)
    cercle: str | None = Field(default=None, max_length=200)
    statut_administratif: str | None = Field(default=None, max_length=50)
    type_ecole: str | None = Field(default=None, max_length=50)
    mode: str | None = Field(default=None, max_length=50)


class EtablissementResponse(EtablissementUpdate):
    id: int
    academie: str | None = None
    cap: str | None = None
    date_initialisation: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}
