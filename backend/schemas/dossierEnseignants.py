from pydantic import BaseModel
from typing import List, Optional

from schemas.enseignants import EnseignantResponse
from schemas.cours import CoursResponse
from schemas.annees_scolaires import AnneeScolaireResponse
from schemas.classes import ClasseResponse
from schemas.documents import DocumentResponse


# ─── Affectation : une classe + un cours pour une année donnée ────────────────
class AffectationResponse(BaseModel):
    """Un cours donné dans une classe pour une année scolaire."""
    classe: Optional[ClasseResponse] = None   # ✅ optionnel : cours sans classe assignée
    cours: CoursResponse

    model_config = {"from_attributes": True}


# ─── Bloc annuel : une année scolaire + ses affectations ─────────────────────
class HistoriqueAnneeResponse(BaseModel):
    """Toutes les affectations de l'enseignant pour une année scolaire."""
    annee_scolaire: Optional[AnneeScolaireResponse] = None  # ✅ optionnel : Cours sans FK annee_scolaire
    affectations: List[AffectationResponse] = []

    model_config = {"from_attributes": True}


# ─── Stats globales ───────────────────────────────────────────────────────────
class StatsEnseignantResponse(BaseModel):
    nb_annees: int = 0
    nb_classes_distinctes: int = 0
    nb_matieres_distinctes: int = 0

    model_config = {"from_attributes": True}


# ─── Dossier complet ──────────────────────────────────────────────────────────
class DossierEnseignantResponse(BaseModel):
    enseignant: EnseignantResponse
    stats: StatsEnseignantResponse
    historique: List[HistoriqueAnneeResponse] = []
    documents: List[DocumentResponse] = []

    model_config = {"from_attributes": True}


DossierEnseignantResponse.model_rebuild()