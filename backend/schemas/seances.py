from datetime import time
from typing import Literal, Optional, TYPE_CHECKING
from pydantic import BaseModel, model_validator

if TYPE_CHECKING:
    from schemas.cours import CoursResponse
    from schemas.classes import ClasseResponse
    from schemas.salles import SalleResponse

JourSemaine = Literal["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]


class SeanceBase(BaseModel):
    id_cours: int
    id_classe: int
    id_annee_scolaire: int
    id_salle: Optional[int] = None
    jour_semaine: JourSemaine
    heure_debut: time
    heure_fin: time

    @model_validator(mode="after")
    def verifier_horaires(self):
        if self.heure_fin <= self.heure_debut:
            raise ValueError("L'heure de fin doit être après l'heure de début.")
        return self


class SeanceCreate(SeanceBase):
    pass


class SeanceUpdate(BaseModel):
    id_cours: Optional[int] = None
    id_classe: Optional[int] = None
    id_salle: Optional[int] = None
    jour_semaine: Optional[JourSemaine] = None
    heure_debut: Optional[time] = None
    heure_fin: Optional[time] = None


class SeanceResponse(SeanceBase):
    id: int
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}


class SeanceDetailResponse(SeanceResponse):
    cours: Optional["CoursResponse"] = None
    classe: Optional["ClasseResponse"] = None
    salle: Optional["SalleResponse"] = None
