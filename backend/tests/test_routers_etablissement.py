"""Tests du router `etablissement` (fiche établissement, logo, infrastructures).

`test_securite_rbac.py` vérifie déjà le 403 non-admin sur PUT / upload logo.
Ce fichier couvre le comportement fonctionnel (encore non testé) : lecture,
écriture, validations, et le sous-système infrastructures dans son
intégralité (aucun test préexistant)."""
import io

import pytest

import models


PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture()
def fiche(db_session):
    etab = models.Etablissement(
        id=1, nom="Collège Auréole", academie="Bamako-Rive Gauche", cap="CAP1",
    )
    db_session.add(etab)
    db_session.commit()
    db_session.refresh(etab)
    return etab


@pytest.fixture()
def annee_active(db_session):
    from datetime import date

    annee = models.AnneesScolaires(
        libelle="2030-2031", date_debut=date(2030, 10, 1), date_fin=date(2031, 7, 31), active=True,
    )
    db_session.add(annee)
    db_session.commit()
    db_session.refresh(annee)
    return annee


class TestFicheEtablissement:
    def test_get_sans_fiche_404(self, client, auth_headers):
        resp = client.get("/api/etablissement", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_sans_authentification_est_accessible(self, client, fiche):
        """Constat (pas une assertion de sécurité voulue) : contrairement à
        `/api/etablissement/infrastructures` (protégé par
        `Depends(get_current_user)`) et à la quasi-totalité des autres GET de
        l'API, `GET /api/etablissement` n'exige AUCUNE authentification —
        `get_etablissement` ne déclare aucune dépendance de sécurité. N'importe
        qui atteignant le serveur (pas seulement le poste local) peut lire nom,
        adresse, téléphone et email de l'établissement sans être connecté. Ce
        test documente le comportement actuel ; à corriger en ajoutant
        `Depends(get_current_user)` si ce n'est pas voulu (cf. rapport de revue)."""
        resp = client.get("/api/etablissement")
        assert resp.status_code == 200

    def test_get_ok(self, client, auth_headers, fiche):
        resp = client.get("/api/etablissement", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Collège Auréole"

    def test_put_met_a_jour_et_persiste(self, client, auth_headers, fiche):
        payload = {
            "nom": "Collège Auréole Nouveau",
            "adresse": "Quartier du Fleuve, Bamako",
            "telephone": "+223 20 22 33 44",
            "email": "contact@aureole.ml",
            "academie": "Bamako-Rive Gauche",
            "cap": "CAP1",
        }
        resp = client.put("/api/etablissement", json=payload, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["adresse"] == "Quartier du Fleuve, Bamako"

        relu = client.get("/api/etablissement", headers=auth_headers).json()
        assert relu["nom"] == "Collège Auréole Nouveau"
        assert relu["telephone"] == "+223 20 22 33 44"

    def test_put_email_invalide_422(self, client, auth_headers, fiche):
        resp = client.put(
            "/api/etablissement",
            json={"nom": "X", "email": "pas-un-email"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_put_champ_inconnu_rejete_422(self, client, auth_headers, fiche):
        resp = client.put(
            "/api/etablissement",
            json={"nom": "X", "champ_surprise": "y"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_put_academie_cap_omis_sont_effaces(self, client, auth_headers, fiche, db_session):
        """Constat : contrairement aux autres champs (préservés si omis, car
        `if value is not None: setattr(...)`), `academie`/`cap` sont
        forcés à `''` dès qu'ils sont absents du payload — le PUT n'étant
        pas un vrai partiel sur ces deux colonnes. Un client qui ne
        renvoie pas ces champs (ex. formulaire ne les affichant pas)
        efface silencieusement une valeur déjà enregistrée. Même famille
        de bug que BUG 2 (taches.md, `lien_parente`), non corrigée ici :
        ce test documente le comportement actuel plutôt que de le
        modifier, pour qu'un futur correctif le fasse échouer
        intentionnellement."""
        assert fiche.academie == "Bamako-Rive Gauche"
        resp = client.put("/api/etablissement", json={"nom": "X"}, headers=auth_headers)
        assert resp.status_code == 200
        db_session.refresh(fiche)
        assert fiche.academie == ""
        assert fiche.cap == ""


class TestLogoEtablissement:
    def test_upload_ok(self, client, auth_headers, tmp_path, monkeypatch):
        monkeypatch.setenv("AUREOLE_UPLOADS_DIR", str(tmp_path))
        import importlib
        import routers.etablissement as mod
        importlib.reload(mod)

        resp = client.post(
            "/api/etablissement/logo",
            files={"file": ("logo.png", io.BytesIO(PNG_1PX), "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        chemin = resp.json()["logo"]
        assert chemin.startswith("/uploads/logos/logo_")
        assert chemin.endswith(".png")
        assert (tmp_path / "logos" / chemin.rsplit("/", 1)[-1]).exists()
        importlib.reload(mod)

    def test_upload_type_non_supporte_400(self, client, auth_headers):
        resp = client.post(
            "/api/etablissement/logo",
            files={"file": ("logo.png", io.BytesIO(b"contenu quelconque"), "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_upload_trop_volumineux_400(self, client, auth_headers):
        contenu = PNG_1PX + b"\x00" * (2 * 1024 * 1024 + 1)
        resp = client.post(
            "/api/etablissement/logo",
            files={"file": ("logo.png", io.BytesIO(contenu), "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_upload_sans_admin_403(self, client, db_session):
        from hashing import hash_password
        from security import create_access_token

        secretaire = models.Utilisateurs(
            nom="S", prenom="T", email="secretaire.logo@test.com",
            mot_de_passe=hash_password("secret123"), role="SECRETAIRE", actif=True,
        )
        db_session.add(secretaire)
        db_session.commit()
        headers = {"Authorization": f"Bearer {create_access_token(utilisateur_id=secretaire.id)}"}

        resp = client.post(
            "/api/etablissement/logo",
            files={"file": ("logo.png", io.BytesIO(PNG_1PX), "image/png")},
            headers=headers,
        )
        assert resp.status_code == 403


class TestInfrastructures:
    def test_get_sans_annee_active_404(self, client, auth_headers):
        resp = client.get("/api/etablissement/infrastructures", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_annee_active_sans_donnees_404(self, client, auth_headers, annee_active):
        resp = client.get("/api/etablissement/infrastructures", headers=auth_headers)
        assert resp.status_code == 404

    def test_put_cree_pour_annee_active(self, client, auth_headers, annee_active):
        payload = {"salles_dur": 6, "salles_semi_dur": 2, "tables_bancs": 120}
        resp = client.put("/api/etablissement/infrastructures", json=payload, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["salles_dur"] == 6
        assert body["id_annee_scolaire"] == annee_active.id

    def test_put_puis_get_coherents(self, client, auth_headers, annee_active):
        client.put(
            "/api/etablissement/infrastructures",
            json={"chaises": 200},
            headers=auth_headers,
        )
        resp = client.get("/api/etablissement/infrastructures", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["chaises"] == 200

    def test_put_deux_fois_ne_duplique_pas(self, client, auth_headers, annee_active, db_session):
        client.put("/api/etablissement/infrastructures", json={"armoires": 3}, headers=auth_headers)
        client.put("/api/etablissement/infrastructures", json={"armoires": 5}, headers=auth_headers)
        total = db_session.query(models.EtablissementInfrastructures).count()
        assert total == 1
        resp = client.get("/api/etablissement/infrastructures", headers=auth_headers)
        assert resp.json()["armoires"] == 5

    def test_put_annee_scolaire_id_introuvable_404(self, client, auth_headers):
        resp = client.put(
            "/api/etablissement/infrastructures",
            json={"id_annee_scolaire": 999999, "chaises": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_put_sans_annee_active_ni_id_400(self, client, auth_headers):
        resp = client.put(
            "/api/etablissement/infrastructures",
            json={"chaises": 10},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_put_champ_inconnu_422(self, client, auth_headers, annee_active):
        resp = client.put(
            "/api/etablissement/infrastructures",
            json={"champ_surprise": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_put_valeur_negative_422(self, client, auth_headers, annee_active):
        resp = client.put(
            "/api/etablissement/infrastructures",
            json={"chaises": -1},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_put_sans_admin_403(self, client, db_session, annee_active):
        from hashing import hash_password
        from security import create_access_token

        secretaire = models.Utilisateurs(
            nom="S", prenom="T", email="secretaire.infra@test.com",
            mot_de_passe=hash_password("secret123"), role="SECRETAIRE", actif=True,
        )
        db_session.add(secretaire)
        db_session.commit()
        headers = {"Authorization": f"Bearer {create_access_token(utilisateur_id=secretaire.id)}"}

        resp = client.put(
            "/api/etablissement/infrastructures",
            json={"chaises": 1},
            headers=headers,
        )
        assert resp.status_code == 403
