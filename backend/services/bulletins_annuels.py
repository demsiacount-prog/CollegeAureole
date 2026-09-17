"""Données du bulletin annuel (3 blocs trimestriels) pour l'édition officielle.

Contrairement aux bulletins trimestriels stockés (qui ne retiennent que la
moyenne par matière), le bulletin annuel puise dans les notes brutes afin
d'afficher la note de classe et la note de composition de chaque période.
"""
import re
import unicodedata
from collections import defaultdict
from typing import Optional

from sqlalchemy.orm import Session

import models
from bareme import (
    appreciation_for_moyenne,
    bareme_niveau,
    est_bulletin_officiel,
    utilise_coefficient,
)


def _norm(s: str) -> str:
    """Normalise un nom de matière pour la correspondance flexible."""
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    s = s.lower()
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


# Matières du bulletin officiel (6è à 9è) — ordre et coefficients officiels.
# (nom_affiche, coefficient, italic)
MATIERES_BULLETIN_OFFICIEL = [
    ("Rédaction", 3, False),
    ("Ortho. Question", 2, False),
    ("Mathématique", 3, False),
    ("Physique – Chimie", 3, False),
    ("Anglais", 2, False),
    ("Biologie", 2, False),
    ("Histoire – Géographie", 2, False),
    ("ECM", 1, False),
    ("Éducation physique", 1, False),
    ("Musique", 1, False),
    ("Dessin", 1, False),
    ("Lecture", 1, False),
    ("Récitation", 1, False),
    ("Conduite", 1, False),
    ("Informatique", 1, True),
]


def moyenne_matiere(note_comp: Optional[float], note_classe: Optional[float]) -> Optional[float]:
    """Moyenne d'une matière sur une période : 60 % composition + 40 % classe.

    En l'absence de note de classe, la note de composition fait foi.
    """
    if note_comp is None:
        return None
    classe = note_classe if note_classe is not None else note_comp
    return round(0.6 * note_comp + 0.4 * classe, 2)


def _notes_par_cours(db: Session, matricule_eleve: str, id_trimestre: int) -> dict:
    rows = (
        db.query(models.Notes)
        .filter(
            models.Notes.matricule_eleve == matricule_eleve,
            models.Notes.id_trimestre == id_trimestre,
        )
        .all()
    )
    resultats = {}
    for n in rows:
        comp = float(n.note)
        classe = float(n.note_classe) if n.note_classe is not None else None
        resultats[n.id_cours] = {"note_comp": comp, "note_classe": classe}
    return resultats


def _moyennes_annuelles_classe(db: Session, id_classe: int, ids_trimestres: list[int]) -> dict:
    """Moyenne annuelle de chaque élève d'une classe (moyennes trimestrielles)."""
    bulletins = (
        db.query(models.Bulletins)
        .filter(
            models.Bulletins.id_classe == id_classe,
            models.Bulletins.id_trimestre.in_(ids_trimestres),
        )
        .all()
    )
    par_eleve: dict[str, list[float]] = defaultdict(list)
    for b in bulletins:
        if b.moyenne_generale is not None:
            par_eleve[b.matricule_eleve].append(float(b.moyenne_generale))
    return {
        matricule: sum(valeurs) / len(valeurs)
        for matricule, valeurs in par_eleve.items()
        if valeurs
    }


def _rang_annuel(moyennes: dict, matricule: str) -> Optional[int]:
    if matricule not in moyennes:
        return None
    ordre = sorted(moyennes.items(), key=lambda kv: kv[1], reverse=True)
    for index, (m, _) in enumerate(ordre, start=1):
        if m == matricule:
            return index
    return None


