from datetime import date
from typing import List, Literal, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

from schemas.paiements import PaiementResponse
from schemas.noteParMatieres import NoteParMatiere
from schemas.tuteurs import TuteurCreate

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
    matricule_eleve: str = Field(min_length=1, max_length=20)
    id_classe: int
    id_annee_scolaire: int
    statut: StatutInscription = "Inscrit"
    montant_total: float = Field(default=0.0, ge=0)
    date_inscription: date = Field(default_factory=date.today)
    date_fin: Optional[date] = None
    observation: Optional[str] = Field(default=None, max_length=500)


class InscriptionCreate(InscriptionBase):
    pass


class InscriptionUpdate(BaseModel):
    id_classe: Optional[int] = None
    statut: Optional[StatutInscription] = None
    statut_passage: Optional[StatutPassage] = None
    diplome: Optional[bool] = None
    montant_total: Optional[float] = Field(default=None, ge=0)
    date_fin: Optional[date] = None
    observation: Optional[str] = Field(default=None, max_length=500)


class InscriptionResponse(InscriptionBase):
    id: int
    code_inscription: Optional[str] = None
    statut_passage: StatutPassage = "EN_ATTENTE"
    diplome: bool = False
    credit_disponible: float = 0.0
    eleve_nom: Optional[str] = None
    eleve_prenom: Optional[str] = None
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


class DossierCompletEleve(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    photo: Optional[str] = None
    date_de_naissance: date
    lieu_de_naissance: str = Field(min_length=1, max_length=200)
    sexe: Literal["M", "F"]
    adresse: str = Field(default="", max_length=300)
    statut: Literal["actif", "inactif"] = "actif"
    acte_naissance: bool = False
    carnet_sante: bool = False


class DossierCompletCreate(BaseModel):
    tuteur: Optional[TuteurCreate] = None
    tuteur_id: Optional[int] = None
    eleve: DossierCompletEleve
    classe_id: int
    id_annee_scolaire: int
    observation: Optional[str] = Field(default=None, max_length=500)


class PassageAnneeResponse(BaseModel):
    nb_inscriptions_creees: int
    nb_redoublants: int
    erreurs: List[str] = []
