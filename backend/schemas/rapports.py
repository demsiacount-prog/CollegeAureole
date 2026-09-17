from datetime import date
from typing import List, Optional
from pydantic import BaseModel

from schemas.noteParMatieres import NoteParMatiere
from schemas.inscriptions import MoyenneTrimestre


class ParcoursAnnee(BaseModel):
    annee_label: str
    classe: Optional[str]
    niveau: Optional[str]
    statut_passage: str
    moyenne_annuelle: Optional[float]


class FicheSuiviPassage(BaseModel):
    """Une des 7 périodes fixes du formulaire (classe × nème passage)."""
    niveau: str
    passage: int
    label: str
    annee_label: Optional[str]
    statut_passage: Optional[str]
    moyenne_annuelle: Optional[float]
    effectue: bool = False
    moyennes: List[Optional[float]] = []


class FicheSuiviLigne(BaseModel):
    matiere: str
    valeurs: List[Optional[float]] = []
    tendance: Optional[str] = None


class FicheSuiviResponse(BaseModel):
    matricule: str
    nom: str
    prenom: str
    date_de_naissance: Optional[date]
    lieu_de_naissance: str
    sexe: str
    adresse: Optional[str]
    pere: Optional[str] = None
    mere: Optional[str] = None
    niveau: Optional[str]
    classe: Optional[str]
    bareme: int
    est_jardin: bool
    transfert: bool
    annee_label: str
    moyenne_annuelle: Optional[float]
    rang: Optional[int]
    effectif: Optional[int]
    moyennes_trimestres: List[MoyenneTrimestre]
    notes_par_matiere: List[NoteParMatiere]
    colonnes: List[FicheSuiviPassage]
    lignes: List[FicheSuiviLigne]
    orientation: Optional[str] = None
    remarques: List[str] = []
    fois_x: int = 1
    nb_absences: int
    nb_absences_justifiees: int
    nb_absences_injustifiees: int
    parcours: List[ParcoursAnnee]


class EleveMoyenne(BaseModel):
    inscription_id: int
    matricule: str
    nom: str
    prenom: str
    moyenne_annuelle: Optional[float]
    rang: Optional[int]
    statut_passage: str


class ClasseMoyennes(BaseModel):
    id_classe: int
    niveau: str
    nom: str
    bareme: int
    effectif: int
    moyenne_classe: Optional[float]
    eleves: List[EleveMoyenne]


class RapportMoyennesResponse(BaseModel):
    annee_label: str
    classes: List[ClasseMoyennes]


class EleveProposition(BaseModel):
    inscription_id: int
    matricule: str
    nom: str
    prenom: str
    moyenne_annuelle: Optional[float]
    statut_actuel: str
    proposition: str


class ClasseProposition(BaseModel):
    id_classe: int
    niveau: str
    nom: str
    bareme: int
    seuil: float
    est_fin_cycle: bool
    effectif: int
    admis: int
    recales: int
    en_attente: int
    exclus: int
    eleves: List[EleveProposition]


class PropositionPassageResponse(BaseModel):
    annee_label: str
    classes: List[ClasseProposition]