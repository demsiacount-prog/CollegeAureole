"""Registre de notes : synthèse d'une matière pour une classe et une année.

Pour chaque élève et chaque période, la ligne affiche la note de composition,
la note de classe et la moyenne (60 % composition + 40 % classe, la note de
composition faisant foi en l'absence de note de classe). La moyenne annuelle
de l'élève est la moyenne simple des moyennes de période.
"""
from typing import Optional

from sqlalchemy.orm import Session

import models
from bareme import bareme_niveau, est_jardin, niveau_ordre, utilise_coefficient


def _periodes_classe(db: Session, id_classe: int, id_annee_scolaire: int) -> list[models.Trimestres]:
    """Périodes évaluées pour cette classe cette année.

    1ère-5ème : compositions ; 6ème : compositions + trimestres ; 7ème-9ème
    et lycée : trimestres. Les périodes d'un même nom ne comptent qu'une fois.
    """
    niveau = db.query(models.Classes.niveau).filter(models.Classes.id == id_classe).scalar()
    num = niveau_ordre(niveau) or 0

    queryset = db.query(models.Trimestres).filter(
        models.Trimestres.annee_scolaire_id == id_annee_scolaire,
    )
    if num and 1 <= num <= 5:
        queryset = queryset.filter(models.Trimestres.type == "COMPOSITION")
    elif num and num != 6:
        queryset = queryset.filter(models.Trimestres.type == "TRIMESTRE")

    periodes = queryset.order_by(models.Trimestres.date_debut.asc()).all()
    vus: set[str] = set()
    resultat: list[models.Trimestres] = []
    for t in periodes:
        if t.nom in vus:
            continue
        vus.add(t.nom)
        resultat.append(t)
    return resultat


def registre_notes(db: Session, id_classe: int, id_cours: int, id_annee_scolaire: int) -> dict:
    """Construit la charge utile du registre de notes d'une matière."""
    classe = db.query(models.Classes).filter(models.Classes.id == id_classe).first()
    if not classe:
        raise ValueError("Classe introuvable")
    if est_jardin(classe.niveau):
        raise ValueError("Le jardin d'enfants est évalué par appréciation, pas par notes.")
    cours = db.query(models.Cours).filter(models.Cours.id == id_cours).first()
    if not cours:
        raise ValueError("Matière introuvable")
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == id_annee_scolaire).first()
    if not annee:
        raise ValueError("Année scolaire introuvable")

    affectation = (
        db.query(models.AffectationCoursClasse)
        .filter(
            models.AffectationCoursClasse.id_classe == id_classe,
            models.AffectationCoursClasse.id_cours == id_cours,
        )
        .first()
    )
    coefficient = float(affectation.coefficient) if affectation else 1.0

    periodes = _periodes_classe(db, id_classe, id_annee_scolaire)
    ids_periodes = [t.id for t in periodes]

    eleves = (
        db.query(models.Eleves)
        .filter(models.Eleves.classe_id == id_classe)
        .order_by(models.Eleves.nom.asc(), models.Eleves.prenom.asc(), models.Eleves.matricule.asc())
        .all()
    )

    notes = (
        db.query(models.Notes)
        .filter(
            models.Notes.id_classe == id_classe,
            models.Notes.id_cours == id_cours,
            models.Notes.id_trimestre.in_(ids_periodes or [0]),
        )
        .all()
    )
    notes_par_eleve: dict[tuple[str, int], models.Notes] = {
        (n.matricule_eleve, n.id_trimestre): n for n in notes
    }

    bareme = bareme_niveau(classe.niveau)
    enseignant = "—"
    if cours.matricule_enseignant:
        enseignant = (
            db.query(models.Enseignants)
            .filter(models.Enseignants.matricule == cours.matricule_enseignant)
            .first()
        )

    resultat_eleves = []
    for eleve in eleves:
        lignes = []
        moyennes_periode: list[float] = []
        for periode in periodes:
            note = notes_par_eleve.get((eleve.matricule, periode.id))
            moyenne = None
            if note is not None:
                comp = float(note.note)
                classe_note = float(note.note_classe) if note.note_classe is not None else None
                classe_eff = classe_note if classe_note is not None else comp
                moyenne = round(0.6 * comp + 0.4 * classe_eff, 2)
                if moyenne is not None:
                    moyennes_periode.append(moyenne)
            utilise_coeff = utilise_coefficient(classe.niveau, periode.type)
            points = moyenne * coefficient if (moyenne is not None and utilise_coeff) else moyenne
            lignes.append({
                "id_trimestre": periode.id,
                "nom": periode.nom,
                "note_comp": float(note.note) if note is not None else None,
                "note_classe": float(note.note_classe) if (note is not None and note.note_classe is not None) else None,
                "moyenne": moyenne,
                "points": None if points is None else round(points, 2),
            })
        resultat_eleves.append({
            "matricule": eleve.matricule,
            "nom": eleve.nom,
            "prenom": eleve.prenom,
            "lignes": lignes,
            "moyenne_annuelle": round(sum(moyennes_periode) / len(moyennes_periode), 2)
            if moyennes_periode
            else None,
        })

    return {
        "classe": {"id": id_classe, "niveau": classe.niveau, "nom": classe.nom},
        "cours": {
            "id": cours.id,
            "nom": cours.nom,
            "coefficient": coefficient,
            "enseignant": (
                {"matricule": enseignant.matricule, "nom": enseignant.nom, "prenom": enseignant.prenom}
                if enseignant != "—"
                else None
            ),
        },
        "annee_libelle": annee.libelle,
        "bareme": bareme,
        "trimestres": [{"id": t.id, "nom": t.nom} for t in periodes],
        "eleves": resultat_eleves,
    }