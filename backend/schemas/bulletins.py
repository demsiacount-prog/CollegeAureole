from datetime import datetime
from pydantic import BaseModel
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
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}


class BulletinGenerateRequest(BaseModel):
    matricule_eleve: str
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
    appreciation: Optional[str] = None
    statut: StatutBulletin = "BROUILLON"
    generated_at: datetime
    published_at: Optional[datetime] = None
    created_at: str
    updated_at: str
    details: List[BulletinDetailResponse] = []
    eleve: Optional[BulletinEleveResponse] = None
    model_config = {"from_attributes": True}


class BulletinDetailFullResponse(BulletinResponse):
    eleve: "EleveResponse"
    trimestre: "TrimestreResponse"
    classe: "ClasseResponse"
