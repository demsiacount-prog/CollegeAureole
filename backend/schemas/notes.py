from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING
from schemas.enseignants import EnseignantResponse

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse
    from schemas.cours import CoursResponse
    from schemas.classes import ClasseResponse
    from schemas.trimestres import TrimestreResponse

class NoteBase(BaseModel):
    note: float = Field(..., ge=0.0, le=100.0)  # validated dynamically per-classe bareme in router

class NoteCreate(NoteBase):
    matricule_eleve: str
    id_cours: int
    id_classe: int  # Requis pour contextualiser la note
    matricule_enseignant: str
    id_trimestre: Optional[int] = None  # Recommandé pour permettre la génération de bulletins

class NoteResponse(NoteBase):
    id: int
    date: str
    matricule_eleve: str
    id_cours: int
    id_classe: int
    matricule_enseignant: str
    id_trimestre: Optional[int] = None
    created_at: str
    updated_at: str
    eleve: "EleveResponse"
    cours: "CoursResponse"
    classe: "ClasseResponse"
    enseignant: EnseignantResponse
    trimestre: Optional["TrimestreResponse"] = None
    model_config = {"from_attributes": True}

# NE PAS appeler model_rebuild() ici — dépendances pas encore définies à ce stade
