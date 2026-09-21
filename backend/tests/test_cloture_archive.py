"""Tests : l'archive complète ne se déclenche plus qu'à la clôture d'année.

Comportement attendu : la sauvegarde automatique au démarrage a été supprimée
(main.py) ; la clôture est désormais le SEUL moment où une archive complète
est créée automatiquement (sauvegardes.sauvegarde_cloture). Un échec
d'écriture annule la clôture.
"""
import os
from datetime import date
from unittest import mock

import pytest

import models


def _creer_tuteur(client, auth_headers):
    return client.post("/api/tuteurs/", json={
        "nom": "T", "prenom": "T", "email": "t@ex.com",
        "telephone": "+22376000000", "adresse": "Bamako", "profession": "M",
    }, headers=auth_headers)


def _creer_classe(client, auth_headers, niveau="Petite Section", nom="A"):
    return client.post("/api/classes/", json={"niveau": niveau, "nom": nom}, headers=auth_headers)


def _creer_annee(client, auth_headers, libelle="2025-2026"):
    return client.post("/api/anneesScolaires/", json={
        "libelle": libelle, "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers)


def _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur_id, classe_id, annee_id):
    eleve = models.Eleves(
        nom="Konaté", prenom="Amadou",
        date_de_naissance=date(2018, 3, 15),
        lieu_de_naissance="Bamako", sexe="M",
        tuteur_id=tuteur_id,
    )
    db_session.add(eleve)
    db_session.commit()
    db_session.refresh(eleve)
    resp = client.post("/api/inscriptions/", json={
        "matricule_eleve": eleve.matricule,
        "id_classe": classe_id,
        "id_annee_scolaire": annee_id,
    }, headers=auth_headers)
    assert resp.status_code in (200, 201), resp.text
    return eleve


_PAYLOAD = {"nouvelle_annee": {"libelle": "2026-2027", "date_debut": "2026-09-01", "date_fin": "2027-06-30"}}


def _cloturer(client, auth_headers):
    return client.post("/api/cloture/executer", json=_PAYLOAD, headers=auth_headers)


class TestArchiveALaCloture:
    def test_cloture_ecrit_une_archive_complete(self, client, auth_headers, db_session, tmp_path):
        """En dehors des tests, la clôture écrit bien un fichier .zip dans le
        dossier des sauvegardes, AVANT le passage à la nouvelle année."""
        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section").json()
        ms = _creer_classe(client, auth_headers, niveau="Moyenne Section").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"])

        with mock.patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "AUREOLE_SAUVEGARDES_DIR": str(tmp_path),
        }):
            resp = _cloturer(client, auth_headers)
            assert resp.status_code == 200, resp.text

        archives = list(tmp_path.glob("collegeaureole_sauvegarde_*.zip"))
        assert len(archives) == 1, "la clôture doit écrire exactement une archive"
        assert archives[0].stat().st_size > 0

        db_session.expire_all()
        ancienne = db_session.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee["id"]).first()
        assert ancienne.cloturee is True
        assert ancienne.active is False

    def test_aucune_archive_en_environnement_test(self, client, auth_headers, db_session, tmp_path):
        """Aucun fichier n'est écrit pendant les tests (base en mémoire)."""
        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section").json()
        ms = _creer_classe(client, auth_headers, niveau="Moyenne Section").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"])

        with mock.patch.dict(os.environ, {"AUREOLE_SAUVEGARDES_DIR": str(tmp_path)}):
            resp = _cloturer(client, auth_headers)
            assert resp.status_code == 200, resp.text

        assert list(tmp_path.glob("collegeaureole_sauvegarde_*.zip")) == []

    def test_echec_archive_annule_la_cloture(self, client, auth_headers, db_session, tmp_path, monkeypatch):
        """Si l'archive ne peut pas être écrite, la clôture est refusée et
        l'année reste active (aucun changement d'année)."""
        from services import sauvegardes

        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section").json()
        ms = _creer_classe(client, auth_headers, niveau="Moyenne Section").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"])

        def _en_echec(db, dossier=None):
            raise OSError("disque plein")

        monkeypatch.setattr(sauvegardes, "ecrire_sauvegarde", _en_echec)

        with mock.patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            resp = _cloturer(client, auth_headers)
            assert resp.status_code == 500

        db_session.expire_all()
        ancienne = db_session.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee["id"]).first()
        assert ancienne.active is True
        assert ancienne.cloturee is False
        inexistant = db_session.query(models.AnneesScolaires).filter(
            models.AnneesScolaires.libelle == "2026-2027"
        ).first()
        assert inexistant is None


class TestSauvegardeClotureHelper:
    def test_ignoree_en_environnement_test(self, db_session, tmp_path):
        from services import sauvegardes

        with mock.patch.dict(os.environ, {"ENVIRONMENT": "test", "AUREOLE_SAUVEGARDES_DIR": str(tmp_path)}):
            resultat = sauvegardes.sauvegarde_cloture(db_session)

        assert resultat is None
        assert list(tmp_path.glob("collegeaureole_sauvegarde_*.zip")) == []

    def test_ecriture_hors_test(self, db_session, tmp_path):
        from services import sauvegardes

        with mock.patch.dict(os.environ, {"ENVIRONMENT": "production", "AUREOLE_SAUVEGARDES_DIR": str(tmp_path)}):
            resultat = sauvegardes.sauvegarde_cloture(db_session)

        assert resultat is not None
        assert resultat.name.endswith(".zip")
        assert list(tmp_path.glob("collegeaureole_sauvegarde_*.zip")) == [resultat]