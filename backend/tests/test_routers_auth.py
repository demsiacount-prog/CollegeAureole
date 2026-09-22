"""Tests d'intégration de l'authentification (routers/auth.py).

Couvre la connexion (succès/échec), le verrouillage après trop d'échecs,
les comptes désactivés, la récupération du profil courant et le flux « mot de
passe oublié » (jetons de réinitialisation, anti-énumération, déverrouillage).
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import pytest

from hashing import hash_password, verify_password
from credentials import ADMIN_EMAIL, ADMIN_PASSWORD
import models


def _connecter(client, email, mot_de_passe):
    return client.post("/api/auth/connexion", json={"email": email, "mot_de_passe": mot_de_passe})


class TestConnexion:
    def test_connexion_reussie(self, client, admin_user):
        resp = _connecter(client, admin_user.email, ADMIN_PASSWORD)
        assert resp.status_code == 200
        body = resp.json()
        assert body["access_token"]
        assert body["utilisateur"]["email"] == admin_user.email

    def test_mauvais_mot_de_passe(self, client, admin_user):
        resp = _connecter(client, admin_user.email, "MauvaisMotDePasse!")
        assert resp.status_code == 401

    def test_email_inconnu(self, client):
        resp = _connecter(client, "inconnu@etablissement.com", ADMIN_PASSWORD)
        assert resp.status_code == 401


class TestCompteDesactive:
    def test_connexion_dun_compte_desactive_refusee(self, client, db_session):
        from models.utilisateurs import Utilisateurs

        user = Utilisateurs(
            nom="Desactive", prenom="Test",
            email="desactive@etablissement.com",
            mot_de_passe=hash_password(ADMIN_PASSWORD),
            actif=False,
        )
        db_session.add(user)
        db_session.commit()
        resp = _connecter(client, "desactive@etablissement.com", ADMIN_PASSWORD)
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


class TestChangerMotDePasse:
    URL = "/api/auth/utilisateurs/{id}/mot-de-passe"

    def _changer(self, client, utilisateur_id, ancien, nouveau):
        return client.put(
            self.URL.format(id=utilisateur_id),
            json={"ancien_mot_de_passe": ancien, "nouveau_mot_de_passe": nouveau},
            headers={"Authorization": f"Bearer {self.token}"},
        )

    @pytest.fixture(autouse=True)
    def _token(self, auth_headers, admin_user):
        self.token = auth_headers["Authorization"].split()[1]

    def test_changer_son_mot_de_passe(self, client, admin_user):
        nouveau = "NouveauMotDePasse123!"
        resp = self._changer(client, admin_user.id, ADMIN_PASSWORD, nouveau)
        assert resp.status_code == 204
        resp = _connecter(client, admin_user.email, nouveau)
        assert resp.status_code == 200

    def test_ancien_mot_de_passe_incorrect_401(self, client, admin_user):
        resp = self._changer(client, admin_user.id, "MauvaisMotDePasse!", "NouveauMotDePasse123!")
        assert resp.status_code == 401

    def test_mot_de_passe_identique_refuse(self, client, admin_user):
        resp = self._changer(client, admin_user.id, ADMIN_PASSWORD, ADMIN_PASSWORD)
        assert resp.status_code == 422
        detail = resp.json()
        assert detail["error_code"] == "VALIDATION_ERROR"
        assert "différent" in detail["details"]["reason"]

    def test_mot_de_passe_faible_refuse(self, client, admin_user):
        resp = self._changer(client, admin_user.id, ADMIN_PASSWORD, "court")
        assert resp.status_code == 422

    def test_impossible_changer_le_mot_de_passe_dun_autre(self, client, auth_headers):
        resp = client.put(
            "/api/auth/utilisateurs/999999/mot-de-passe",
            json={"ancien_mot_de_passe": ADMIN_PASSWORD, "nouveau_mot_de_passe": "NouveauMotDePasse123!"},
            headers=auth_headers,
        )
        # 999999 ≠ id de l'admin authentifié : refus avant même la recherche en base.
        assert resp.status_code == 403


_SMTP_KEYS = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM", "SMTP_TLS"]


@pytest.fixture()
def _sans_smtp(monkeypatch):
    """Garantit l'absence de configuration SMTP pour ces tests (repli admin)."""
    for cle in _SMTP_KEYS:
        monkeypatch.delenv(cle, raising=False)


