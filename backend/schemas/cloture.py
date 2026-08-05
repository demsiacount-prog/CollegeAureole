from datetime import date
from typing import List, Literal, Optional
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
    compteurs: CompteursPreview = CompteursPreview()
    eleves: List[ElevePreview] = []


class NouvelleAnneePayload(BaseModel):
    libelle: str
    date_debut: date
    date_fin: date


class ClotureExecuterPayload(BaseModel):
    nouvelle_annee: NouvelleAnneePayload


class RapportCloture(BaseModel):
    admis_passage: int = 0
    admis_diplome: int = 0
    recale_redoublement: int = 0
    exclus: int = 0
    total_traites: int = 0


class ClotureExecuterResponse(BaseModel):
    succes: bool
    ancienne_annee: AnneeInfo
    nouvelle_annee: AnneeInfo
    rapport: RapportCloture
