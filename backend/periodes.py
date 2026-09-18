"""Génération automatique du jeu de périodes par défaut d'une année scolaire.

Les classes de la 1ère à la 5ème année utilisent des compositions, la 6ème
(classe spéciale) combine trimestres + compositions intermédiaires, et les
classes supérieures (7ème-9ème, lycée) des trimestres : une année doit donc
posséder les deux types de périodes pour permettre la saisie des notes pour
tous les niveaux.
"""
from datetime import date, timedelta

import models

N_TRIMESTRES = 3
N_COMPOSITIONS = 9

MOIS_FRANCAIS = (
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
)


def _mois_composition(debut: date, fin: date) -> str:
    """Mois (en français) auquel appartient une composition.

    S'appuie sur le jour médian de la période : pour une année scolaire
    classique (≈ 1 mois par composition), chaque période tombe dans un mois
    distinct, alors que le mois de début peut se répéter (ex. deux périodes
    débutant en janvier).
    """
    milieu = debut + (fin - debut) // 2
    return MOIS_FRANCAIS[milieu.month - 1]


def _decouper_plage(debut: date, fin: date, n: int):
    """Découpe [debut, fin] en n plages contiguës sans chevauchement."""
    if n <= 0:
        return []
    total = max((fin - debut).days + 1, n)
    pas = max(total // n, 1)
    plages = []
    d = debut
    for _ in range(n):
        d_fin = min(d + timedelta(days=pas - 1), fin)
        plages.append((d, d_fin))
        d = d_fin + timedelta(days=1)
    return plages


def generer_periodes_par_defaut(db, annee_scolaire_id: int, date_debut: date, date_fin: date) -> int:
    """Crée les périodes par défaut manquantes (trimestres + compositions).

    Idempotent : un type déjà présent dans l'année n'est pas dupliqué.
    Retourne le nombre de périodes créées.
    """
    types_existants = {
        t.type
        for t in db.query(models.Trimestres)
        .filter(models.Trimestres.annee_scolaire_id == annee_scolaire_id)
        .all()
    }
    cree = 0

    if "TRIMESTRE" not in types_existants:
        for i, (debut, fin) in enumerate(_decouper_plage(date_debut, date_fin, N_TRIMESTRES), start=1):
            db.add(
                models.Trimestres(
                    nom=f"Trimestre {i}",
                    date_debut=debut,
                    date_fin=fin,
                    type="TRIMESTRE",
                    annee_scolaire_id=annee_scolaire_id,
                )
            )
            cree += 1

    if "COMPOSITION" not in types_existants:
        noms_utilises: set[str] = set()
        for i, (debut, fin) in enumerate(_decouper_plage(date_debut, date_fin, N_COMPOSITIONS), start=1):
            nom = f"Composition {_mois_composition(debut, fin)}"
            if nom in noms_utilises:
                nom = f"{nom} {i}"
            noms_utilises.add(nom)
            db.add(
                models.Trimestres(
                    nom=nom,
                    date_debut=debut,
                    date_fin=fin,
                    type="COMPOSITION",
                    annee_scolaire_id=annee_scolaire_id,
                )
            )
            cree += 1

    if cree:
        db.flush()
    return cree
