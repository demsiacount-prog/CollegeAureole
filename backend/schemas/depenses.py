# schemas/depenses.py
from datetime import date
from pydantic import BaseModel, Field
from typing import Optional, Literal

CategorieDepense = Literal[
    "SALAIRES","FOURNITURES","ENTRETIEN","ELECTRICITE","EAU",
    "COMMUNICATION","TRANSPORT","ALIMENTATION","MATERIEL","AUTRE"
]

class DepenseBase(BaseModel):
    libelle:     str
    montant:     float = Field(gt=0)
    categorie:   CategorieDepense = "AUTRE"
    date:        date
    description: Optional[str] = None

class DepenseCreate(DepenseBase):
    pass

class DepenseUpdate(BaseModel):
    libelle:     Optional[str]             = None
    montant:     Optional[float]           = None
    categorie:   Optional[CategorieDepense] = None
    date:        Optional[str]            = None
    description: Optional[str]            = None

class DepenseResponse(DepenseBase):
    id: int
    code_depense: Optional[str] = None
    model_config = {"from_attributes": True}