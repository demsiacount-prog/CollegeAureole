"""Tests d'intégration du router Salles via TestClient.

Couverture : CRUD complet, génération automatique du code_salle, validation
des doublons, et contrôle des permissions par rôle.
"""
import pytest


def _creer_salle(client, auth_headers, nom="A101", capacite=30):
    resp = client.post("/api/salles/", json={"nom": nom, "capacite": capacite}, headers=auth_headers)
    return resp


class TestCreation:
    def test_creer_une_salle(self, client, auth_headers):
        resp = _creer_salle(client, auth_headers, nom="A101", capacite=30)
        assert resp.status_code == 201
        body = resp.json()
        assert body["nom"] == "A101"
        assert body["capacite"] == 30
        # Le code est généré automatiquement par l'événement before_insert.
        assert body["code_salle"].startswith("SAL")

    def test_creer_salle_sans_capacite(self, client, auth_headers):
        resp = client.post("/api/salles/", json={"nom": "B201"}, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["capacite"] is None

    def test_doublon_de_nom_refuse(self, client, auth_headers):
        _creer_salle(client, auth_headers, nom="A101")
        resp = _creer_salle(client, auth_headers, nom="A101")
        assert resp.status_code == 400

    def test_nom_vide_refuse(self, client, auth_headers):
        resp = _creer_salle(client, auth_headers, nom="")
        assert resp.status_code >= 400


class TestLecture:
    def test_liste_vide_au_depart(self, client, auth_headers):
        resp = client.get("/api/salles/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_liste_apres_creation(self, client, auth_headers):
        _creer_salle(client, auth_headers, nom="A101")
        _creer_salle(client, auth_headers, nom="A102")
        resp = client.get("/api/salles/", headers=auth_headers)
        assert resp.status_code == 200
        noms = {s["nom"] for s in resp.json()}
        assert noms == {"A101", "A102"}

    def test_salle_introuvable_404(self, client, auth_headers, db_session):
        resp = client.put("/api/salles/99999", json={"nom": "X"}, headers=auth_headers)
        assert resp.status_code == 404


class TestModification:
    def test_modifier_une_salle(self, client, auth_headers):
        created = _creer_salle(client, auth_headers, nom="A101", capacite=20).json()
        resp = client.put(
            f"/api/salles/{created['id']}",
            json={"nom": "A101bis", "capacite": 45},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nom"] == "A101bis"
        assert resp.json()["capacite"] == 45


class TestSuppression:
    def test_supprimer_une_salle(self, client, auth_headers):
        created = _creer_salle(client, auth_headers, nom="A101").json()
        resp = client.delete(f"/api/salles/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204
        liste = client.get("/api/salles/", headers=auth_headers).json()
        assert liste == []

    def test_suppression_sans_token_refusee(self, client):
        resp = client.delete("/api/salles/1")
        assert resp.status_code == 401


class TestAuthRequis:
    def test_creer_sans_token_401(self, client):
        resp = client.post("/api/salles/", json={"nom": "A101"})
        assert resp.status_code == 401
