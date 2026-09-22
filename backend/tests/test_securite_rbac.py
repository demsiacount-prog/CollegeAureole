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


class TestTrimestresReservesAdmin:
    """Génération/verrouillage/suppression de trimestres = rôle admin."""

    @pytest.mark.parametrize("methode,url", [
        ("GET", "/api/trimestres/"),
        ("GET", "/api/trimestres/1"),
    ])
    def test_lecture_secretaire_ok(self, client, secretaire_headers, methode, url):
        # La lecture reste ouverte aux authentifiés (données absentes : 404/200).
        resp = client.request(methode, url, headers=secretaire_headers)
        if url.endswith("/1"):
            assert resp.status_code == 404
        else:
            assert resp.status_code == 200

    @pytest.mark.parametrize("methode,url", [
        ("POST", "/api/trimestres/generer"),
        ("POST", "/api/trimestres/"),
        ("PUT", "/api/trimestres/1/verrouiller"),
        ("PUT", "/api/trimestres/1/deverrouiller"),
        ("DELETE", "/api/trimestres/1"),
    ])
    def test_ecriture_secretaire_403(self, client, secretaire_headers, methode, url):
        resp = client.request(methode, url, headers=secretaire_headers, json={})
        assert resp.status_code == 403

    def test_admin_generer_ok(self, client, auth_headers, db_session):
        annee = _creer_annee(db_session)
        resp = client.post(
            "/api/trimestres/generer",
            json={"annee_scolaire_id": annee.id},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["cree"] >= 1

    def test_admin_creer_ok(self, client, auth_headers, db_session):
        annee = _creer_annee(db_session)
        resp = client.post("/api/trimestres/", json={
            "nom": "1er Trimestre", "annee_scolaire_id": annee.id,
            "date_debut": "2030-09-01", "date_fin": "2030-11-30",
        }, headers=auth_headers)
        assert resp.status_code == 201

    def test_admin_verrouiller_ok(self, client, auth_headers, db_session):
        annee = _creer_annee(db_session)
        resp = client.post(
            "/api/trimestres/generer",
            json={"annee_scolaire_id": annee.id},
            headers=auth_headers,
        )
        trimestre_id = resp.json()["annee_scolaire_id"]
        trimestres = client.get(f"/api/trimestres/?annee_scolaire_id={trimestre_id}", headers=auth_headers).json()
        resp = client.put(f"/api/trimestres/{trimestres[0]['id']}/verrouiller", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["verrouille"] is True


def _creer_eleve(db_session) -> models.Eleves:
    tuteur = models.Tuteurs(
        nom="Kante", prenom="Mariam", email="mariam.kante@test.com",
        telephone="0102030401", adresse="Bamako", profession="Commerçante",
    )
    db_session.add(tuteur)
    db_session.flush()
    eleve = models.Eleves(
        matricule="EL202501", nom="Traore", prenom="Awa",
        date_de_naissance=date(2015, 1, 1), lieu_de_naissance="Bamako",
        sexe="F", statut="actif", tuteur_id=tuteur.id,
    )
    db_session.add(eleve)
    db_session.commit()
    db_session.refresh(eleve)
    return eleve


def _upload_document(client, headers, eleve, categorie, filename="doc.pdf"):
    return client.post(
        "/api/documents/",
        data={"entite_type": "eleve", "entite_id": eleve.matricule, "categorie": categorie},
        files={"fichier": (filename, b"%PDF-1.4 test", "application/pdf")},
        headers=headers,
    )


class TestDocumentsSensiblesReservesAdmin:
    """Les documents de catégorie « medical » ne sont lisibles que par les admins ;
    toutes les écritures documents sont réservées à l'admin."""

    def _jeu(self, client, auth_headers, db_session):
        eleve = _creer_eleve(db_session)
        med = _upload_document(client, auth_headers, eleve, "medical", "certificat.pdf").json()
        ident = _upload_document(client, auth_headers, eleve, "identite", "cni.pdf").json()
        return eleve, med, ident

    def test_secretaire_upload_403(self, client, secretaire_headers, db_session):
        eleve = _creer_eleve(db_session)
        resp = _upload_document(client, secretaire_headers, eleve, "identite")
        assert resp.status_code == 403

    def test_secretaire_upload_legacy_403(self, client, secretaire_headers, db_session):
        eleve = _creer_eleve(db_session)
        resp = client.post(
            "/api/documents/upload",
            data={"matricule_eleve": eleve.matricule, "type_document": "acte_naissance"},
            files={"file": ("acte.pdf", b"%PDF-1.4 test", "application/pdf")},
            headers=secretaire_headers,
        )
        assert resp.status_code == 403

    def test_secretaire_patch_delete_403(self, client, auth_headers, secretaire_headers, db_session):
        _, _, ident = self._jeu(client, auth_headers, db_session)
        patch = client.patch(f"/api/documents/{ident['id']}", json={"nom": "X"}, headers=secretaire_headers)
        assert patch.status_code == 403
        delete = client.delete(f"/api/documents/{ident['id']}", headers=secretaire_headers)
        assert delete.status_code == 403

    def test_secretaire_liste_globale_exclut_medical(self, client, auth_headers, secretaire_headers, db_session):
        _, med, ident = self._jeu(client, auth_headers, db_session)
        resp = client.get("/api/documents/", headers=secretaire_headers)
        assert resp.status_code == 200
        docs = resp.json()
        assert all(d["categorie"] != "medical" for d in docs)
        assert any(d["id"] == ident["id"] for d in docs)
        assert all(d["id"] != med["id"] for d in docs)

    def test_admin_liste_globale_contient_medical(self, client, auth_headers, db_session):
        _, med, _ = self._jeu(client, auth_headers, db_session)
        resp = client.get("/api/documents/", headers=auth_headers)
        assert resp.status_code == 200
        assert any(d["id"] == med["id"] for d in resp.json())

    def test_secretaire_telechargement_medical_403(self, client, auth_headers, secretaire_headers, db_session):
        _, med, _ = self._jeu(client, auth_headers, db_session)
        resp = client.get(f"/api/documents/{med['id']}/fichier", headers=secretaire_headers)
        assert resp.status_code == 403

    def test_admin_telechargement_medical_200(self, client, auth_headers, db_session):
        _, med, _ = self._jeu(client, auth_headers, db_session)
        resp = client.get(f"/api/documents/{med['id']}/fichier", headers=auth_headers)
        assert resp.status_code == 200

    def test_secretaire_preview_medical_403(self, client, auth_headers, secretaire_headers, db_session):
        _, med, _ = self._jeu(client, auth_headers, db_session)
        resp = client.get(f"/api/documents/{med['id']}/preview", headers=secretaire_headers)
        assert resp.status_code == 403

    def test_secretaire_lecture_non_sensible_ok(self, client, auth_headers, secretaire_headers, db_session):
        _, _, ident = self._jeu(client, auth_headers, db_session)
        fichier = client.get(f"/api/documents/{ident['id']}/fichier", headers=secretaire_headers)
        assert fichier.status_code == 200
        preview = client.get(f"/api/documents/{ident['id']}/preview", headers=secretaire_headers)
        assert preview.status_code == 200


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