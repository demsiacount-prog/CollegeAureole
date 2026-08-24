from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse
    from schemas.trimestres import TrimestreResponse
    from schemas.classes import ClasseResponse

StatutBulletin = Literal["BROUILLON", "PUBLIE"]


class BulletinDetailResponse(BaseModel):
    id: int
    id_cours: int
    cours_nom: str
    moyenne: float
    coefficient: float  # remplace volume_horaire
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class BulletinGenerateRequest(BaseModel):
    matricule_eleve: str = Field(min_length=1, max_length=20)
    id_trimestre: int


class BulletinGenerateClasseRequest(BaseModel):
    id_classe: int
    id_trimestre: int


class BulletinPublierRequest(BaseModel):
    id_classe: int
    id_trimestre: int


class BulletinEleveResponse(BaseModel):
    matricule: str
    nom: str
    prenom: str
    photo: Optional[str] = None
    model_config = {"from_attributes": True}


class BulletinResponse(BaseModel):
    id: int
    matricule_eleve: str
    id_trimestre: int
    id_classe: int
    moyenne_generale: float
    rang: Optional[int] = None
    appreciation: Optional[str] = Field(default=None, max_length=1000)
    statut: StatutBulletin = "BROUILLON"
    generated_at: datetime
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    details: List[BulletinDetailResponse] = []
    eleve: Optional[BulletinEleveResponse] = None
    model_config = {"from_attributes": True}


class BulletinDetailFullResponse(BulletinResponse):
    eleve: "EleveResponse"
    trimestre: "TrimestreResponse"
    classe: "ClasseResponse"
