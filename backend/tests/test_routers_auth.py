"""Tests d'intégration de l'authentification (routers/auth.py).

Couvre la connexion (succès/échec), le verrouillage après trop d'échecs,
les comptes désactivés et la récupération du profil courant.
"""
import pytest

from hashing import hash_password


def _connecter(client, email, mot_de_passe):
    return client.post("/api/auth/connexion", json={"email": email, "mot_de_passe": mot_de_passe})


class TestConnexion:
    def test_connexion_reussie(self, client, admin_user):
        resp = _connecter(client, admin_user.email, "Password123!")
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["utilisateur"]["email"] == admin_user.email
        assert body["utilisateur"]["role"] == "admin"

    def test_mauvais_mot_de_passe(self, client, admin_user):
        resp = _connecter(client, admin_user.email, "MauvaisMotDePasse!")
        assert resp.status_code == 401

    def test_email_inconnu(self, client):
        resp = _connecter(client, "inconnu@etablissement.com", "Password123!")
        assert resp.status_code == 401


class TestCompteDesactive:
    def test_connexion_dun_compte_desactive_refusee(self, client, db_session):
        from models.utilisateurs import Utilisateurs
        from enums import RoleUtilisateur

        user = Utilisateurs(
            nom="Desactive", prenom="Test",
            email="desactive@etablissement.com",
            mot_de_passe=hash_password("Password123!"),
            role=RoleUtilisateur.ADMIN, actif=False,
        )
        db_session.add(user)
        db_session.commit()
        resp = _connecter(client, "desactive@etablissement.com", "Password123!")
        assert resp.status_code in (401, 403)


class TestVerrouillage:
    def test_verrouille_apres_5_echecs(self, client, admin_user, db_session):
        for _ in range(5):
            _connecter(client, admin_user.email, "MauvaisMotDePasse!")
        resp = _connecter(client, admin_user.email, "MauvaisMotDePasse!")
        # Compte verrouillé (Forbidden 403).
        assert resp.status_code == 403


class TestProfil:
    def test_moi_avec_token(self, client, auth_headers, admin_user):
        resp = client.get("/api/auth/moi", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == admin_user.id

    def test_moi_sans_token_401(self, client):
        resp = client.get("/api/auth/moi")
        assert resp.status_code == 401
