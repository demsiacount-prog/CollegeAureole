"""Tests unitaires du découpage des périodes (periodes.py).

Vérifie la fonction pure `_decouper_plage` (trimestres et compositions).
La génération des lignes en base (`generer_periodes_par_defaut`) est couverte
par les tests d'intégration.
"""
from datetime import date, timedelta

from periodes import _decouper_plage, N_TRIMESTRES, N_COMPOSITIONS


def test_decoupe_1_plage_couvre_la_plage():
    plages = _decouper_plage(date(2025, 9, 1), date(2025, 12, 31), 1)
    assert plages == [(date(2025, 9, 1), date(2025, 12, 31))]


def test_decoupe_3_trimestres_contigus_sans_chevauchenent():
    debut, fin = date(2025, 9, 1), date(2026, 6, 30)
    plages = _decouper_plage(debut, fin, N_TRIMESTRES)
    assert len(plages) == N_TRIMESTRES
    # Premier jour = début.
    assert plages[0][0] == debut
    # Aucune plage ne dépasse la fin de l'intervalle.
    for _, d_fin in plages:
        assert d_fin <= fin
    # Contiguïté : chaque plage commence le lendemain de la fin précédente.
    for (prec_debut, prec_fin), (debut_p, _) in zip(plages, plages[1:]):
        assert debut_p == prec_fin + timedelta(days=1)


def test_decoupe_9_compositions_conserve_les_bornes():
    debut, fin = date(2025, 9, 1), date(2026, 6, 30)
    plages = _decouper_plage(debut, fin, N_COMPOSITIONS)
    assert len(plages) == N_COMPOSITIONS
    assert plages[0][0] == debut
    # La dernière fin peut être antérieure à fin (division entière), jamais au-delà.
    for _, d_fin in plages:
        assert d_fin <= fin


def test_decoupe_n_zero_renvoie_vide():
    assert _decouper_plage(date(2025, 1, 1), date(2025, 1, 10), 0) == []


def test_decoupe_plus_de_plages_que_de_jours_se_replie():
    # Intervalle de 2 jours mais 5 plages demandées → pas = max(total//n, 1).
    plages = _decouper_plage(date(2025, 1, 1), date(2025, 1, 2), 5)
    assert len(plages) == 5
    assert plages[0][0] == date(2025, 1, 1)
    assert plages[-1][1] == date(2025, 1, 2)
