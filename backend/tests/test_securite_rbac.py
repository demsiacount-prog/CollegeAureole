"""Tests de sécurité : autorisation par rôle (RBAC).

Le backend distingue désormais « authentifié » (get_current_user) de
« administrateur » (require_admin). Toute opération de gestion sensible doit
renvoyer 403 pour un compte non-admin (ici SECRETAIRE), tandis que les
lectures de données restent ouvertes à tout utilisateur authentifié.
"""
import pytest

import models
from hashing import hash_password
from security import create_access_token

from datetime import date


@pytest.fixture()
def secretaire_user(db_session):
    user = models.Utilisateurs(
        nom="Secretaire",
        prenom="Test",
        email="secretaire@test.com",
        mot_de_passe=hash_password("secret123"),
        role="SECRETAIRE",
        actif=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def secretaire_headers(secretaire_user):
    return {"Authorization": f"Bearer {create_access_token(utilisateur_id=secretaire_user.id)}"}


_CLOTURE_PAYLOAD = {
    "nouvelle_annee": {
        "libelle": "2030-2031",
        "date_debut": "2030-09-01",
        "date_fin": "2031-06-30",
    }
}

_ANNEE_PAYLOAD = {
    "libelle": "2030-2031",
    "date_debut": "2030-09-01",
    "date_fin": "2031-06-30",
    "active": False,
}

_ETAB_PAYLOAD = {"nom": "Collège Auréole"}


class TestGestionComptesReserveeAdmin:
    @pytest.mark.parametrize("methode,url", [
        ("GET", "/api/utilisateurs/"),
        ("POST", "/api/utilisateurs/"),
        ("DELETE", "/api/utilisateurs/1"),
    ])
    def test_secretaire_403(self, client, secretaire_headers, methode, url):
        resp = client.request(methode, url, headers=secretaire_headers)
        assert resp.status_code == 403

    def test_reinitialiser_mot_de_passe_autre_compte_403(self, client, secretaire_headers, admin_user):
        resp = client.put(
            f"/api/utilisateurs/{admin_user.id}/mot-de-passe",
            json={"nouveau_mot_de_passe": "nouveau123"},
            headers=secretaire_headers,
        )
        assert resp.status_code == 403

    def test_secretaire_impossible_creer_admin(self, client, secretaire_headers):
        resp = client.post(
            "/api/utilisateurs/",
            json={
                "nom": "X", "prenom": "Y", "email": "x@test.com",
                "mot_de_passe": "motdepasse123", "role": "ADMIN",
            },
            headers=secretaire_headers,
        )
        assert resp.status_code == 403

    def test_admin_ok(self, client, auth_headers, admin_user):
        resp = client.get("/api/utilisateurs/", headers=auth_headers)
        assert resp.status_code == 200
        assert any(u["email"] == admin_user.email for u in resp.json())


class TestExportEtPurgeReservesAdmin:
    def test_export_403(self, client, secretaire_headers):
        resp = client.get("/api/import-export/export", headers=secretaire_headers)
        assert resp.status_code == 403

    def test_export_admin_ok(self, client, auth_headers):
        resp = client.get("/api/import-export/export", headers=auth_headers)
        assert resp.status_code == 200

    @pytest.mark.parametrize("url", [
        "/api/setup/purge-donnees",
        "/api/setup/reset",
    ])
    def test_purge_reset_403(self, client, secretaire_headers, url):
        resp = client.post(
            url,
            json={"confirm": True},
            headers={**secretaire_headers, "X-Confirm": "PURGE-DONNEES"},
        )
        assert resp.status_code == 403


class TestParametresEtAnneeReservesAdmin:
    def test_creer_annee_403(self, client, secretaire_headers):
        resp = client.post("/api/anneesScolaires/", json=_ANNEE_PAYLOAD, headers=secretaire_headers)
        assert resp.status_code == 403

    def test_activer_annee_403(self, client, secretaire_headers, db_session):
        annee = _creer_annee(db_session)
        resp = client.put(f"/api/anneesScolaires/{annee.id}/activer", headers=secretaire_headers)
        assert resp.status_code == 403

    def test_etablissement_403(self, client, secretaire_headers):
        resp = client.put("/api/etablissement", json=_ETAB_PAYLOAD, headers=secretaire_headers)
        assert resp.status_code == 403

    def test_logo_403(self, client, secretaire_headers):
        resp = client.post(
            "/api/etablissement/logo",
            files={"file": ("logo.png", b"\x89PNG\r\n\x1a\n" + b"x" * 16, "image/png")},
            headers=secretaire_headers,
        )
        assert resp.status_code == 403

    def test_cloture_executer_403(self, client, secretaire_headers):
        resp = client.post("/api/cloture/executer", json=_CLOTURE_PAYLOAD, headers=secretaire_headers)
        assert resp.status_code == 403

    def test_creer_annee_admin_ok(self, client, auth_headers):
        resp = client.post("/api/anneesScolaires/", json=_ANNEE_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 201

    def test_lire_annees_secretaire_ok(self, client, secretaire_headers, db_session):
        _creer_annee(db_session)
        resp = client.get("/api/anneesScolaires/", headers=secretaire_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_preview_cloture_accessible_en_lecture(self, client, secretaire_headers):
        # Pas d'année active : 404 (données), jamais 403 (autorisation).
        resp = client.get("/api/cloture/preview", headers=secretaire_headers)
        assert resp.status_code == 404


def _creer_annee(db_session) -> models.AnneesScolaires:
    annee = models.AnneesScolaires(
        libelle="2029-2030",
        date_debut=date(2029, 9, 1),
        date_fin=date(2030, 6, 30),
        active=False,
    )
    db_session.add(annee)
    db_session.commit()
    db_session.refresh(annee)
    return annee