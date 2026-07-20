from pydantic import BaseModel
from typing import Optional


class SalleBase(BaseModel):
    nom: str
    capacite: Optional[int] = None


class SalleCreate(SalleBase):
    pass


class SalleResponse(SalleBase):
    id: int
    created_at: str
    updated_at: str
    model_config = {"from_attributes": True}
