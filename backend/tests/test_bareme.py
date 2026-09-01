"""Tests unitaires des règles de barème (bareme.py).

Vérifient la logique métier pure, sans base de données :
extraction du niveau, détection lycée, barème 10/20, appréciations et seuil.
"""
import pytest

from bareme import (
    niveau_ordre,
    bareme_niveau,
    appreciation_for_moyenne,
    seuil_passage,
    _est_lycee,
)


class TestNiveauOrdre:
    def test_extrait_ordre_de_base(self):
        assert niveau_ordre("1ère") == 1
        assert niveau_ordre("6ème") == 6
        assert niveau_ordre("7ème") == 7
        assert niveau_ordre("9ème") == 9

    def test_lycee_en_deux_chiffres(self):
        assert niveau_ordre("10ème") == 10
        assert niveau_ordre("12ème") == 12

    def test_sans_chiffre_renvoie_none(self):
        assert niveau_ordre("Terminale") is None
        assert niveau_ordre("") is None
        assert niveau_ordre(None) is None


class TestEstLycee:
    def test_continue_sur_annee_fondamentale(self):
        # « 1ère Année » / « 2ème Année » appartiennent à l'école fondamentale.
        assert _est_lycee("1ère Année") is False
        assert _est_lycee("2ème Année") is False
        assert _est_lycee("1ère an") is False

    def test_detecte_les_libelles_lycee(self):
        for libelle in ("Seconde", "2nde", "2de", "Première", "Premiere", "Terminale", "Tle", "1ère", "1re"):
            assert _est_lycee(libelle) is True, libelle

    def test_vide(self):
        assert _est_lycee("") is False
        assert _est_lycee(None) is False


class TestBaremeNiveau:
    def test_ef1_coin_sur_10(self):
        # 1ère à 6ème année → barème 10
        assert bareme_niveau("1ère Année") == 10
        assert bareme_niveau("6ème Année") == 10

    def test_ef2_et_lycee_sur_20(self):
        assert bareme_niveau("7ème Année") == 20
        assert bareme_niveau("9ème Année") == 20
        assert bareme_niveau("Seconde") == 20
        assert bareme_niveau("Terminale") == 20

    def test_bareme_niveau_sans_ordre_bascule_20(self):
        assert bareme_niveau("CP") == 20


class TestAppreciationForMoyenne:
    def test_barème_20(self):
        assert appreciation_for_moyenne(18, 20) == "Excellent"
        assert appreciation_for_moyenne(15, 20) == "Très bien"
        assert appreciation_for_moyenne(13, 20) == "Bien"
        assert appreciation_for_moyenne(11, 20) == "Passable"
        assert appreciation_for_moyenne(8, 20) == "Insuffisant"

    def test_barème_10(self):
        assert appreciation_for_moyenne(9, 10) == "Excellent"
        assert appreciation_for_moyenne(5, 10) == "Passable"
        assert appreciation_for_moyenne(4, 10) == "Insuffisant"

    def test_frontieres(self):
        assert appreciation_for_moyenne(16, 20) == "Excellent"  # >= 80%
        assert appreciation_for_moyenne(14, 20) == "Très bien"  # 70%
        assert appreciation_for_moyenne(12, 20) == "Bien"        # 60%
        assert appreciation_for_moyenne(10, 20) == "Passable"    # 50%


class TestSeuilPassage:
    def test_moitie_du_bareme(self):
        assert seuil_passage(20) == 10.0
        assert seuil_passage(10) == 5.0
