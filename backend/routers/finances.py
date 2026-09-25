# routers/finances.py
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models
import schemas
from security import get_current_user
from routers.paiements import _filtre_echeances_payables

router = APIRouter(prefix="/api/finances", tags=["Finances"], dependencies=[Depends(get_current_user)])


def _recapitulatif(db: Session, id_annee: Optional[int] = None,
                   date_debut=None, date_fin=None) -> schemas.RecapitulatifLocal:
    """Indicateurs financiers d'un périmètre : tout l'historique, ou une seule
    année scolaire. L'encaissé d'une année compte uniquement les versements
    rattachés aux inscriptions de cette année ; les dépenses sont celles dont
    la date tombe dans la fenêtre de l'année."""
    total_encaisse = db.query(func.coalesce(func.sum(models.Paiements.montant), 0.0))
    if id_annee is not None:
        total_encaisse = total_encaisse.join(
            models.Inscriptions, models.Inscriptions.id == models.Paiements.id_inscription
        ).filter(models.Inscriptions.id_annee_scolaire == id_annee)
    total_encaisse = float(total_encaisse.scalar() or 0.0)

    total_depenses = db.query(func.coalesce(func.sum(models.Depenses.montant), 0.0))
    if date_debut is not None:
        total_depenses = total_depenses.filter(
            models.Depenses.date >= date_debut, models.Depenses.date <= date_fin
        )
    total_depenses = float(total_depenses.scalar() or 0.0)

    echeances_impayees = (
        db.query(models.Echeances)
        .filter(_filtre_echeances_payables())
    )
    if id_annee is not None:
        echeances_impayees = echeances_impayees.filter(
            models.Echeances.id_inscription.in_(
                db.query(models.Inscriptions.id).filter(models.Inscriptions.id_annee_scolaire == id_annee)
            )
        )
    impayees = echeances_impayees.all()
    montant_impaye = round(
        sum(max(e.montant_du - e.montant_paye, 0.0) for e in impayees), 2
    )

    nb_soldees = db.query(func.count(models.Echeances.id)).filter(models.Echeances.statut == "SOLDE")
    if id_annee is not None:
        nb_soldees = nb_soldees.filter(
            models.Echeances.id_inscription.in_(
                db.query(models.Inscriptions.id).filter(models.Inscriptions.id_annee_scolaire == id_annee)
            )
        )

    return schemas.RecapitulatifLocal(
        total_encaisse=round(total_encaisse, 2),
        total_depenses=round(total_depenses, 2),
        solde=round(total_encaisse - total_depenses, 2),
        montant_impaye=montant_impaye,
        nb_echeances_impayees=len(impayees),
        nb_echeances_soldees=nb_soldees.scalar() or 0,
    )


@router.get("/recapitulatif", response_model=schemas.RecapitulatifFinancier)
def get_recapitulatif(db: Session = Depends(get_db)):
    """Synthèse de réconciliation école : encaissé, dépenses, solde et impayés,
    sur tout l'historique puis sur l'année scolaire active quand elle existe."""
    annee_active = (
        db.query(models.AnneesScolaires)
        .filter(models.AnneesScolaires.active.is_(True))
        .first()
    )
    annee = None
    if annee_active:
        annee = _recapitulatif(
            db,
            id_annee=annee_active.id,
            date_debut=annee_active.date_debut,
            date_fin=annee_active.date_fin,
        )
    return schemas.RecapitulatifFinancier(
        historique=_recapitulatif(db),
        annee=annee,
        annee_id=annee_active.id if annee_active else None,
        annee_libelle=annee_active.libelle if annee_active else None,
    )