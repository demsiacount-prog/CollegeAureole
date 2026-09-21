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
    # FIX BUG CRITIQUE (perte de données) : Notes.id_classe et Bulletins.id_classe
    # sont en ondelete="CASCADE". Une classe sans élève/inscription/séance ACTUELS
    # peut pourtant porter des notes et bulletins d'années passées : sans ce
    # contrôle, la supprimer effaçait silencieusement tout cet historique.
    nb_notes = db.query(models.Notes).filter(models.Notes.id_classe == classe_id).count()
    nb_bulletins = db.query(models.Bulletins).filter(models.Bulletins.id_classe == classe_id).count()
    if nb_eleves or nb_seances or nb_inscriptions or nb_notes or nb_bulletins:
        _bloquer(
            "cette classe",
            f"Impossible de supprimer cette classe : {nb_eleves} élève(s), {nb_inscriptions} inscription(s), "
            f"{nb_seances} séance(s), {nb_notes} note(s) et {nb_bulletins} bulletin(s) y sont lié(s).",
        )


def verifier_salle(db: Session, salle_id: int, nom: str = ""):
    nb_classes = db.query(models.Classes).filter(models.Classes.id_salle == salle_id).count()
    nb_seances = db.query(models.Seances).filter(models.Seances.id_salle == salle_id).count()
    if nb_classes or nb_seances:
        _bloquer("cette salle", f"Impossible de supprimer cette salle : elle est affectée à {nb_classes} classe(s) et {nb_seances} séance(s).")


def verifier_cours(db: Session, cours_id: int, nom: str = ""):
    nb_seances = db.query(models.Seances).filter(models.Seances.id_cours == cours_id).count()
    nb_notes = db.query(models.Notes).filter(models.Notes.id_cours == cours_id).count()
    nb_affectations = db.query(models.AffectationCoursClasse).filter(models.AffectationCoursClasse.id_cours == cours_id).count()
    # FIX BUG CRITIQUE (perte de données) : BulletinDetails.id_cours est en
    # ondelete="CASCADE". Un cours sans note/séance/affectation actuelle peut
    # encore apparaître comme ligne de matière sur d'anciens bulletins déjà
    # émis : sans ce contrôle, le supprimer effaçait cette ligne silencieusement.
    nb_details_bulletins = db.query(models.BulletinDetails).filter(models.BulletinDetails.id_cours == cours_id).count()
    if nb_seances or nb_notes or nb_affectations or nb_details_bulletins:
        _bloquer(
            "ce cours",
            f"Impossible de supprimer ce cours : il est lié à {nb_notes} note(s), {nb_seances} séance(s), "
            f"{nb_affectations} affectation(s) et {nb_details_bulletins} ligne(s) de bulletin.",
        )


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


def verifier_eleve(db: Session, matricule: str, nom: str = ""):
    """Garde la suppression d'un élève : toute l'arborescence CASCADE
    (inscriptions → paiements/échéances/remises, bulletins + détails, notes,
    absences, documents) serait effacée irrémédiablement avec lui. Un élève
    ne doit donc être supprimé que s'il n'a aucune donnée liée (fiche vierge,
    jamais inscrit). Si l'entité doit être retirée du circuit scolaire actif,
    l'API offre desactiver_eleve / activer_eleve (statut) qui conservent
    l'historique.

    La vérification est explicite et préalable (avant tout db.delete), comme
    pour les autres entités du module. Elle devra être appelée par tout
    futur endpoint de suppression d'élève jusqu'à ce qu'un guard applicatif
    homologue existe (la FK `inscriptions.matricule_eleve ON DELETE CASCADE`
    est protégée au niveau base, mais cette couche rend la règle lisible et
    testable)."""
    libelle = nom or matricule
    nb_inscriptions = db.query(models.Inscriptions).filter(models.Inscriptions.matricule_eleve == matricule).count()
    nb_notes = db.query(models.Notes).filter(models.Notes.matricule_eleve == matricule).count()
    nb_absences = db.query(models.Absences).filter(models.Absences.matricule_eleve == matricule).count()
    nb_bulletins = db.query(models.Bulletins).filter(models.Bulletins.matricule_eleve == matricule).count()
    nb_documents = db.query(models.Documents).filter(models.Documents.matricule_eleve == matricule).count()

    if nb_notes or nb_absences or nb_bulletins or nb_inscriptions or nb_documents:
        # Les paiements/échéances/remises suivent les inscriptions : ils sont
        # implicitement comptés dans nb_inscriptions.
        _bloquer(
            "cet élève",
            f"Impossible de supprimer {libelle} : son historique conserve "
            f"{nb_inscriptions} inscription(s) (avec leurs paiements et échéances), "
            f"{nb_notes} note(s), {nb_absences} absence(s), {nb_bulletins} bulletin(s) "
            f"et {nb_documents} document(s). Désactivez le compte plutôt que de supprimer.",
        )
