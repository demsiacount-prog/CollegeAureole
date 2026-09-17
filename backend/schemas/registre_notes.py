from pydantic import BaseModel
from typing import List, Optional


class RegistreNoteLigne(BaseModel):
    id_trimestre: int
    nom: str
    note_comp: Optional[float] = None
    note_classe: Optional[float] = None
    moyenne: Optional[float] = None
    points: Optional[float] = None


class RegistreEleve(BaseModel):
    matricule: str
    nom: str
    prenom: str
    lignes: List[RegistreNoteLigne] = []
    moyenne_annuelle: Optional[float] = None


class RegistreTrimestre(BaseModel):
    id: int
    nom: str


class RegistreCours(BaseModel):
    id: int
    nom: str
    coefficient: float
    enseignant: Optional[dict] = None


class RegistreNotesResponse(BaseModel):
    classe: dict
    cours: RegistreCours
    annee_libelle: Optional[str] = None
    bareme: int = 20
    trimestres: List[RegistreTrimestre] = []
    eleves: List[RegistreEleve] = []