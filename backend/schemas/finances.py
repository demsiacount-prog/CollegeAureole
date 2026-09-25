# schemas/finances.py
from pydantic import BaseModel
from typing import Optional


class RecapitulatifLocal(BaseModel):
    total_encaisse: float
    total_depenses: float
    solde: float
    montant_impaye: float
    nb_echeances_impayees: int
    nb_echeances_soldees: int


class RecapitulatifFinancier(BaseModel):
    historique: RecapitulatifLocal
    annee: Optional[RecapitulatifLocal] = None
    annee_id: Optional[int] = None
    annee_libelle: Optional[str] = None