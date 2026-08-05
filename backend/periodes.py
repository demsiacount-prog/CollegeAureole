"""Génération automatique du jeu de périodes par défaut d'une année scolaire.

Les classes de la 1ère à la 6ème année utilisent des compositions, les
classes supérieures des trimestres : une année doit donc posséder les deux
types de périodes pour permettre la saisie des notes pour tous les niveaux.
"""
from datetime import date, timedelta

import models

N_TRIMESTRES = 3
N_COMPOSITIONS = 9


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
        for i, (debut, fin) in enumerate(_decouper_plage(date_debut, date_fin, N_COMPOSITIONS), start=1):
            db.add(
                models.Trimestres(
                    nom=f"Composition {i}",
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
