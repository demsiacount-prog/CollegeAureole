from pydantic import BaseModel
class NoteParMatiere(BaseModel):
    matiere: str
    nb_notes: int
    moyenne: float | None = None