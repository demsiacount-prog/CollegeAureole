"""Tests d'intégration du router Dépenses via TestClient.

Couverture : CRUD complet, comptage avec total_montant, filtrage par
catégorie et dates, code auto-généré.
"""
import pytest
from datetime import date


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
