from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class ElevePreview(BaseModel):
    matricule: str
    nom: str
    prenom: str
    classe_id: Optional[int] = None
    classe_nom: Optional[str] = None
    niveau: Optional[str] = None
    statut_passage: str = "EN_ATTENTE"
    diplome: bool = False
    action_prevue: str = ""
    inscription_id: int
    # Vrai quand l'élève admis n'a AUCUNE classe du niveau suivant : il ne
    # pourra pas être réinscrit au moment de la clôture. Rappel actif AVANT
    # l'exécution pour que l'admin crée la classe manquante.
    classe_manquante: bool = False


class CompteursPreview(BaseModel):
    ADMIS_PASSAGE: int = 0
    ADMIS_DIPLOME: int = 0
    RECALE_REDOUBLEMENT: int = 0
    EXCLU: int = 0
    EN_ATTENTE: int = 0


class AnneeInfo(BaseModel):
    id: int
    libelle: str


class CloturePreviewResponse(BaseModel):
    annee_active: Optional[AnneeInfo] = None
    total_eleves: int = 0
    blocants: int = 0
    peut_executer: bool = False
    cloturee: bool = False
    compteurs: CompteursPreview = CompteursPreview()
    eleves: List[ElevePreview] = []
    # Nb d'élèves admis sans classe de destination : à corriger avant clôture.
    nb_classes_manquantes: int = 0


class NouvelleAnneePayload(BaseModel):
    libelle: str
    date_debut: date
    date_fin: date

    model_config = {"extra": "forbid"}


class ClotureExecuterPayload(BaseModel):
    nouvelle_annee: NouvelleAnneePayload

    model_config = {"extra": "forbid"}


class EleveCloture(BaseModel):
    matricule: str
    nom: str
    prenom: str
    classe_nom: Optional[str] = None
    niveau: Optional[str] = None


class EleveErreurCloture(BaseModel):
    matricule: str
    nom: str
    prenom: str
    motif: str


class RapportCloture(BaseModel):
    admis_passage: int = 0
    admis_diplome: int = 0
    recale_redoublement: int = 0
    exclus: int = 0
    total_traites: int = 0
    eleves_admis_passage: List[EleveCloture] = []
    eleves_diplomes: List[EleveCloture] = []
    eleves_redoublants: List[EleveCloture] = []
    eleves_exclus: List[EleveCloture] = []
    # Élèves NON traités malgré une décision (doublon d'inscription, classe
    # suivante introuvable...) : à corriger manuellement après la clôture.
    # Ne jamais laisser cette liste non vue par l'admin.
    erreurs: List[EleveErreurCloture] = []
    # Dérivé de `erreurs` : exposé explicitement pour signaler facilement un
    # rattrapage à faire (bannière front, alerte persistée).
    nb_erreurs: int = 0


class ClotureExecuterResponse(BaseModel):
    succes: bool
    ancienne_annee: AnneeInfo
    nouvelle_annee: AnneeInfo
    rapport: RapportCloture


class ClotureAlerteRead(BaseModel):
    """Alerte persistée de rattrapage post-clôture (rappel actif)."""
    model_config = {"from_attributes": True}

    id: int
    id_annee_scolaire: int
    matricule: str
    nom: Optional[str] = None
    prenom: Optional[str] = None
    motif: str
    resolue: bool = False
    cree_le: datetime
    resolue_le: Optional[datetime] = None


class ClotureAlertesReponse(BaseModel):
    nb_en_attente: int = 0
    alertes: List[ClotureAlerteRead] = []
