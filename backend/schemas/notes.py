from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator
from typing import Optional, TYPE_CHECKING
from schemas.enseignants import EnseignantResponse

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse
    from schemas.cours import CoursResponse
    from schemas.classes import ClasseResponse
    from schemas.trimestres import TrimestreResponse

class NoteBase(BaseModel):
    note: Optional[float] = Field(default=None, ge=0.0, le=100.0)  # validated dynamically per-classe bareme in router
    note_classe: Optional[float] = Field(default=None, ge=0.0, le=100.0)  # nullable — moyenne matière = 60% note + 40% note_classe

    @model_validator(mode="after")
    def au_moins_une_note(self):
        """Au moins une des deux notes (composition ou classe) doit être fournie."""
        if self.note is None and self.note_classe is None:
            raise ValueError("Au moins une note (note ou note_classe) est requise")
        return self


class NoteCreate(NoteBase):
    matricule_eleve: str
    id_cours: int
    id_classe: int  # Requis pour contextualiser la note
    matricule_enseignant: str
    id_trimestre: int  # Requis : toute note doit être rattachée à une période (verrou globale par trimestre)

class NotePatch(BaseModel):
    """Mise à jour partielle (Type D — sauvegarde auto à chaque blur)."""
    note: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    note_classe: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    matricule_eleve: Optional[str] = None
    id_cours: Optional[int] = None
    id_classe: Optional[int] = None
    matricule_enseignant: Optional[str] = None
    id_trimestre: Optional[int] = None

class NoteBulkItem(NoteCreate):
    """Élément du lot (Type D — Enregistrer tout) : `id` présent → mise à jour, sinon création."""
    id: Optional[int] = None

class NoteBulkRequest(BaseModel):
    notes: list[NoteBulkItem]

class NoteBulkResponse(BaseModel):
    notes: list["NoteResponse"]
    creees: int
    modifiees: int

class NoteResponse(NoteBase):
    id: int
    date: date
    matricule_eleve: str
    id_cours: int
    id_classe: int
    matricule_enseignant: str
    id_trimestre: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    eleve: "EleveResponse"
    cours: "CoursResponse"
    classe: "ClasseResponse"
    enseignant: EnseignantResponse
    trimestre: Optional["TrimestreResponse"] = None
    peut_saisir: Optional[bool] = None  # False si le trimestre est verrouillé ou l'année clôturée
    model_config = {"from_attributes": True}


class NoteSaisieTrimestre(BaseModel):
    """État de saisie d'un trimestre pour la période active (verrouillage annuel)."""
    id: int
    nom: str
    type: str
    verrouille: bool
    annee_cloturee: bool
    peut_saisir: bool


class NoteSaisieAutoriseeResponse(BaseModel):
    """Réponse de GET /api/notes/saisie-autorisee : simplifie le blocage côté
    front (pastilles de saisie, messages) sans lire une note par note."""
    annee_id: int
    annee_libelle: Optional[str] = None
    annee_cloturee: bool
    trimestres: list[NoteSaisieTrimestre]
    peut_saisir: bool  # vrai si l'année est ouverte et qu'au moins un trimestre est saisissable

# NE PAS appeler model_rebuild() ici — dépendances pas encore définies à ce stade