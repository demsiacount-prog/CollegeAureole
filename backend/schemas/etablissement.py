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

    model_config = {"extra": "forbid"}


class EtablissementResponse(EtablissementUpdate):
    id: int
    academie: str | None = None
    cap: str | None = None
    date_initialisation: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


def _int_field(**kwargs):
    from pydantic import Field
    return Field(default=None, ge=0, **kwargs)


class EtablissementInfrastructuresPayload(BaseModel):
    """Infrastructures et mobiliers de l'établissement pour une année scolaire
    (fiche de renseignements 1er cycle)."""

    id_annee_scolaire: int | None = None
    salles_dur: int | None = _int_field()
    salles_semi_dur: int | None = _int_field()
    salles_banco: int | None = _int_field()
    salles_autres: int | None = _int_field()
    direction_dur: int | None = _int_field()
    direction_banco: int | None = _int_field()
    direction_autres: int | None = _int_field()
    logement_direction: int | None = _int_field()
    tables_bancs: int | None = _int_field()
    chaises: int | None = _int_field()
    armoires: int | None = _int_field()
    tableaux: int | None = _int_field()
    mobilier_divers: int | None = _int_field()

    model_config = {"extra": "forbid"}


class EtablissementInfrastructuresResponse(EtablissementInfrastructuresPayload):
    id: int
    id_annee_scolaire: int | None
    model_config = {"from_attributes": True}
