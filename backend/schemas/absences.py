from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse
    from schemas.cours import CoursResponse


class AbsenceBase(BaseModel):
    matricule_eleve: str = Field(min_length=1, max_length=20)
    id_cours: Optional[int] = None
    date_absence: date
    justifiee: bool = False
    motif: Optional[str] = Field(default=None, max_length=500)


class AbsenceCreate(AbsenceBase):
    pass


class AbsenceJustifierRequest(BaseModel):
    justifiee: bool
    motif: Optional[str] = Field(default=None, max_length=500)
    utilisateur_id: Optional[int] = None  # à remplacer par l'utilisateur authentifié une fois l'auth en place


class AbsenceResponse(AbsenceBase):
    id: int
    justifiee_par_id: Optional[int] = None
    date_justification: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    eleve: Optional["EleveResponse"] = None
    cours: Optional["CoursResponse"] = None
    model_config = {"from_attributes": True}


class AlerteAbsenceEleve(BaseModel):
    matricule_eleve: str
    nom: str
    prenom: str
    nb_absences_non_justifiees: int
