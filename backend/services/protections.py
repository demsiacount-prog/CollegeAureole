"""
Couche de protection métier contre la suppression d'enregistrements
encore référencés par d'autres entités.

Chaque helper fait une **vérification explicite et préalable** (avant tout
`db.delete`) de la présence d'enregistrements dépendants, et lève une
HTTPException 409 avec un message lisible si l'entité ne peut pas être supprimée
sans perte de données (fiches, historiques, relations, etc.).

La logique est volontairement centralisée ici afin d'offrir un comportement
homogène sur tous les endpoints de suppression de l'application.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import models


def _bloquer(libelle: str, detail: str):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail or f"Impossible de supprimer {libelle} : des données y sont liées.")


def verifier_tuteur(db: Session, tuteur_id: int, nom: str = ""):
    nb = db.query(models.Eleves).filter(models.Eleves.tuteur_id == tuteur_id).count()
    if nb:
        _bloquer("ce tuteur", f"Impossible de supprimer ce tuteur : {nb} élève(s) lui sont affecté(s).")


def verifier_classe(db: Session, classe_id: int, nom: str = ""):
    nb_eleves = db.query(models.Eleves).filter(models.Eleves.classe_relation.has(id=classe_id)).count()
    nb_seances = db.query(models.Seances).filter(models.Seances.id_classe == classe_id).count()
    nb_inscriptions = db.query(models.Inscriptions).filter(models.Inscriptions.id_classe == classe_id).count()
    if nb_eleves or nb_seances or nb_inscriptions:
        _bloquer("cette classe", f"Impossible de supprimer cette classe : {nb_eleves} élève(s), {nb_inscriptions} inscription(s) et {nb_seances} séance(s) y sont lié(s).")


def verifier_salle(db: Session, salle_id: int, nom: str = ""):
    nb_classes = db.query(models.Classes).filter(models.Classes.id_salle == salle_id).count()
    nb_seances = db.query(models.Seances).filter(models.Seances.id_salle == salle_id).count()
    if nb_classes or nb_seances:
        _bloquer("cette salle", f"Impossible de supprimer cette salle : elle est affectée à {nb_classes} classe(s) et {nb_seances} séance(s).")


def verifier_cours(db: Session, cours_id: int, nom: str = ""):
    nb_seances = db.query(models.Seances).filter(models.Seances.id_cours == cours_id).count()
    nb_notes = db.query(models.Notes).filter(models.Notes.id_cours == cours_id).count()
    nb_affectations = db.query(models.AffectationCoursClasse).filter(models.AffectationCoursClasse.id_cours == cours_id).count()
    if nb_seances or nb_notes or nb_affectations:
        _bloquer("ce cours", f"Impossible de supprimer ce cours : il est lié à {nb_notes} note(s), {nb_seances} séance(s) et {nb_affectations} affectation(s).")


def verifier_enseignant(db: Session, matricule: str, nom: str = ""):
    nb_cours = db.query(models.Cours).filter(models.Cours.matricule_enseignant == matricule).count()
    nb_notes = db.query(models.Notes).filter(models.Notes.matricule_enseignant == matricule).count()
    if nb_cours or nb_notes:
        _bloquer("cet enseignant", f"Impossible de supprimer cet enseignant : il est lié à {nb_cours} cours et {nb_notes} note(s).")


def verifier_annee_scolaire(db: Session, annee_id: int, nom: str = ""):
    nb_inscriptions = db.query(models.Inscriptions).filter(models.Inscriptions.id_annee_scolaire == annee_id).count()
    nb_trimestres = db.query(models.Trimestres).filter(models.Trimestres.annee_scolaire_id == annee_id).count()
    nb_seances = db.query(models.Seances).filter(models.Seances.id_annee_scolaire == annee_id).count()
    if nb_inscriptions or nb_trimestres or nb_seances:
        _bloquer("cette année scolaire", f"Impossible de supprimer cette année scolaire : {nb_inscriptions} inscription(s), {nb_trimestres} trimestre(s) et {nb_seances} séance(s) y sont lié(s).")


def verifier_trimestre(db: Session, trimestre_id: int, nom: str = ""):
    nb_bulletins = db.query(models.Bulletins).filter(models.Bulletins.id_trimestre == trimestre_id).count()
    nb_notes = db.query(models.Notes).filter(models.Notes.id_trimestre == trimestre_id).count()
    if nb_bulletins or nb_notes:
        _bloquer("ce trimestre", f"Impossible de supprimer ce trimestre : il contient {nb_bulletins} bulletin(s) et {nb_notes} note(s).")
