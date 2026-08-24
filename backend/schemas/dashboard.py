from pydantic import BaseModel
from typing import List

class MoyenneClasse(BaseModel):
    classe: str
    moy: float
    bareme: int

class RepartitionNiveau(BaseModel):
    name: str
    value: int

class AbsenceMois(BaseModel):
    mois: str
    absences: int

class ActiviteRecente(BaseModel):
    type: str
    texte: str
    date: str

class DashboardStatsResponse(BaseModel):
    nb_eleves: int
    nb_enseignants: int
    nb_classes: int
    taux_absence: float
    absences_7_jours: int
    paiements_mois: float
    moyennes_par_classe: List[MoyenneClasse]
    repartition_niveaux: List[RepartitionNiveau]
    absences_par_mois: List[AbsenceMois]
    dernieres_activites: List[ActiviteRecente]

    model_config = {"from_attributes": True}


class EvolutionMensuelle(BaseModel):
    mois: str
    paiements: float
    depenses: float


class DashboardFinanceResponse(BaseModel):
    """Tableau de bord du comptable : flux financiers uniquement."""
    paiements_mois: float
    depenses_mois: float
    solde_mois: float
    echeances_en_retard: int
    montant_en_retard: float
    evolution_mensuelle: List[EvolutionMensuelle]
    dernieres_activites: List[ActiviteRecente]

    model_config = {"from_attributes": True}