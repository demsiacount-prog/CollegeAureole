"""Tests d'intégration du router Cours via TestClient.

Couverture : CRUD complet, affectation cours-classe avec coefficients,
refus coefficient EF1, enseignant introuvable, protection suppression.
"""
import pytest


def _creer_enseignant(client, auth_headers, email="ens@ex.com"):
    return client.post("/api/enseignants/", json={
        "nom": "E", "prenom": "E", "email": email,
        "telephone": "+22376000000", "adresse": "Bamako", "specialite": "X",
    }, headers=auth_headers)


def _creer_classe(client, auth_headers, niveau="7ème Année", nom="A"):
    return client.post("/api/classes/", json={"niveau": niveau, "nom": nom}, headers=auth_headers)


class TestCreation:
    def test_creer_cours_sans_affectation(self, client, auth_headers):
        resp = client.post("/api/cours/", json={
            "nom": "Mathématiques", "description": "Algèbre",
            "volume_horaire": 4, "affectations": [],
        }, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["nom"] == "Mathématiques"
        assert body["code_cours"].startswith("COU")

    def test_creer_cours_avec_enseignant(self, client, auth_headers):
        ens = _creer_enseignant(client, auth_headers).json()
        resp = client.post("/api/cours/", json={
            "nom": "Français", "description": "Littérature",
            "volume_horaire": 3, "matricule_enseignant": ens["matricule"],
            "affectations": [],
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["matricule_enseignant"] == ens["matricule"]

    def test_enseignant_introuvable_404(self, client, auth_headers):
        resp = client.post("/api/cours/", json={
            "nom": "X", "description": "", "volume_horaire": 1,
            "matricule_enseignant": "ENS9900000",
            "affectations": [],
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_classe_introuvable_404(self, client, auth_headers):
        resp = client.post("/api/cours/", json={
            "nom": "X", "description": "", "volume_horaire": 1,
            "affectations": [{"id_classe": 99999, "coefficient": 1.0}],
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_coefficient_ef1_refuse(self, client, auth_headers):
        cl = _creer_classe(client, auth_headers, niveau="1ère Année").json()
        resp = client.post("/api/cours/", json={
            "nom": "X", "description": "", "volume_horaire": 1,
            "affectations": [{"id_classe": cl["id"], "coefficient": 2.0}],
        }, headers=auth_headers)
        assert resp.status_code == 422


class TestLecture:
    def test_liste(self, client, auth_headers):
        client.post("/api/cours/", json={
            "nom": "M", "description": "", "volume_horaire": 1, "affectations": [],
        }, headers=auth_headers)
        resp = client.get("/api/cours/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_get_cours(self, client, auth_headers):
        created = client.post("/api/cours/", json={
            "nom": "M", "description": "", "volume_horaire": 1, "affectations": [],
        }, headers=auth_headers).json()
        resp = client.get(f"/api/cours/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200

    def test_cours_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/cours/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestModification:
    def test_modifier_cours(self, client, auth_headers):
        created = client.post("/api/cours/", json={
            "nom": "M", "description": "", "volume_horaire": 1, "affectations": [],
        }, headers=auth_headers).json()
        resp = client.put(f"/api/cours/{created['id']}", json={
            "nom": "Physique", "description": "Mécanique",
            "volume_horaire": 3, "affectations": [],
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Physique"


class TestSuppression:
    def test_supprimer_sans_lien(self, client, auth_headers):
        created = client.post("/api/cours/", json={
            "nom": "M", "description": "", "volume_horaire": 1, "affectations": [],
        }, headers=auth_headers).json()
        resp = client.delete(f"/api/cours/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_supprimer_avec_notes_409(self, client, auth_headers, db_session):
        """Un cours avec des notes ne peut pas être supprimé."""
        from datetime import date

        from models.classes import Classes
        from models.cours import Cours
        from models.eleves import Eleves
        from models.enseignants import Enseignants
        from models.notes import Notes
        from models.tuteurs import Tuteurs

        cl = Classes(niveau="7ème Année", nom="A")
        db_session.add(cl)
        db_session.flush()
        tuteur = Tuteurs(
            nom="T", prenom="T", email="t@x.com",
            telephone="+22376000000", adresse="B", profession="M",
        )
        db_session.add(tuteur)
        db_session.flush()
        eleve = Eleves(
            nom="E", prenom="E", date_de_naissance=date(2012, 1, 1),
            lieu_de_naissance="B", sexe="M", tuteur_id=tuteur.id,
        )
        db_session.add(eleve)
        db_session.flush()
        enseignant = Enseignants(
            nom="N", prenom="P", telephone="+22376000000", adresse="B", specialite="S",
        )
        db_session.add(enseignant)
        db_session.flush()
        cours = Cours(nom="M", description="", volume_horaire=1)
        db_session.add(cours)
        db_session.flush()
        db_session.add(Notes(
            matricule_eleve=eleve.matricule, id_cours=cours.id,
            id_classe=cl.id, matricule_enseignant=enseignant.matricule,
            note=12.0,
        ))
        db_session.commit()
        resp = client.delete(f"/api/cours/{cours.id}", headers=auth_headers)
        assert resp.status_code == 409


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/cours/")
        assert resp.status_code == 401
