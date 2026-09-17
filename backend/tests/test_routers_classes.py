"""Tests d'intégration du router Classes via TestClient.

Couverture : CRUD complet, vérification disponibilité salle, détail
avec effectif et cours, protection contre suppression.
"""
import pytest
from datetime import date


def _creer_classe(client, auth_headers, **overrides):
    data = {"niveau": "1ère Année", "nom": "A", "frais_inscription": 50000, "mensualite": 10000, **overrides}
    return client.post("/api/classes/", json=data, headers=auth_headers)


def _creer_salle(client, auth_headers, nom="A101"):
    return client.post("/api/salles/", json={"nom": nom, "capacite": 30}, headers=auth_headers)


class TestCreation:
    def test_creer_classe(self, client, auth_headers):
        resp = _creer_classe(client, auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["niveau"] == "1ère Année"
        assert body["nom"] == "A"
        assert body["code_classe"] is not None
        assert body["code_classe"].startswith("CLA")

    def test_creer_classe_avec_salle(self, client, auth_headers):
        salle = _creer_salle(client, auth_headers).json()
        resp = _creer_classe(client, auth_headers, id_salle=salle["id"])
        assert resp.status_code == 201
        assert resp.json()["id_salle"] == salle["id"]

    def test_salle_deja_affectee_400(self, client, auth_headers):
        salle = _creer_salle(client, auth_headers).json()
        _creer_classe(client, auth_headers, id_salle=salle["id"])
        resp = _creer_classe(client, auth_headers, nom="B", id_salle=salle["id"])
        assert resp.status_code == 400

    def test_salle_introuvable_404(self, client, auth_headers):
        resp = _creer_classe(client, auth_headers, id_salle=99999)
        assert resp.status_code == 404

    def test_code_auto_generé(self, client, auth_headers):
        c1 = _creer_classe(client, auth_headers, nom="A").json()
        c2 = _creer_classe(client, auth_headers, nom="B").json()
        assert c1["code_classe"] != c2["code_classe"]


class TestLecture:
    def test_liste_vide(self, client, auth_headers):
        resp = client.get("/api/classes/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_liste_apres_creation(self, client, auth_headers):
        _creer_classe(client, auth_headers, nom="A")
        _creer_classe(client, auth_headers, nom="B")
        resp = client.get("/api/classes/", headers=auth_headers)
        assert len(resp.json()) == 2

    def test_detail_classe(self, client, auth_headers):
        created = _creer_classe(client, auth_headers).json()
        resp = client.get(f"/api/classes/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["niveau"] == "1ère Année"
        assert resp.json()["effectif_actuel"] == 0

    def test_classe_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/classes/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestModification:
    def test_modifier_classe(self, client, auth_headers):
        created = _creer_classe(client, auth_headers).json()
        resp = client.put(
            f"/api/classes/{created['id']}",
            json={"niveau": "2ème Année", "nom": "B"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["niveau"] == "2ème Année"

    def test_modifier_classe_changer_salle(self, client, auth_headers):
        salle1 = _creer_salle(client, auth_headers, nom="A101").json()
        salle2 = _creer_salle(client, auth_headers, nom="A102").json()
        created = _creer_classe(client, auth_headers, id_salle=salle1["id"]).json()
        resp = client.put(
            f"/api/classes/{created['id']}",
            json={"niveau": "1ère Année", "nom": "A", "id_salle": salle2["id"]},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["id_salle"] == salle2["id"]

    def test_modifier_classe_introuvable_404(self, client, auth_headers):
        resp = client.put(
            "/api/classes/99999",
            json={"niveau": "X", "nom": "Y"},
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestSuppression:
    def test_supprimer_classe_vide(self, client, auth_headers):
        created = _creer_classe(client, auth_headers).json()
        resp = client.delete(f"/api/classes/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204
        assert client.get("/api/classes/", headers=auth_headers).json() == []

    def test_supprimer_classe_avec_eleve_409(self, client, auth_headers, db_session):
        from models.tuteurs import Tuteurs
        from models.eleves import Eleves

        created = _creer_classe(client, auth_headers).json()
        tuteur = Tuteurs(
            nom="T", prenom="T", email="t@ex.com",
            telephone="+22376000000", adresse="Bamako", profession="M",
        )
        db_session.add(tuteur)
        db_session.flush()
        eleve = Eleves(
            matricule="EL9900001", nom="E", prenom="E",
            date_de_naissance=date(2010, 1, 1),
            lieu_de_naissance="Bamako", sexe="M", statut="actif",
            tuteur_id=tuteur.id, classe_id=created["id"],
        )
        db_session.add(eleve)
        db_session.commit()
        resp = client.delete(f"/api/classes/{created['id']}", headers=auth_headers)
        assert resp.status_code == 409


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/classes/")
        assert resp.status_code == 401
