from datetime import datetime
from typing import Annotated, List, Literal, Optional, TYPE_CHECKING, Union
from pydantic import BaseModel, EmailStr, Field, StringConstraints, field_validator

from schemas.documents import DocumentResponse

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse

# Email/téléphone : chaîne vide ('' stockée en base pour un parent importé sans
# coordonnées, colonne NOT NULL) OU valeur au format valide. Le format n'est
# contrôlé que lorsqu'une valeur non vide est fournie.
TypeEmail = Union[Literal[""], EmailStr]
TypeTelephone = Union[Literal[""], Annotated[str, StringConstraints(min_length=8, max_length=30, pattern=r"^\+?[\d\s\-()]{7,}$")]]


def _coordonnees_vide(value):
    """None (absent du payload) est cohérent avec '' : les deux signifient
    « pas de coordonnée » et sont stockés comme chaîne vide (colonne NOT NULL)."""
    if value is None:
        return ""
    return value


class TuteurBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: TypeEmail = ""
    telephone: TypeTelephone = ""
    adresse: str = Field(default="", max_length=300)
    profession: str = Field(default="", max_length=100)
    lien_parente: Optional[str] = Field(default=None, max_length=100)

    @field_validator("email", "telephone", mode="before")
    @classmethod
    def normaliser_coordonnees(cls, value):
        return _coordonnees_vide(value)

class TuteurCreate(TuteurBase):
    pass

class TuteurResponse(TuteurBase):
    id: int
    code_tuteur: Optional[str] = None
    # Tolère les champs vides ou absents en sortie : l'import de reprise
    # peut stocker '' (colonne NOT NULL) pour un parent sans email/téléphone.
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    profession: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class TuteurDetailResponse(TuteurResponse):
    eleves: List["EleveResponse"] = []
    documents: List[DocumentResponse] = []
