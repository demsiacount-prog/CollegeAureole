import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/resultats", tags=["Résultats de passage"], dependencies=[Depends(get_current_user)])


def _niveau_ordre(niveau: str) -> Optional[int]:
    match = re.match(r"^(\d+)", niveau or "")
    return int(match.group(1)) if match else None


def _moyenne_annuelle(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> Optional[float]:
    bulletins = (
        db.query(models.Bulletins)
        .join(models.Trimestres, models.Bulletins.id_trimestre == models.Trimestres.id)
        .filter(
            models.Bulletins.matricule_eleve == matricule_eleve,
            models.Trimestres.annee_scolaire_id == id_annee_scolaire,
        )
        .all()
    )
    if not bulletins:
        return None
    return round(sum(b.moyenne_generale for b in bulletins) / len(bulletins), 2)


class EleveResultat(BaseModel):
    inscription_id: int
    matricule: str
    nom: str
    prenom: str
    photo: Optional[str] = None
    moyenne_annuelle: Optional[float] = None
    statut_passage: str


class ResultatsClasseResponse(BaseModel):
    classe: schemas.ClasseResponse
    niveau_ordre: Optional[int] = None
    effectif: int
    compteurs: dict
    eleves: List[EleveResultat]


class DetailRapportAuto(BaseModel):
    matricule: str
    nom: str
    moyenne: Optional[float] = None
    ancien_statut: str
    nouveau_statut: str


class RapportAutoResponse(BaseModel):
    classe: schemas.ClasseResponse
    seuil_applique: float
    est_fin_cycle: bool
    admis: int
    diplomes: int
    recales: int
    exclus_conserves: int
    en_attente: int
    detail: List[DetailRapportAuto]


def _annee_active(db: Session) -> models.AnneesScolaires:
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Aucune année scolaire active.")
    return annee


@router.get("/{id_classe}", response_model=ResultatsClasseResponse)
def get_resultats_classe(id_classe: int, db: Session = Depends(get_db)):
    classe = db.query(models.Classes).filter(models.Classes.id == id_classe).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable.")
    annee = _annee_active(db)

    inscriptions = db.query(models.Inscriptions).filter(
        models.Inscriptions.id_classe == id_classe,
        models.Inscriptions.id_annee_scolaire == annee.id,
    ).all()

    compteurs = {"EN_ATTENTE": 0, "ADMIS": 0, "RECALE": 0, "EXCLU": 0}
    eleves_out = []
    for insc in inscriptions:
        eleve = db.query(models.Eleves).filter(models.Eleves.matricule == insc.matricule_eleve).first()
        if not eleve:
            continue
        compteurs[insc.statut_passage] = compteurs.get(insc.statut_passage, 0) + 1
        eleves_out.append(EleveResultat(
            inscription_id=insc.id, matricule=eleve.matricule, nom=eleve.nom, prenom=eleve.prenom,
            photo=eleve.photo, moyenne_annuelle=_moyenne_annuelle(db, eleve.matricule, annee.id),
            statut_passage=insc.statut_passage,
        ))

    return ResultatsClasseResponse(
        classe=classe, niveau_ordre=_niveau_ordre(classe.niveau), effectif=len(inscriptions),
        compteurs=compteurs, eleves=eleves_out,
    )


@router.post("/{id_classe}/calcul-auto", response_model=RapportAutoResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def calculer_automatiquement(id_classe: int, db: Session = Depends(get_db)):
    classe = db.query(models.Classes).filter(models.Classes.id == id_classe).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable.")
    annee = _annee_active(db)
    niveau_ordre = _niveau_ordre(classe.niveau)
    if niveau_ordre is None:
        raise HTTPException(status_code=400, detail="Niveau de la classe non reconnu.")

    est_fin_cycle = niveau_ordre == 9
    seuil = 10.0  # moyenne toujours calculée /20 par les bulletins, quel que soit le niveau

    inscriptions = db.query(models.Inscriptions).filter(
        models.Inscriptions.id_classe == id_classe,
        models.Inscriptions.id_annee_scolaire == annee.id,
    ).all()

    admis = diplomes = recales = exclus_conserves = en_attente = 0
    detail = []

    for insc in inscriptions:
        eleve = db.query(models.Eleves).filter(models.Eleves.matricule == insc.matricule_eleve).first()
        if not eleve:
            continue
        ancien_statut = insc.statut_passage

        if ancien_statut == "EXCLU":
            exclus_conserves += 1
            detail.append(DetailRapportAuto(matricule=eleve.matricule, nom=f"{eleve.prenom} {eleve.nom}",
                                             moyenne=None, ancien_statut=ancien_statut, nouveau_statut="EXCLU"))
            continue

        moyenne = _moyenne_annuelle(db, eleve.matricule, annee.id)
        if moyenne is None:
            en_attente += 1
            detail.append(DetailRapportAuto(matricule=eleve.matricule, nom=f"{eleve.prenom} {eleve.nom}",
                                             moyenne=None, ancien_statut=ancien_statut, nouveau_statut="EN_ATTENTE"))
            continue

        if moyenne >= seuil:
            nouveau_statut = "ADMIS"
            insc.diplome = est_fin_cycle
            if est_fin_cycle:
                diplomes += 1
            else:
                admis += 1
        else:
            nouveau_statut = "RECALE"
            recales += 1

        insc.statut_passage = nouveau_statut
        detail.append(DetailRapportAuto(matricule=eleve.matricule, nom=f"{eleve.prenom} {eleve.nom}",
                                         moyenne=moyenne, ancien_statut=ancien_statut, nouveau_statut=nouveau_statut))

    db.commit()

    return RapportAutoResponse(
        classe=classe, seuil_applique=seuil, est_fin_cycle=est_fin_cycle,
        admis=admis, diplomes=diplomes, recales=recales,
        exclus_conserves=exclus_conserves, en_attente=en_attente, detail=detail,
    )


class StatutPassageRequest(BaseModel):
    statut: str  # "EN_ATTENTE" | "EXCLU" (transitions manuelles autorisées côté front)


@router.put("/statut/{inscription_id}", response_model=schemas.InscriptionResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def modifier_statut_passage(inscription_id: int, payload: StatutPassageRequest, db: Session = Depends(get_db)):
    insc = db.query(models.Inscriptions).filter(models.Inscriptions.id == inscription_id).first()
    if not insc:
        raise HTTPException(status_code=404, detail="Inscription introuvable.")
    if payload.statut not in ("EN_ATTENTE", "ADMIS", "RECALE", "EXCLU"):
        raise HTTPException(status_code=400, detail="Statut de passage invalide.")
    insc.statut_passage = payload.statut
    db.commit()
    db.refresh(insc)
    return insc
