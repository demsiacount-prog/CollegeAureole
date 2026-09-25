"""Tests d'intégration du router Dépenses via TestClient.

Couverture : CRUD complet, comptage avec total_montant, filtrage par
catégorie et dates, code auto-généré.
"""
import pytest
from datetime import date

import models


class TestCreation:
    def test_creer_depense(self, client, auth_headers):
        resp = client.post("/api/depenses/", json={
            "libelle": "Fournitures", "montant": 50000,
            "categorie": "FOURNITURES", "date": "2025-10-15",
        }, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["libelle"] == "Fournitures"
        assert body["montant"] == 50000.0
        assert body["code_depense"].startswith("DEP")

    def test_code_auto_genere(self, client, auth_headers):
        d1 = client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 1000, "date": "2025-10-01",
        }, headers=auth_headers).json()
        d2 = client.post("/api/depenses/", json={
            "libelle": "D2", "montant": 2000, "date": "2025-10-01",
        }, headers=auth_headers).json()
        assert d1["code_depense"] != d2["code_depense"]

    def test_montant_zero_refuse(self, client, auth_headers):
        resp = client.post("/api/depenses/", json={
            "libelle": "X", "montant": 0, "date": "2025-10-01",
        }, headers=auth_headers)
        assert resp.status_code >= 400


class TestLecture:
    def test_liste(self, client, auth_headers):
        client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 1000, "date": "2025-10-01",
        }, headers=auth_headers)
        resp = client.get("/api/depenses/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_par_id(self, client, auth_headers):
        created = client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 1000, "date": "2025-10-01",
        }, headers=auth_headers).json()
        resp = client.get(f"/api/depenses/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200

    def test_depense_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/depenses/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_compte_avec_montant_total(self, client, auth_headers):
        client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 5000, "date": "2025-10-01",
        }, headers=auth_headers)
        client.post("/api/depenses/", json={
            "libelle": "D2", "montant": 3000, "date": "2025-10-15",
        }, headers=auth_headers)
        resp = client.get("/api/depenses/compte", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2
        assert resp.json()["total_montant"] == 8000.0

    def test_filtre_par_categorie(self, client, auth_headers):
        client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 1000, "date": "2025-10-01", "categorie": "SALAIRES",
        }, headers=auth_headers)
        client.post("/api/depenses/", json={
            "libelle": "D2", "montant": 2000, "date": "2025-10-01", "categorie": "EAU",
        }, headers=auth_headers)
        resp = client.get("/api/depenses/?categorie=SALAIRES", headers=auth_headers)
        assert len(resp.json()) == 1

    def test_filtre_par_dates(self, client, auth_headers):
        client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 1000, "date": "2025-10-01",
        }, headers=auth_headers)
        client.post("/api/depenses/", json={
            "libelle": "D2", "montant": 2000, "date": "2025-12-01",
        }, headers=auth_headers)
        resp = client.get("/api/depenses/?date_debut=2025-11-01", headers=auth_headers)
        assert len(resp.json()) == 1


class TestModification:
    def test_modifier_depense(self, client, auth_headers):
        created = client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 1000, "date": "2025-10-01",
        }, headers=auth_headers).json()
        resp = client.put(f"/api/depenses/{created['id']}", json={
            "libelle": "D2", "montant": 9999,
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["libelle"] == "D2"
        assert resp.json()["montant"] == 9999


class TestSuppression:
    def test_supprimer_depense(self, client, auth_headers):
        created = client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 1000, "date": "2025-10-01",
        }, headers=auth_headers).json()
        resp = client.delete(f"/api/depenses/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204
        assert client.get("/api/depenses/", headers=auth_headers).json() == []


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/depenses/")
        assert resp.status_code == 401


class TestAnneeCloturee:
    def _creer_annee_cloturee(self, db_session):
        db_session.add(models.AnneesScolaires(
            libelle="2024-2025", date_debut=date(2024, 9, 1), date_fin=date(2025, 6, 30),
            active=False, cloturee=True,
        ))
        db_session.commit()

    def test_creation_historique_permise(self, client, auth_headers, db_session):
        """On peut saisir une dépense historique même si l'année est clôturée."""
        self._creer_annee_cloturee(db_session)
        resp = client.post("/api/depenses/", json={
            "libelle": "Historique", "montant": 10000, "date": "2025-01-15",
        }, headers=auth_headers)
        assert resp.status_code == 201

    def test_modification_permise_sur_annee_cloturee(self, client, auth_headers, db_session):
        """Les dépenses restent corrigibles même sur une année clôturée
        (elles ne sont pas liées à une inscription : pas de gel comptable)."""
        self._creer_annee_cloturee(db_session)
        created = client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 10000, "date": "2025-01-15",
        }, headers=auth_headers).json()
        resp = client.put(f"/api/depenses/{created['id']}", json={"montant": 5000}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["montant"] == 5000

    def test_suppression_permise_sur_annee_cloturee(self, client, auth_headers, db_session):
        self._creer_annee_cloturee(db_session)
        created = client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 10000, "date": "2025-01-15",
        }, headers=auth_headers).json()
        resp = client.delete(f"/api/depenses/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_montant_zero_ou_negatif_refuse_en_update(self, client, auth_headers):
        created = client.post("/api/depenses/", json={
            "libelle": "D1", "montant": 1000, "date": "2025-10-01",
        }, headers=auth_headers).json()
        resp = client.put(f"/api/depenses/{created['id']}", json={"montant": 0}, headers=auth_headers)
        assert resp.status_code == 422
