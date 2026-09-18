"""Schémas des documents de rentrée et de notes (doc1, doc5, doc6, doc7).

Ces modèles alimentent les endpoints JSON construits par services.effectifs.
"""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel


# ─── Classement des élèves (doc1) ─────────────────────────────────────────────

class ClassementEleve(BaseModel):
    inscription_id: int
    matricule: str
    nom: str
    prenom: str
    moyenne_annuelle: Optional[float]
    rang: Optional[int]
    observation: Optional[str] = None


class ClassementClasseResponse(BaseModel):
    id_classe: int
    niveau: str
    nom: str
    bareme: int
    effectif: int
    moyenne_classe: Optional[float]
    eleves: List[ClassementEleve]


class ClassementResponse(BaseModel):
    annee_label: str
    classes: List[ClassementClasseResponse]


# ─── Rapport succinct de rentrée (doc5) ───────────────────────────────────────

class RapportRentreeClasse(BaseModel):
    annee_etude: str
    groupes: int
    garcons: int
    filles: int
    total: int
    redoublants_g: int
    redoublants_f: int
    redoublants_total: int


class RapportRentreeCycle(BaseModel):
    cycle: str
    fe: int = 0
    fc: int = 0
    ce: int = 0
    cc: int = 0
    autres: int = 0
    em: int = 0
    total: int = 0


class RapportRentreeResponse(BaseModel):
    annee_label: str
    ecole: str
    village_quartier: Optional[str] = None
    commune: Optional[str] = None
    cap: Optional[str] = None
    cercle: Optional[str] = None
    ae: Optional[str] = None
    cycles: List[str]
    statuts: List[str]
    types_modes: List[str]
    classes: List[RapportRentreeClasse]
    total_garcons: int
    total_filles: int
    total_general: int
    total_redoublants_g: int
    total_redoublants_f: int
    total_redoublants: int
    premiers_cycle: RapportRentreeCycle
    second_cycle: RapportRentreeCycle
    nb_salles_1er: int
    nb_salles_2nd: int


# ─── Fiche de renseignements de rentrée (doc6) ────────────────────────────────

class FicheRenseignementsCellule(BaseModel):
    rc: int = 0
    garcons: int = 0
    filles: int = 0
    total: int = 0


class FicheRenseignementsLigne(BaseModel):
    libelle: str
    sept: FicheRenseignementsCellule
    huit: FicheRenseignementsCellule
    neuf: FicheRenseignementsCellule
    total: FicheRenseignementsCellule


class FicheRenseignementsPersonnel(BaseModel):
    prenom: str
    nom: str
    genre: Optional[str] = None
    nina: Optional[str] = None
    date_naissance: Optional[date] = None
    lieu_de_naissance: Optional[str] = None
    nationalite: Optional[str] = None
    situation_matrimoniale: Optional[str] = None
    categorie: Optional[str] = None
    classe: Optional[str] = None
    echelon: Optional[str] = None
    fonction: Optional[str] = None
    sf_nombre_enfants: Optional[str] = None
    date_contrat: Optional[date] = None
    classe_tenue: Optional[str] = None
    dernier_poste: Optional[str] = None
    date_arrivee_cap: Optional[date] = None
    observations: Optional[str] = None
    diplome: Optional[str] = None


class FicheRenseignementsResponse(BaseModel):
    annee_label: str
    academie: Optional[str] = None
    cap: Optional[str] = None
    ecole: str
    telephone: Optional[str] = None
    dirigee_par: Optional[str] = None
    effectifs: List[FicheRenseignementsLigne]
    personnel: List[FicheRenseignementsPersonnel]


# ─── Fiche de renseignements de rentrée, 1er cycle —───────────────────────────
# Tableau de bord recto/verso (1ère → 6ème année). Distinct de la fiche du 2nd
# cycle : la section effectifs compte 6 années + TOTAL (sous-colonnes N.C/G/F/T),
# s'ajoutent les infrastructures/mobiliers, et le personnel est ventilé entre
# personnel administratif (section II) et enseignant (section III).

class FicheRensPCLigne(BaseModel):
    libelle: str
    annee_1: FicheRenseignementsCellule
    annee_2: FicheRenseignementsCellule
    annee_3: FicheRenseignementsCellule
    annee_4: FicheRenseignementsCellule
    annee_5: FicheRenseignementsCellule
    annee_6: FicheRenseignementsCellule
    total: FicheRenseignementsCellule


class FicheRensPCPersonnel(BaseModel):
    prenom: str
    nom: str
    numero_mle: Optional[str] = None
    date_naissance: Optional[date] = None
    lieu_de_naissance: Optional[str] = None
    nationalite: Optional[str] = None
    situation_matrimoniale: Optional[str] = None
    grade: Optional[str] = None
    sf: Optional[str] = None
    nbre_enfants: Optional[str] = None
    fonction: Optional[str] = None
    date_recrutement: Optional[date] = None
    date_titularisation: Optional[date] = None
    date_dernier_avancement: Optional[date] = None
    dernier_poste: Optional[str] = None
    date_arrivee_cap: Optional[date] = None
    classe_tenue: Optional[str] = None
    observations: Optional[str] = None
    diplome: Optional[str] = None


class FicheRensPCInfrastructures(BaseModel):
    salles_dur: Optional[int] = None
    salles_semi_dur: Optional[int] = None
    salles_banco: Optional[int] = None
    salles_autres: Optional[int] = None
    direction_dur: Optional[int] = None
    direction_banco: Optional[int] = None
    direction_autres: Optional[int] = None
    logement_direction: Optional[int] = None
    tables_bancs: Optional[int] = None
    chaises: Optional[int] = None
    armoires: Optional[int] = None
    tableaux: Optional[int] = None
    mobilier_divers: Optional[int] = None


class FicheRenseignementsPremierCycleResponse(BaseModel):
    annee_label: str
    cap: Optional[str] = None
    commune: Optional[str] = None
    ecole: str
    village_quartier: Optional[str] = None
    dirige_par: Optional[str] = None
    telephone: Optional[str] = None
    effectifs: List[FicheRensPCLigne]
    personnel_admin: List[FicheRensPCPersonnel]
    personnel_enseignant: List[FicheRensPCPersonnel]
    infrastructures: Optional[FicheRensPCInfrastructures] = None


# ─── Fiche de notes de composition, 1er cycle (doc7) ──────────────────────────

class FicheNotesCompoMatiere(BaseModel):
    matiere: str
    note: Optional[float] = None
    coef: Optional[float] = None
    observation: Optional[str] = None


class FicheNotesCompoResponse(BaseModel):
    matricule: str
    nom: str
    prenom: str
    niveau: Optional[str]
    classe: Optional[str]
    bareme: int
    est_jardin: bool
    annee_label: str
    mois: Optional[str]
    matieres: List[FicheNotesCompoMatiere]
    total_notes: Optional[float]
    moyenne: Optional[float]
    rang: Optional[int]
    effectif: int
    moyenne_annuelle: Optional[float]
    rang_annuel: Optional[int]
    effectif_annuel: int