def _creer_jeton(db_session, utilisateur_id, *, expire_apres_min=30):
    """Crée un enregistrement de jeton valide et renvoie le jeton brut."""
    from models.mot_de_passe_reinitialisation import MotDePasseReinitialisation

    jeton = secrets.token_hex(32)
    maintenant = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.add(MotDePasseReinitialisation(
        id_utilisateur=utilisateur_id,
        jeton_hash=hashlib.sha256(jeton.encode("utf-8")).hexdigest(),
        expire_le=maintenant + timedelta(minutes=expire_apres_min),
    ))
    db_session.commit()
    return jeton


class TestMotDePasseOublie:
    URL = "/api/auth/mot-de-passe-oublie"

    def test_sans_smtp_200_email_non_envoye(self, client, admin_user, _sans_smtp):
        resp = client.post(self.URL, json={"email": admin_user.email})
        assert resp.status_code == 200
        body = resp.json()
        assert body["email_envoye"] is False
        assert "admin" in body["message"]

    def test_email_inconnu_reponse_identique(self, client, _sans_smtp):
        """Anti-énumération : pas d'écart de statut ni de forme si le compte
        n'existe pas (réponse muette identique au compte existant)."""
        resp = client.post(self.URL, json={"email": "introuvable@etablissement.com"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["email_envoye"] is False
        assert set(body.keys()) == {"email_envoye", "message"}


class TestReinitialiserMotDePasse:
    URL = "/api/auth/reinitialiser-mot-de-passe"

    def test_jeton_invalide_400(self, client, auth_headers):
        resp = client.post(self.URL, json={
            "jeton": secrets.token_hex(32),
            "nouveau_mot_de_passe": "NouveauMotDePasse123!",
        })
        assert resp.status_code == 400

    def test_jeton_expire_400(self, client, admin_user, db_session):
        jeton = _creer_jeton(db_session, admin_user.id, expire_apres_min=-1)
        resp = client.post(self.URL, json={
            "jeton": jeton,
            "nouveau_mot_de_passe": "NouveauMotDePasse123!",
        })
        assert resp.status_code == 400

    def test_jeton_deja_utilise_400(self, client, admin_user, db_session):
        jeton = secrets.token_hex(32)
        db_session.add(models.MotDePasseReinitialisation(
            id_utilisateur=admin_user.id,
            jeton_hash=hashlib.sha256(jeton.encode("utf-8")).hexdigest(),
            expire_le=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30),
            utilise_le=datetime.now(timezone.utc).replace(tzinfo=None),
        ))
        db_session.commit()
        resp = client.post(self.URL, json={
            "jeton": jeton,
            "nouveau_mot_de_passe": "NouveauMotDePasse123!",
        })
        assert resp.status_code == 400

    def test_mot_de_passe_trop_court_422(self, client, admin_user, db_session):
        jeton = _creer_jeton(db_session, admin_user.id)
        resp = client.post(self.URL, json={"jeton": jeton, "nouveau_mot_de_passe": "court"})
        assert resp.status_code == 422

    def test_jeton_valide_change_mdp_et_deverrouille(self, client, admin_user, db_session):
        # Verrouillage simulé : trop d'échecs, compte bloqué jusqu'à +15 min.
        admin_user.tentatives_echouees = 5
        admin_user.verrouille_jusqua = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
        db_session.commit()

        jeton = _creer_jeton(db_session, admin_user.id)
        nouveau = "MotDePasseReinitialise42!"
        resp = client.post(self.URL, json={"jeton": jeton, "nouveau_mot_de_passe": nouveau})
        assert resp.status_code == 200
        assert resp.json()["message"]

        db_session.expire_all()
        admin_user = db_session.get(models.Utilisateurs, admin_user.id)
        # Mot de passe réellement remplacé + compte déverrouillé.
        assert verify_password(nouveau, admin_user.mot_de_passe)
        assert not verify_password(ADMIN_PASSWORD, admin_user.mot_de_passe)
        assert admin_user.tentatives_echouees == 0
        assert admin_user.verrouille_jusqua is None

        jeton_enreg = db_session.query(models.MotDePasseReinitialisation).first()
        assert jeton_enreg.utilise_le is not None

        # Le nouveau mot de passe reconnecte (l'ancien est invalide).
        resp = _connecter(client, admin_user.email, nouveau)
        assert resp.status_code == 200
        resp = _connecter(client, admin_user.email, ADMIN_PASSWORD)
        assert resp.status_code == 401
