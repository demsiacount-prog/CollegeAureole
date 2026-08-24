from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, EmailStr, Field

from schemas.documents import DocumentResponse

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse

class TuteurBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telephone: str = Field(min_length=8, max_length=30, pattern=r"^\+?[\d\s\-()]{7,}$")
    adresse: str = Field(default="", max_length=300)
    profession: str = Field(default="", max_length=100)

class TuteurCreate(TuteurBase):
    pass

class TuteurResponse(TuteurBase):
    id: int
    code_tuteur: Optional[str] = None
    # Tolère les champs vides ou absents en sortie : l'import de reprise
    # peut stocker '' (colonne NOT NULL) pour un parent sans email/téléphone.
    email: Optional[str] = None
    telephone: Optional[str] = None
    adresse: Optional[str] = None
    profession: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}

class TuteurDetailResponse(TuteurResponse):
    eleves: List["EleveResponse"] = []
    documents: List[DocumentResponse] = []
