"""Tests d'intégration du router Trimestres via TestClient.

Couverture : CRUD, génération périodes, verrouillage/déverrouillage, filtrage
par année, protection suppression.
"""
import pytest


def _creer_annee(client, auth_headers, **overrides):
    data = {
        "libelle": "2025-2026", "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
        **overrides,
    }
    return client.post("/api/anneesScolaires/", json=data, headers=auth_headers)


def _creer_trimestre(client, auth_headers, annee_id, **overrides):
    data = {
        "nom": "1er Trimestre", "type": "TRIMESTRE",
        "annee_scolaire_id": annee_id,
        "date_debut": "2025-09-01", "date_fin": "2025-11-30",
        **overrides,
    }
    return client.post("/api/trimestres/", json=data, headers=auth_headers)


class TestCreation:
    def test_creer_trimestre(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers).json()
        resp = _creer_trimestre(client, auth_headers, annee["id"])
        assert resp.status_code == 201
        body = resp.json()
        assert body["nom"] == "1er Trimestre"
        assert body["verrouille"] is False

    def test_annee_introuvable_404(self, client, auth_headers):
        resp = _creer_trimestre(client, auth_headers, 99999)
        assert resp.status_code == 404

    def test_dates_invalidees(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers).json()
        resp = client.post("/api/trimestres/", json={
            "nom": "X", "annee_scolaire_id": annee["id"],
            "date_debut": "2025-12-01", "date_fin": "2025-09-01",
        }, headers=auth_headers)
        assert resp.status_code >= 400


class TestGenerationPeriodes:
    def test_generer_periodes(self, client, auth_headers, db_session):
        """La création d'une année génère automatiquement les périodes.
        On vérifie qu'elles existent bien après la création."""
        from models.trimestres import Trimestres

        annee = _creer_annee(client, auth_headers).json()
        # Les périodes sont auto-générées à la création de l'année
        resp = client.get(f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers)
        assert resp.status_code == 200
        periodes = resp.json()
        assert len(periodes) > 0

    def test_generer_est_idempotent(self, client, auth_headers):
        """Appeler generer une 2e fois ne crée rien (déjà auto-généré)."""
        annee = _creer_annee(client, auth_headers).json()
        r1 = client.post("/api/trimestres/generer", json={"annee_scolaire_id": annee["id"]}, headers=auth_headers)
        assert r1.status_code == 200
        r2 = client.post("/api/trimestres/generer", json={"annee_scolaire_id": annee["id"]}, headers=auth_headers)
        assert r2.json()["cree"] == 0

    def test_generer_annee_introuvable_404(self, client, auth_headers):
        resp = client.post("/api/trimestres/generer", json={"annee_scolaire_id": 99999}, headers=auth_headers)
        assert resp.status_code == 404


class TestVerrouillage:
    def test_verrouiller(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers).json()
        # Récupérer un trimestre auto-généré
        trimestres = client.get(f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers).json()
        trimestre = trimestres[0]
        resp = client.put(f"/api/trimestres/{trimestre['id']}/verrouiller", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["verrouille"] is True

    def test_deverrouiller(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers).json()
        trimestres = client.get(f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers).json()
        trimestre = trimestres[0]
        client.put(f"/api/trimestres/{trimestre['id']}/verrouiller", headers=auth_headers)
        resp = client.put(f"/api/trimestres/{trimestre['id']}/deverrouiller", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["verrouille"] is False


class TestLecture:
    def test_liste_filtrée(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers).json()
        resp = client.get(f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_trimestre_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/trimestres/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestSuppression:
    def test_supprimer_trimestre_vide(self, client, auth_headers):
        """Supprimer un trimestre auto-généré qui n'a pas de notes/bulletins."""
        annee = _creer_annee(client, auth_headers).json()
        trimestres = client.get(f"/api/trimestres/?annee_scolaire_id={annee['id']}", headers=auth_headers).json()
        trimestre = trimestres[0]
        resp = client.delete(f"/api/trimestres/{trimestre['id']}", headers=auth_headers)
        assert resp.status_code == 204


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/trimestres/")
        assert resp.status_code == 401
