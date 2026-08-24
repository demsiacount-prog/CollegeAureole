from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field


class EtablissementUpdate(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    sigle: str | None = Field(default=None, max_length=50)
    devise: str | None = Field(default=None, max_length=200)
    adresse: str | None = Field(default=None, max_length=300)
    telephone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    logo: str | None = Field(default=None, max_length=500)


class EtablissementResponse(EtablissementUpdate):
    id: int
    date_initialisation: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}
