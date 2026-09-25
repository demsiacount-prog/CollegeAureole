"""Tests du router `setup` (initialisation unique de l'application).

Zone jusqu'ici non couverte par la suite : `test_robustesse_sauvegardes.py`
teste `/api/setup/reset` et `/api/setup/purge-donnees` (protection par
snapshot), mais aucun test n'exerçait `/api/setup/run`, `/api/setup/status`,
`/api/setup/progress` ni `/api/setup/logo` — c'est-à-dire le tout premier
parcours utilisateur de l'application (aucun compte n'existe encore).
"""
import io

import pytest

import models
from services import initialisation


PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\x18\xdd\x8d\xb0\x00\x00\x00\x00IEND\xaeB`\x82"
)

PAYLOAD = {
    "etablissement": {"nom": "Collège Auréole", "sigle": "CA", "academie": "Bamako-Rive Gauche", "cap": "CAP1"},
    "admin": {"nom": "Diarra", "prenom": "Fatoumata", "email": "admin@aureole.ml", "mot_de_passe": "motdepasse123"},
    "annee_scolaire": {"date_debut": "2030-10-01", "date_fin": "2031-07-31"},
}


@pytest.fixture(autouse=True)
def _progression_isolee():
    """`initialisation._progress` est un dict global tenu en mémoire de
    processus (pas en base) : il survit donc d'un test à l'autre alors que le
    schéma, lui, est purgé avant chaque test (cf. conftest._schema_purge).
    Sans cette remise à zéro, l'ordre d'exécution des tests changerait le
    résultat de `GET /api/setup/status` / `/progress` (état figé du test
    précédent) : symptôme concret de cet état global documenté ci-dessous
    dans le rapport de revue."""
    initialisation._progress.update(
        run_id=None, en_cours=False, etape=0, message="",
        pourcent=0, termine=False, erreur=None,
    )
    yield


def _executer_run(client, payload=None):
    resp = client.post("/api/setup/run", json=payload or PAYLOAD)
    assert resp.status_code == 202, resp.text
    return resp.json()


class TestStatus:
    def test_avant_configuration(self, client):
        resp = client.get("/api/setup/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data == {
            "configured": False,
            "etablissement": False,
            "admin": False,
            "annee_scolaire": False,
            "donnees_presentes": False,
            "progression": None,
        }

    def test_apres_configuration(self, client):
        _executer_run(client)
        data = client.get("/api/setup/status").json()
        assert data["configured"] is True
        assert data["etablissement"] is True
        assert data["admin"] is True
        assert data["annee_scolaire"] is True


class TestProgress:
    def test_sans_execution(self, client):
        data = client.get("/api/setup/progress").json()
        assert data["en_cours"] is False
        assert data["termine"] is False
        assert data["etape"] == 0

    def test_apres_execution_reussie(self, client):
        _executer_run(client)
        data = client.get("/api/setup/progress").json()
        assert data["termine"] is True
        assert data["erreur"] is None
        assert data["pourcent"] == 100
        assert data["etape"] == initialisation.NB_ETAPES


class TestRun:
    def test_cree_etablissement_admin_et_annee(self, client, db_session):
        _executer_run(client)

        etab = db_session.query(models.Etablissement).one()
        assert etab.nom == "Collège Auréole"
        assert etab.academie == "Bamako-Rive Gauche"

        annee = db_session.query(models.AnneesScolaires).one()
        assert annee.active is True
        assert annee.libelle == "2030-2031"

        admin = db_session.query(models.Utilisateurs).one()
        assert admin.email == "admin@aureole.ml"

    def test_genere_les_periodes_de_lannee(self, client, db_session):
        _executer_run(client)
        annee = db_session.query(models.AnneesScolaires).one()
        periodes = (
            db_session.query(models.Trimestres)
            .filter(models.Trimestres.annee_scolaire_id == annee.id)
            .all()
        )
        types = {p.type for p in periodes}
        assert types == {"TRIMESTRE", "COMPOSITION"}

    def test_admin_cree_peut_se_connecter(self, client):
        _executer_run(client)
        resp = client.post(
            "/api/auth/connexion",
            json={"email": "admin@aureole.ml", "mot_de_passe": "motdepasse123"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["access_token"]

    def test_sans_annee_scolaire_utilise_une_periode_par_defaut(self, client, db_session):
        payload = {k: v for k, v in PAYLOAD.items() if k != "annee_scolaire"}
        _executer_run(client, payload)
        assert db_session.query(models.AnneesScolaires).count() == 1

    def test_refuse_si_deja_configure(self, client):
        _executer_run(client)
        resp = client.post("/api/setup/run", json=PAYLOAD)
        assert resp.status_code == 409

    def test_refuse_si_initialisation_deja_en_cours(self, client, monkeypatch):
        monkeypatch.setattr(
            initialisation,
            "get_progress",
            lambda: {**initialisation._progress, "en_cours": True},
        )
        resp = client.post("/api/setup/run", json=PAYLOAD)
        assert resp.status_code == 409

    def test_email_admin_invalide_rejete(self, client):
        payload = {**PAYLOAD, "admin": {**PAYLOAD["admin"], "email": "pas-un-email"}}
        resp = client.post("/api/setup/run", json=payload)
        assert resp.status_code == 422

    def test_mot_de_passe_trop_court_rejete(self, client):
        payload = {**PAYLOAD, "admin": {**PAYLOAD["admin"], "mot_de_passe": "court"}}
        resp = client.post("/api/setup/run", json=payload)
        assert resp.status_code == 422

    def test_date_fin_avant_date_debut_rejetee(self, client):
        payload = {
            **PAYLOAD,
            "annee_scolaire": {"date_debut": "2031-07-31", "date_fin": "2030-10-01"},
        }
        resp = client.post("/api/setup/run", json=payload)
        assert resp.status_code == 422

    def test_champ_inconnu_rejete(self, client):
        payload = {**PAYLOAD, "champ_surprise": True}
        resp = client.post("/api/setup/run", json=payload)
        assert resp.status_code == 422

    def test_echec_execution_nettoie_letat(self, client, db_session, monkeypatch):
        """Une erreur pendant l'exécution en tâche de fond doit laisser la
        base dans un état permettant de relancer l'initialisation (aucune
        ligne orpheline, `configured` reste False)."""

        def _boom(*_a, **_k):
            raise RuntimeError("panne simulée")

        monkeypatch.setattr(initialisation, "generer_periodes_par_defaut", _boom)
        _executer_run(client)

        assert client.get("/api/setup/progress").json()["erreur"] is not None
        assert db_session.query(models.Utilisateurs).count() == 0
        assert client.get("/api/setup/status").json()["configured"] is False


class TestLogo:
    def test_upload_avant_configuration_ok(self, client):
        resp = client.post(
            "/api/setup/logo",
            files={"file": ("logo.png", io.BytesIO(PNG_1PX), "image/png")},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["logo"].startswith("/uploads/logos/")

    def test_upload_refuse_si_deja_configure(self, client):
        _executer_run(client)
        resp = client.post(
            "/api/setup/logo",
            files={"file": ("logo.png", io.BytesIO(PNG_1PX), "image/png")},
        )
        assert resp.status_code == 409

    def test_upload_contenu_non_image_refuse(self, client):
        resp = client.post(
            "/api/setup/logo",
            files={"file": ("logo.png", io.BytesIO(b"pas une image"), "image/png")},
        )
        assert resp.status_code == 400
