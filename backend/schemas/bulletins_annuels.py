from datetime import date, datetime
from pydantic import BaseModel
from typing import List, Optional


class BulletinAnnuelLigne(BaseModel):
    id_cours: int
    cours_nom: str
    coefficient: float
    note_comp: Optional[float] = None
    note_classe: Optional[float] = None
    moyenne: Optional[float] = None
    points: Optional[float] = None
    appreciation: Optional[str] = None


class BulletinAnnuelBloc(BaseModel):
    id_trimestre: int
    nom: str
    type: str
    id_classe: int
    bareme: int
    moyenne_generale: Optional[float] = None
    rang: Optional[int] = None
    effectif: Optional[int] = None
    moyenne_premier: Optional[float] = None
    lignes: List[BulletinAnnuelLigne] = []
    totaux_coefficients: float = 0.0
    totaux_points: float = 0.0


class BulletinAnnuelEleve(BaseModel):
    matricule: str
    nom: str
    prenom: str


class BulletinAnnuelClasse(BaseModel):
    id: int
    niveau: str
    nom: str


class BulletinAnnuelResponse(BaseModel):
    eleve: BulletinAnnuelEleve
    classe: BulletinAnnuelClasse
    annee_libelle: Optional[str] = None
    bareme: int = 20
    trimestres: List[BulletinAnnuelBloc] = []
    moyenne_annuelle: Optional[float] = None
    rang_annuel: Optional[int] = None
    mention_annuelle: Optional[str] = None
    decision: Optional[str] = None
    officiel: bool = False
    statut: str = "OK"
    date_edition: date = date.today()