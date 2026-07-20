from pydantic import BaseModel, EmailStr

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
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}