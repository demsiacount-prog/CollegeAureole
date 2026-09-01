"""Tests unitaires des validateurs métier (validators.py).

Couvrent la logique indépendante de la base de données : unicité, email,
téléphone, statut, permissions d'écriture. Les fonctions qui requièrent une
session (assert_active_school_year) sont testées en intégration.
"""
import pytest

from validators import (
    assert_found,
    assert_unique,
    assert_valid_email,
    assert_valid_phone,
    assert_user_can_write,
    assert_valid_status,
)
from exceptions import NotFoundError, DuplicateError, ValidationError, ForbiddenError


class TestAssertFound:
    def test_retourne_objet_si_trouve(self):
        obj = object()
        assert assert_found(obj, "Ressource") is obj

    def test_leve_not_found_si_vide(self):
        with pytest.raises(NotFoundError):
            assert_found(None, "Ressource", "42")


class TestAssertUnique:
    def test_ok_si_aucun_doublon(self):
        # Ne lève rien quand query_result est vide.
        assert_unique(None, None, "Salles", "nom", "A")  # type: ignore

    def test_leve_si_doublon(self):
        with pytest.raises(DuplicateError):
            assert_unique(None, object(), "Salles", "nom", "A")  # type: ignore


class TestAssertValidEmail:
    def test_emails_valides(self):
        for email in ("a@b.fr", "prenom.nom@etablissement.com", "x.y+tag@sub.domain.org"):
            assert_valid_email(email)  # ne doit pas lever

    def test_emails_invalides(self):
        for email in ("", "pas-un-email", "a@", "@b.fr", "a b@c.fr", "a@b"):
            with pytest.raises(ValidationError):
                assert_valid_email(email)


class TestAssertValidPhone:
    def test_telephones_valides(self):
        for tel in ("0123456789", "+33 6 12 34 56 78", "(01) 23-45-67-89"):
            assert_valid_phone(tel)

    def test_telephones_invalides(self):
        for tel in ("", "12", "abc", "123"):
            with pytest.raises(ValidationError):
                assert_valid_phone(tel)


class TestAssertUserCanWrite:
    def test_autorise_les_roles_requis(self):
        class U:
            role = "admin"
        assert_user_can_write(U(), ["admin", "directeur"])

    def test_refuse_les_autres(self):
        class U:
            role = "comptable"
        with pytest.raises(ForbiddenError):
            assert_user_can_write(U(), ["admin", "directeur"])


class TestAssertValidStatus:
    def test_accepte_les_valeurs(self):
        assert_valid_status("actif", ["actif", "inactif"])

    def test_refuse_hors_liste(self):
        with pytest.raises(ValidationError):
            assert_valid_status("en_attente", ["actif", "inactif"])