def bulletin_annuel(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> dict:
    """Construit la charge utile du bulletin annuel d'un élève."""
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule_eleve).first()
    if not eleve:
        raise ValueError("Élève introuvable")
    if not eleve.classe_id:
        raise ValueError("Aucune classe pour cet élève")

    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == id_annee_scolaire).first()
    if not annee:
        raise ValueError("Année scolaire introuvable")

    trimestres = (
        db.query(models.Trimestres)
        .filter(
            models.Trimestres.annee_scolaire_id == id_annee_scolaire,
            models.Trimestres.type == "TRIMESTRE",
        )
        .order_by(models.Trimestres.date_debut.asc())
        .all()
    )
    if not trimestres:
        return {
            "eleve": {"matricule": eleve.matricule, "nom": eleve.nom, "prenom": eleve.prenom},
            "classe": {"id": eleve.classe_id, "niveau": "", "nom": ""},
            "annee_libelle": annee.libelle,
            "bareme": 20,
            "trimestres": [],
            "statut": "AUCUN_TRIMESTRE",
        }

    ids_trimestres = [t.id for t in trimestres]
    moyennes_annuelles = _moyennes_annuelles_classe(db, eleve.classe_id, ids_trimestres)

    blocs = []
    for trimestre in trimestres:
        bulletin = (
            db.query(models.Bulletins)
            .filter(
                models.Bulletins.matricule_eleve == eleve.matricule,
                models.Bulletins.id_trimestre == trimestre.id,
            )
            .first()
        )
        id_classe = bulletin.id_classe if bulletin else eleve.classe_id
        classe = db.query(models.Classes).filter(models.Classes.id == id_classe).first()
        niveau = classe.niveau if classe else ""
        bareme = bareme_niveau(niveau) if classe else 20
        utilise_coeff = utilise_coefficient(niveau, trimestre.type)

        affectations = (
            db.query(models.AffectationCoursClasse)
            .filter(models.AffectationCoursClasse.id_classe == id_classe)
            .all()
        )
        coefficients = {a.id_cours: a.coefficient for a in affectations}
        cours_map = {
            c.id: c
            for c in db.query(models.Cours).filter(models.Cours.id.in_(coefficients.keys() or [0])).all()
        }

        effectif = (
            db.query(models.Bulletins)
            .filter(models.Bulletins.id_classe == id_classe, models.Bulletins.id_trimestre == trimestre.id)
            .count()
        )
        moyenne_premier = (
            db.query(models.Bulletins.moyenne_generale)
            .filter(models.Bulletins.id_classe == id_classe, models.Bulletins.id_trimestre == trimestre.id)
            .order_by(models.Bulletins.moyenne_generale.desc())
            .first()
        ) if effectif else None

        notes = _notes_par_cours(db, eleve.matricule, trimestre.id)
        is_officiel = est_bulletin_officiel(niveau)

        if is_officiel:
            cours_by_name = {}
            for id_cours, coeff in coefficients.items():
                cours = cours_map.get(id_cours)
                if cours:
                    cours_by_name[_norm(cours.nom)] = (id_cours, float(coeff))

            lignes = []
            totaux_coefficients = 0.0
            totaux_points = 0.0
            for idx, (tmpl_name, tmpl_coeff, _italic) in enumerate(MATIERES_BULLETIN_OFFICIEL):
                match = cours_by_name.get(_norm(tmpl_name))
                if match:
                    id_cours, db_coeff = match
                    data = notes.get(id_cours, {})
                    note_comp = data.get("note_comp")
                    note_classe = data.get("note_classe")
                    moyenne = moyenne_matiere(note_comp, note_classe)
                    points = (moyenne * db_coeff) if (moyenne is not None and utilise_coeff) else moyenne
                    if moyenne is not None:
                        totaux_coefficients += db_coeff
                        totaux_points += float(points or 0.0)
                    lignes.append({
                        "id_cours": id_cours,
                        "cours_nom": tmpl_name,
                        "coefficient": db_coeff,
                        "note_comp": note_comp,
                        "note_classe": note_classe,
                        "moyenne": moyenne,
                        "points": None if points is None else round(points, 2),
                        "appreciation": appreciation_for_moyenne(moyenne, bareme) if moyenne is not None else None,
                    })
                else:
                    lignes.append({
                        "id_cours": -(idx + 1),
                        "cours_nom": tmpl_name,
                        "coefficient": float(tmpl_coeff),
                        "note_comp": None,
                        "note_classe": None,
                        "moyenne": None,
                        "points": None,
                        "appreciation": None,
                    })
        else:
            lignes = []
            totaux_coefficients = 0.0
            totaux_points = 0.0
            for id_cours, coefficient in coefficients.items():
                cours = cours_map.get(id_cours)
                if not cours:
                    continue
                data = notes.get(id_cours, {})
                note_comp = data.get("note_comp")
                note_classe = data.get("note_classe")
                moyenne = moyenne_matiere(note_comp, note_classe)
                points = (moyenne * coefficient) if (moyenne is not None and utilise_coeff) else moyenne
                if moyenne is not None:
                    totaux_coefficients += float(coefficient)
                    totaux_points += float(points or 0.0)
                lignes.append({
                    "id_cours": id_cours,
                    "cours_nom": cours.nom,
                    "coefficient": float(coefficient),
                    "note_comp": note_comp,
                    "note_classe": note_classe,
                    "moyenne": moyenne,
                    "points": None if points is None else round(points, 2),
                    "appreciation": appreciation_for_moyenne(moyenne, bareme) if moyenne is not None else None,
                })

        blocs.append({
            "id_trimestre": trimestre.id,
            "nom": trimestre.nom,
            "type": trimestre.type,
            "id_classe": id_classe,
            "bareme": bareme,
            "moyenne_generale": float(bulletin.moyenne_generale) if bulletin and bulletin.moyenne_generale is not None else None,
            "rang": bulletin.rang if bulletin else None,
            "effectif": effectif,
            "moyenne_premier": float(moyenne_premier[0]) if moyenne_premier and moyenne_premier[0] is not None else None,
            "lignes": lignes,
            "totaux_coefficients": totaux_coefficients,
            "totaux_points": round(totaux_points, 2),
        })

    valeurs = [b["moyenne_generale"] for b in blocs if b["moyenne_generale"] is not None]
    moyenne_annuelle = round(sum(valeurs) / len(valeurs), 2) if valeurs else None
    bareme = (blocs[0]["bareme"] if blocs else 20)
    mention = appreciation_for_moyenne(moyenne_annuelle, bareme) if moyenne_annuelle is not None else None
    decision = _decision(moyenne_annuelle, bareme)

    classe = classe_actuelle(db, eleve)

    return {
        "eleve": {"matricule": eleve.matricule, "nom": eleve.nom, "prenom": eleve.prenom},
        "classe": {
            "id": eleve.classe_id,
            "niveau": classe.niveau if classe else "",
            "nom": classe.nom if classe else "",
        },
        "annee_libelle": annee.libelle,
        "bareme": bareme,
        "trimestres": blocs,
        "moyenne_annuelle": moyenne_annuelle,
        "rang_annuel": _rang_annuel(moyennes_annuelles, eleve.matricule),
        "mention_annuelle": mention,
        "decision": decision,
        "officiel": est_bulletin_officiel(classe.niveau if classe else None),
        "statut": "OK",
    }


def _decision(moyenne: Optional[float], bareme: int) -> str:
    if moyenne is None:
        return "—"
    if moyenne >= bareme / 2:
        return "Admis en classe supérieure"
    return "Redouble la classe"


def classe_actuelle(db: Session, eleve) -> Optional[models.Classes]:
    return db.query(models.Classes).filter(models.Classes.id == eleve.classe_id).first()