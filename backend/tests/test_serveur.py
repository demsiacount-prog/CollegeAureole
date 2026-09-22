"""Tests du point d'entrée serveur (masquage des identifiants en logs)."""

from serveur import _url_masquee


def test_url_masquee_masque_le_mot_de_passe():
    url = "postgresql+psycopg2://johndoe:S3cre!t@localhost:5432/collegeaureole"
    assert (
        _url_masquee(url)
        == "postgresql+psycopg2://johndoe:*****@localhost:5432/collegeaureole"
    )


def test_url_masquee_preserve_hote_et_port():
    url = "postgresql+psycopg2://admin:pwd@127.0.0.1:5433/collegeaureole"
    assert (
        _url_masquee(url)
        == "postgresql+psycopg2://admin:*****@127.0.0.1:5433/collegeaureole"
    )


def test_url_masquee_sans_identifiants_inchangee():
    # Sans utilisateur/mot de passe dans la netloc, on ne touche pas à l'URL.
    url = "postgresql+psycopg2://collegeaureole"
    assert _url_masquee(url) == url