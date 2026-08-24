"""Fonctions de calcul des moyennes partagées entre les routers eleves et resultats.

Évite la duplication de _moyenne_annuelle (et dérivées) qui existedans
deux implémentations différentes (Python sum/len vs SQL func.avg).
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas


def calculer_moyenne_annuelle(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> Optional[float]:
    """Moyenne annuelle d'un élève (basée sur les bulletins trimestriels)."""
    result = (
        db.query(func.avg(models.Bulletins.moyenne_generale))
        .join(models.Trimestres, models.Bulletins.id_trimestre == models.Trimestres.id)
        .filter(
            models.Bulletins.matricule_eleve == matricule_eleve,
            models.Trimestres.annee_scolaire_id == id_annee_scolaire,
        )
        .scalar()
    )
    if result is not None:
        return round(float(result), 2)
    return None


def calculer_moyennes_par_trimestre(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> List["schemas.MoyenneTrimestre"]:
    """Moyenne de chaque trimestre pour un élève donné.

    Protégé contre les trimestres potentiellement dupliqués (même
    annee+nom mais ID différent) : agrège par nom pour ne renvoyer
    qu'une seule ligne par période.
    """
    trimestres = (
        db.query(models.Trimestres)
        .filter(models.Trimestres.annee_scolaire_id == id_annee_scolaire)
        .order_by(models.Trimestres.date_debut.asc())
        .all()
    )

    seen: dict[str, int] = {}
    resultats: List[schemas.MoyenneTrimestre] = []
    for trimestre in trimestres:
        if trimestre.nom in seen:
            continue
        seen[trimestre.nom] = 1

        bulletin = (
            db.query(models.Bulletins)
            .filter(
                models.Bulletins.matricule_eleve == matricule_eleve,
                models.Bulletins.id_trimestre == trimestre.id,
            )
            .first()
        )
        if bulletin is None:
            # Cherche un bulletin sur un trimestre doublon (même nom)
            bulletin = (
                db.query(models.Bulletins)
                .join(models.Trimestres, models.Bulletins.id_trimestre == models.Trimestres.id)
                .filter(
                    models.Bulletins.matricule_eleve == matricule_eleve,
                    models.Trimestres.annee_scolaire_id == id_annee_scolaire,
                    models.Trimestres.nom == trimestre.nom,
                )
                .first()
            )
        resultats.append(schemas.MoyenneTrimestre(
            numero=len(resultats) + 1,
            periode=trimestre.nom,
            moyenne=bulletin.moyenne_generale if bulletin else None,
        ))
    return resultats


def calculer_notes_par_matiere(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> List["schemas.NoteParMatiere"]:
    """Moyenne par matière d'un élève sur une année scolaire.

    Protégé contre les trimestres dupliqués : sous-requête pour ne
    prendre que les IDs uniques des trimestres de l'année.
    """
    trimestre_ids = (
        db.query(models.Trimestres.id)
        .filter(models.Trimestres.annee_scolaire_id == id_annee_scolaire)
        .subquery()
    )
    resultats = (
        db.query(models.Cours.nom, func.count(models.Notes.id), func.avg(models.Notes.note))
        .join(models.Notes, models.Notes.id_cours == models.Cours.id)
        .filter(
            models.Notes.matricule_eleve == matricule_eleve,
            models.Notes.id_trimestre.in_(db.query(trimestre_ids.c.id)),
        )
        .group_by(models.Cours.nom)
        .all()
    )
    return [
        schemas.NoteParMatiere(matiere=nom, nb_notes=nb, moyenne=round(float(moy), 2) if moy is not None else None)
        for nom, nb, moy in resultats
    ]
