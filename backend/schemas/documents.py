from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    matricule_eleve: Optional[str] = None
    matricule_enseignant: Optional[str] = None
    code_tuteur: Optional[str] = None
    type_document: str
    filename: str
    taille: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime

    model_config = {"from_attributes": True}
