from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, TYPE_CHECKING
from schemas.enseignants import EnseignantResponse

if TYPE_CHECKING:
    from schemas.classes import ClasseResponse


class AffectationCoursClasseInput(BaseModel):
    """Une classe dans laquelle le cours est enseigné, avec son coefficient."""
    id_classe: int
    coefficient: float = Field(1.0, gt=0, description="Coefficient de la matière pour CETTE classe")


class AffectationCoursClasseResponse(BaseModel):
    id_classe: int
    coefficient: float
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CoursBase(BaseModel):
    nom: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=500)
    volume_horaire: int = Field(ge=1)  # conservé pour l'emploi du temps uniquement


class CoursCreate(CoursBase):
    affectations: List[AffectationCoursClasseInput] = []
    matricule_enseignant: Optional[str] = None


class CoursResponse(CoursBase):
    id: int
    code_cours: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    matricule_enseignant: Optional[str] = None
    classes: List["ClasseResponse"] = []
    coefficients: List[AffectationCoursClasseResponse] = Field(default_factory=list, validation_alias="classes_affectations")
    enseignant: Optional[EnseignantResponse] = None
    model_config = {"from_attributes": True}
