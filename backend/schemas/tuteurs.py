from typing import List, Optional, TYPE_CHECKING
from pydantic import BaseModel, EmailStr

from schemas.documents import DocumentResponse

if TYPE_CHECKING:
    from schemas.eleves import EleveResponse

class TuteurBase(BaseModel):
    nom: str
    prenom: str
    email: EmailStr
    telephone: str
    adresse: str
    profession: str

class TuteurCreate(TuteurBase):
    pass

class TuteurResponse(TuteurBase):
    id: int
    code_tuteur: Optional[str] = None
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}

class TuteurDetailResponse(TuteurResponse):
    eleves: List["EleveResponse"] = []
    documents: List[DocumentResponse] = []