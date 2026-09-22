from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse
    from schemas.trimestres import TrimestreResponse
    from schemas.classes import ClasseResponse

StatutBulletin = Literal["BROUILLON", "PUBLIE"]


class BulletinErreurGenerer(BaseModel):
    """Un élève pour lequel le bulletin n'a pas pu être généré (motif explicite)."""
    matricule_eleve: str
    motif: str


class BulletinGenerationClasseResponse(BaseModel):
    """Réponse de génération par classe : bulletins produits + élèves en échec.

    La génération est partielle par nature (notes manquantes, garde jardin...) :
    on documente TOUT, jamais une simple liste qui masque les élèves perdus.
    """
    bulletins: List["BulletinResponse"] = []
    erreurs: List[BulletinErreurGenerer] = []
    nb_succes: int
    nb_erreurs: int


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
    moyenne_generale: Optional[float] = None  # None si aucune matière coefficientée (persisté tel quel, jamais de 0.0 fallacieux)
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
