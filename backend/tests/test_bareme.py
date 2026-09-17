"""Tests unitaires des règles de barème (bareme.py).

Vérifient la logique métier pure, sans base de données :
extraction du niveau, détection lycée, jardin d'enfants, barème 10/20,
mentions officielles maliennes et seuil de passage.
"""
import pytest

from bareme import (
    niveau_ordre,
    bareme_niveau,
    appreciation_for_moyenne,
    seuil_passage,
    est_jardin,
    est_6eme,
    est_ef1,
    utilise_coefficient,
    cycle_niveau,
    _est_lycee,
    jardin_suivant,
    SECTIONS_JARDIN,
)


class TestEstJardin:
    def test_reconnait_les_sections(self):
        for section in SECTIONS_JARDIN:
            assert est_jardin(section) is True, section

    def test_refuse_la_fondamentale_et_le_vide(self):
        assert est_jardin("1ère Année") is False
        assert est_jardin("7ème Année") is False
        assert est_jardin("") is False
        assert est_jardin(None) is False


class TestJardinSuivant:
    def test_progression_des_sections(self):
        assert jardin_suivant("Petite Section") == "Moyenne Section"
        assert jardin_suivant("Moyenne Section") == "Grande Section"

    def test_sortie_vers_la_premiere_annee(self):
        assert jardin_suivant("Grande Section") == "1ère Année"

    def test_refuse_les_niveaux_non_jardin(self):
        assert jardin_suivant("1ère Année") is None
        assert jardin_suivant("7ème Année") is None
        assert jardin_suivant("") is None
        assert jardin_suivant(None) is None


class TestCycleNiveau:
    def test_identifie_les_cycles(self):
        assert cycle_niveau("Petite Section") == "jardin"
        assert cycle_niveau("Grande Section") == "jardin"
        assert cycle_niveau("1ère Année") == "ef1"
        assert cycle_niveau("6ème Année") == "ef1"
        assert cycle_niveau("7ème Année") == "ef2"
        assert cycle_niveau("9ème Année") == "ef2"
        assert cycle_niveau("Seconde") == "lycee"
        assert cycle_niveau("Terminale") == "lycee"


class TestNiveauOrdre:
    def test_extrait_ordre_de_base(self):
        assert niveau_ordre("1ère") == 1
        assert niveau_ordre("6ème") == 6
        assert niveau_ordre("7ème") == 7
        assert niveau_ordre("9ème") == 9

    def test_lycee_en_deux_chiffres(self):
        assert niveau_ordre("10ème") == 10
        assert niveau_ordre("12ème") == 12

    def test_jardin_sans_ordre(self):
        for section in SECTIONS_JARDIN:
            assert niveau_ordre(section) is None, section

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
    def test_ef1_sur_10(self):
        # 1ère à 6ème année → barème 10
        assert bareme_niveau("1ère Année") == 10
        assert bareme_niveau("6ème Année") == 10

    def test_ef2_et_lycee_sur_20(self):
        assert bareme_niveau("7ème Année") == 20
        assert bareme_niveau("9ème Année") == 20
        assert bareme_niveau("Seconde") == 20
        assert bareme_niveau("Terminale") == 20

    def test_jardin_bascule_20(self):
        # Les sections du jardin ne sont pas notées : barème par défaut.
        for section in SECTIONS_JARDIN:
            assert bareme_niveau(section) == 20, section

    def test_bareme_niveau_sans_ordre_bascule_20(self):
        assert bareme_niveau("CP") == 20


class TestAppreciationForMoyenne:
    def test_barème_20(self):
        assert appreciation_for_moyenne(18, 20) == "Excellent"
        assert appreciation_for_moyenne(16.5, 20) == "Très bien"
        assert appreciation_for_moyenne(15, 20) == "Bien"
        assert appreciation_for_moyenne(13, 20) == "Assez bien"
        assert appreciation_for_moyenne(11, 20) == "Passable"
        assert appreciation_for_moyenne(8, 20) == "Insuffisant"

    def test_barème_10(self):
        assert appreciation_for_moyenne(9, 10) == "Excellent"
        assert appreciation_for_moyenne(6.5, 10) == "Assez bien"
        assert appreciation_for_moyenne(5, 10) == "Passable"
        assert appreciation_for_moyenne(4, 10) == "Insuffisant"

    def test_frontieres(self):
        # Mentions officielles (proportionnelles au barème).
        assert appreciation_for_moyenne(18, 20) == "Excellent"   # >= 90%
        assert appreciation_for_moyenne(16, 20) == "Très bien"   # 80-90%
        assert appreciation_for_moyenne(14, 20) == "Bien"        # 70-80%
        assert appreciation_for_moyenne(12, 20) == "Assez bien"  # 60-70%
        assert appreciation_for_moyenne(10, 20) == "Passable"    # 50-60%


class TestSeuilPassage:
    def test_moitie_du_bareme(self):
        assert seuil_passage(20) == 10.0
        assert seuil_passage(10) == 5.0


class TestEst6eme:
    def test_reconnait_la_6eme(self):
        assert est_6eme("6ème") is True
        assert est_6eme("6ème Année") is True

    def test_refuse_les_autres_niveaux(self):
        assert est_6eme("5ème") is False
        assert est_6eme("7ème") is False
        assert est_6eme("Seconde") is False
        assert est_6eme("Grande Section") is False
        assert est_6eme("") is False
        assert est_6eme(None) is False


class TestEstEf1:
    def test_identifie_le_premier_cycle(self):
        assert est_ef1("1ère Année") is True
        assert est_ef1("6ème Année") is True

    def test_refuse_ef2_lycee_et_jardin(self):
        assert est_ef1("7ème Année") is False
        assert est_ef1("Seconde") is False
        assert est_ef1("Grande Section") is False
        assert est_ef1("") is False
        assert est_ef1(None) is False


class TestUtiliseCoefficient:
    def test_compositions_toujours_en_moyenne_simple(self):
        assert utilise_coefficient("1ère Année", "COMPOSITION") is False
        assert utilise_coefficient("6ème Année", "COMPOSITION") is False

    def test_trimestres_ef1_sans_coefficient_sauf_6eme(self):
        assert utilise_coefficient("1ère Année", "TRIMESTRE") is False
        assert utilise_coefficient("6ème Année", "TRIMESTRE") is True

    def test_trimestres_ef2_et_lycee_ponderes(self):
        assert utilise_coefficient("7ème Année", "TRIMESTRE") is True
        assert utilise_coefficient("9ème Année", "TRIMESTRE") is True
        assert utilise_coefficient("Seconde", "TRIMESTRE") is True