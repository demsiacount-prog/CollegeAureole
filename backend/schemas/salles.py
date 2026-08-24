from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class SalleBase(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    capacite: Optional[int] = Field(default=None, ge=1)


class SalleCreate(SalleBase):
    pass


class SalleResponse(SalleBase):
    id: int
    code_salle: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
