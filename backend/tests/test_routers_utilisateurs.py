"""Tests d'intégration de la gestion des utilisateurs (routers/utilisateurs.py).

Couvre la liste, la création, l'activation/désactivation, la réinitialisation
du mot de passe et la suppression.
"""
import pytest


def _creer(client, auth_headers, **overrides):
    payload = {
        "nom": "Traoré",
        "prenom": "Aminata",
        "email": "aminata@ecole.ml",
        "mot_de_passe": "Password123!",
        **overrides,
    }
    return client.post("/api/utilisateurs/", json=payload, headers=auth_headers)


class TestListe:
    def test_liste_sans_auth_401(self, client):
        assert client.get("/api/utilisateurs/").status_code == 401

    def test_liste_contient_les_utilisateurs(self, client, auth_headers, admin_user):
        resp = client.get("/api/utilisateurs/", headers=auth_headers)
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert admin_user.email in emails


class TestCreation:
    def test_creer_utilisateur(self, client, auth_headers):
        resp = _creer(client, auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "aminata@ecole.ml"
        assert body["actif"] is True
        assert body["role"] == "ADMIN"
        assert "id" in body

    def test_creer_avec_role(self, client, auth_headers):
        resp = _creer(client, auth_headers, role="SECRETAIRE")
        assert resp.status_code == 201
        assert resp.json()["role"] == "SECRETAIRE"

    def test_role_insensible_a_la_casse(self, client, auth_headers):
        resp = _creer(client, auth_headers, role="comptable")
        assert resp.status_code == 201
        assert resp.json()["role"] == "COMPTABLE"

    def test_role_invalide(self, client, auth_headers):
        resp = _creer(client, auth_headers, role="MAGICIEN")
        assert resp.status_code == 422

    def test_email_deja_utilise(self, client, auth_headers, admin_user):
        resp = _creer(client, auth_headers, email=admin_user.email)
        assert resp.status_code == 409

    def test_mot_de_passe_trop_court(self, client, auth_headers):
        resp = _creer(client, auth_headers, mot_de_passe="court")
        assert resp.status_code == 422


class TestStatut:
    def test_desactiver_puis_activer(self, client, auth_headers):
        created = _creer(client, auth_headers).json()
        resp = client.patch(
            f"/api/utilisateurs/{created['id']}/statut",
            json={"actif": False},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["actif"] is False
        resp = client.patch(
            f"/api/utilisateurs/{created['id']}/statut",
            json={"actif": True},
            headers=auth_headers,
        )
        assert resp.json()["actif"] is True

    def test_impossible_desactiver_son_propre_compte(self, client, auth_headers, admin_user):
        resp = client.patch(
            f"/api/utilisateurs/{admin_user.id}/statut",
            json={"actif": False},
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestMotDePasse:
    def test_reinitialiser_et_se_connecter(self, client, auth_headers):
        created = _creer(client, auth_headers).json()
        resp = client.put(
            f"/api/utilisateurs/{created['id']}/mot-de-passe",
            json={"nouveau_mot_de_passe": "NouveauMotDePasse123!"},
            headers=auth_headers,
        )
        assert resp.status_code == 204
        connexion = client.post(
            "/api/auth/connexion",
            json={"email": "aminata@ecole.ml", "mot_de_passe": "NouveauMotDePasse123!"},
        )
        assert connexion.status_code == 200


class TestSuppression:
    def test_supprimer_utilisateur(self, client, auth_headers):
        created = _creer(client, auth_headers).json()
        resp = client.delete(f"/api/utilisateurs/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204
        liste = client.get("/api/utilisateurs/", headers=auth_headers).json()
        assert all(u["id"] != created["id"] for u in liste)

    def test_impossible_supprimer_son_propre_compte(self, client, auth_headers, admin_user):
        resp = client.delete(f"/api/utilisateurs/{admin_user.id}", headers=auth_headers)
        assert resp.status_code == 403