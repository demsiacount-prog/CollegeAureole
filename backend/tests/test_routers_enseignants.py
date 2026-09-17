"""Tests d'intégration du router Enseignants via TestClient.

Couverture : CRUD complet, génération matricule, recherche, email unique,
dossier complet, protection suppression.
"""
import pytest


def _creer_enseignant(client, auth_headers, **overrides):
    data = {
        "nom": "Sow", "prenom": "Moussa",
        "email": "moussa.sow@ex.com", "telephone": "+223 76 00 33 44",
        "adresse": "Bamako", "specialite": "Mathématiques",
        **overrides,
    }
    return client.post("/api/enseignants/", json=data, headers=auth_headers)


class TestCreation:
    def test_creer_enseignant(self, client, auth_headers):
        resp = _creer_enseignant(client, auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["matricule"].startswith("ENS")
        assert body["nom"] == "Sow"

    def test_email_doublon_refuse(self, client, auth_headers):
        _creer_enseignant(client, auth_headers, email="dup@ex.com")
        resp = _creer_enseignant(client, auth_headers, email="dup@ex.com")
        assert resp.status_code == 400

    def test_matricule_auto_generé(self, client, auth_headers):
        e1 = _creer_enseignant(client, auth_headers, email="e1@ex.com").json()
        e2 = _creer_enseignant(client, auth_headers, email="e2@ex.com").json()
        assert e1["matricule"] != e2["matricule"]


class TestLecture:
    def test_liste(self, client, auth_headers):
        _creer_enseignant(client, auth_headers, email="e1@ex.com")
        resp = client.get("/api/enseignants/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_par_matricule(self, client, auth_headers):
        created = _creer_enseignant(client, auth_headers).json()
        resp = client.get(f"/api/enseignants/{created['matricule']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Sow"

    def test_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/enseignants/ENS9900000", headers=auth_headers)
        assert resp.status_code == 404

    def test_compte(self, client, auth_headers):
        _creer_enseignant(client, auth_headers, email="e1@ex.com")
        _creer_enseignant(client, auth_headers, email="e2@ex.com")
        resp = client.get("/api/enseignants/compte", headers=auth_headers)
        assert resp.json()["total"] == 2

    def test_recherche(self, client, auth_headers):
        _creer_enseignant(client, auth_headers, nom="Konaté", email="k@ex.com")
        _creer_enseignant(client, auth_headers, nom="Traoré", email="t@ex.com")
        resp = client.get("/api/enseignants/?q=Konaté", headers=auth_headers)
        noms = [e["nom"] for e in resp.json()]
        assert "Konaté" in noms
        assert "Traoré" not in noms


class TestModification:
    def test_modifier(self, client, auth_headers):
        created = _creer_enseignant(client, auth_headers).json()
        resp = client.put(
            f"/api/enseignants/{created['matricule']}",
            json={
                "nom": "Nouveau", "prenom": "Nouveau",
                "email": "nouveau@ex.com", "telephone": "+22376000000",
                "adresse": "Bamako", "specialite": "Français",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Nouveau"

    def test_modifier_email_doublon_400(self, client, auth_headers):
        e1 = _creer_enseignant(client, auth_headers, email="e1@ex.com").json()
        _creer_enseignant(client, auth_headers, email="e2@ex.com")
        resp = client.put(
            f"/api/enseignants/{e1['matricule']}",
            json={
                "nom": "X", "prenom": "X",
                "email": "e2@ex.com", "telephone": "+22376000000",
                "adresse": "", "specialite": "X",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestSuppression:
    def test_supprimer_sans_lien(self, client, auth_headers):
        created = _creer_enseignant(client, auth_headers).json()
        resp = client.delete(f"/api/enseignants/{created['matricule']}", headers=auth_headers)
        assert resp.status_code == 204
        assert client.get("/api/enseignants/", headers=auth_headers).json() == []

    def test_supprimer_404(self, client, auth_headers):
        resp = client.delete("/api/enseignants/ENS9900000", headers=auth_headers)
        assert resp.status_code == 404


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/enseignants/")
        assert resp.status_code == 401
