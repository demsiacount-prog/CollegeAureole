from fastapi import HTTPException
from sqlalchemy.orm import Session
import models


def get_annee_ou_active(db: Session, annee_id: int | None = None) -> models.AnneesScolaires:
    """Résout l'année scolaire à utiliser pour une lecture.

    - annee_id fourni → charge cette année (active ou clôturée, lecture libre)
    - annee_id absent  → retourne l'année active (comportement historique)

    Ne bloque jamais sur cloturee : la lecture est toujours autorisée.
    C'est la réponse qui porte annee_cloturee=True pour signaler au client
    qu'il est en mode lecture seule.
    """
    if annee_id is not None:
        annee = db.query(models.AnneesScolaires).filter(
            models.AnneesScolaires.id == annee_id
        ).first()
        if not annee:
            raise HTTPException(status_code=404, detail="Année scolaire introuvable")
        return annee

    annee = db.query(models.AnneesScolaires).filter(
        models.AnneesScolaires.active == True  # noqa: E712
    ).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Aucune année scolaire active")
    return annee