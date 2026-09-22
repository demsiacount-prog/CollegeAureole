from datetime import date
from pydantic import BaseModel, Field
from typing import Optional


class PaiementBase(BaseModel):
    date: date
    montant: float = Field(gt=0)
    mode: Optional[str] = None
    observation: Optional[str] = None


class PaiementResponse(PaiementBase):
    id: int
    code_paiement: Optional[str] = None
    id_inscription: int
    # Le DB historique contient des paiements à montant 0 (échéances déjà
    # soldées passées en file EN_ATTENTE/PARTIEL) : on ne bloque pas la
    # lecture. La création reste strictement > 0.
    montant: float = Field(ge=0)
    matricule_eleve: Optional[str] = None
    eleve_nom: Optional[str] = None
    eleve_prenom: Optional[str] = None
    model_config = {"from_attributes": True}


class PaiementStatsResponse(BaseModel):
    """Synthèse payé / impayé de la page Paiements (tout l'historique)."""
    total_encaisse:        float
    montant_impaye:        float
    nb_echeances_soldees:  int
    nb_echeances_impayees: int


# ─── Mot de passe oublié ─────────────────────────────────────────────────────
# Hébergées dans schemas/auth.py (uniquement utilisées par routers/auth.py).
# Re-export pour compatibilité avec les imports existants.
from schemas.auth import (  # noqa: F401
    MotDePasseOublieRequest,
    MotDePasseOublieResponse,
    ReinitialiserMotDePasseRequest,
    ReinitialiserMotDePasseResponse,
)