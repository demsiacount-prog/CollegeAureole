from datetime import date
from typing import List, Literal, Optional, TYPE_CHECKING
from pydantic import BaseModel

from schemas.paiements import PaiementResponse
from schemas.noteParMatieres import NoteParMatiere

if TYPE_CHECKING:
    from schemas.classes import ClasseResponse
    from schemas.annees_scolaires import AnneeScolaireResponse
    from schemas.eleves import EleveResponse

StatutInscription = Literal["Inscrit", "Redoublant", "Transféré", "Exclu"]
StatutPassage = Literal["EN_ATTENTE", "ADMIS", "RECALE", "EXCLU"]


class MoyenneTrimestre(BaseModel):
    numero: int
    periode: str
    moyenne: Optional[float] = None


class InscriptionBase(BaseModel):
    matricule_eleve: str
    id_classe: Optional[int] = None
    id_annee_scolaire: int
    statut: StatutInscription = "Inscrit"
    montant_total: float = 0.0
    date_inscription: date = date.today()
    date_fin: Optional[date] = None
    observation: Optional[str] = None


class InscriptionCreate(InscriptionBase):
    pass


class InscriptionUpdate(BaseModel):
    id_classe: Optional[int] = None
    statut: Optional[StatutInscription] = None
    statut_passage: Optional[StatutPassage] = None
    diplome: Optional[bool] = None
    montant_total: Optional[float] = None
    date_fin: Optional[date] = None
    observation: Optional[str] = None


class InscriptionResponse(InscriptionBase):
    id: int
    statut_passage: StatutPassage = "EN_ATTENTE"
    diplome: bool = False
    credit_disponible: float = 0.0
    model_config = {"from_attributes": True}


class InscriptionDetailResponse(InscriptionResponse):
    classe: Optional["ClasseResponse"] = None
    annee_scolaire: Optional["AnneeScolaireResponse"] = None
    eleve: Optional["EleveResponse"] = None

    nb_absences: int = 0
    moyenne_annuelle: Optional[float] = None
    moyennes_par_trimestre: List[MoyenneTrimestre] = []
    paiements: List[PaiementResponse] = []
    montant_paye: float = 0.0
    reste_a_payer: float = 0.0
    notes_par_matiere: List[NoteParMatiere] = []


class PassageAnneeRequest(BaseModel):
    id_classe_origine: int
    id_annee_scolaire_origine: int
    id_annee_scolaire_destination: int
    id_classe_destination: Optional[int] = None
    matricules_redoublants: List[str] = []
    matricules_exclus: List[str] = []


class PassageAnneeResponse(BaseModel):
    nb_inscriptions_creees: int
    nb_redoublants: int
    erreurs: List[str] = []
