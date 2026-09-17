"""Tests d'intégration du router Tuteurs via TestClient.

Couverture : CRUD complet, recherche multi-mots, comptage, protection
contre la suppression d'un tuteur lié à des élèves.
"""
import pytest
from datetime import date


TUTEUR_DATA = {
    "nom": "Diallo",
    "prenom": "Aminata",
    "email": "aminata.diallo@example.com",
    "telephone": "+223 76 00 11 22",
    "adresse": "Bamako",
    "profession": "Enseignante",
}


def _creer_tuteur(client, auth_headers, **overrides):
    data = {**TUTEUR_DATA, **overrides}
    return client.post("/api/tuteurs/", json=data, headers=auth_headers)


class TestCreation:
    def test_creer_un_tuteur(self, client, auth_headers):
        resp = _creer_tuteur(client, auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["nom"] == "Diallo"
        assert body["code_tuteur"] is not None
        assert body["code_tuteur"].startswith("TUT")

    def test_creer_plusieurs_tuteurs(self, client, auth_headers):
        _creer_tuteur(client, auth_headers, nom="T1", email="t1@ex.com")
        _creer_tuteur(client, auth_headers, nom="T2", email="t2@ex.com")
        resp = client.get("/api/tuteurs/", headers=auth_headers)
        assert len(resp.json()) == 2

    def test_refuse_champ_manquant(self, client, auth_headers):
        resp = client.post("/api/tuteurs/", json={"nom": "X"}, headers=auth_headers)
        assert resp.status_code >= 400


class TestLecture:
    def test_liste_vide(self, client, auth_headers):
        resp = client.get("/api/tuteurs/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_tuteur_par_id(self, client, auth_headers):
        created = _creer_tuteur(client, auth_headers).json()
        resp = client.get(f"/api/tuteurs/{created['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Diallo"

    def test_tuteur_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/tuteurs/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_compte_total(self, client, auth_headers):
        _creer_tuteur(client, auth_headers, nom="T1", email="t1@ex.com")
        _creer_tuteur(client, auth_headers, nom="T2", email="t2@ex.com")
        resp = client.get("/api/tuteurs/compte", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2


class TestRecherche:
    def test_recherche_par_nom(self, client, auth_headers):
        _creer_tuteur(client, auth_headers, nom="Konaté", prenom="Ibrahim", email="ibk@ex.com")
        _creer_tuteur(client, auth_headers, nom="Traoré", prenom="Fatoumata", email="ft@ex.com")
        resp = client.get("/api/tuteurs/?q=Konaté", headers=auth_headers)
        noms = [t["nom"] for t in resp.json()]
        assert "Konaté" in noms
        assert "Traoré" not in noms

    def test_recherche_multi_mots(self, client, auth_headers):
        _creer_tuteur(client, auth_headers, nom="Fall", prenom="Aboubacar", email="ab@ex.com")
        _creer_tuteur(client, auth_headers, nom="Diop", prenom="Mariama", email="md@ex.com")
        resp = client.get("/api/tuteurs/?q=fall+ab", headers=auth_headers)
        assert len(resp.json()) == 1
        assert resp.json()[0]["nom"] == "Fall"


class TestModification:
    def test_modifier_un_tuteur(self, client, auth_headers):
        created = _creer_tuteur(client, auth_headers).json()
        resp = client.put(
            f"/api/tuteurs/{created['id']}",
            json={**TUTEUR_DATA, "nom": "NouveauNom"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nom"] == "NouveauNom"


class TestSuppression:
    def test_supprimer_tuteur_sans_eleves(self, client, auth_headers):
        created = _creer_tuteur(client, auth_headers).json()
        resp = client.delete(f"/api/tuteurs/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204
        assert client.get("/api/tuteurs/", headers=auth_headers).json() == []

    def test_supprimer_tuteur_404(self, client, auth_headers):
        resp = client.delete("/api/tuteurs/99999", headers=auth_headers)
        assert resp.status_code == 404

    def test_supprimer_tuteur_lie_a_eleve_409(self, client, auth_headers, db_session):
        """Un tuteur avec des élèves ne peut pas être supprimé."""
        from models.tuteurs import Tuteurs
        from models.eleves import Eleves

        tuteur = Tuteurs(
            nom="Test", prenom="Tut", email="tut@ex.com",
            telephone="+22376000000", adresse="Bamako", profession="C",
        )
        db_session.add(tuteur)
        db_session.flush()
        eleve = Eleves(
            matricule="EL9900001", nom="E", prenom="E",
            date_de_naissance=date(2010, 1, 1),
            lieu_de_naissance="Bamako", sexe="M", statut="actif",
            tuteur_id=tuteur.id,
        )
        db_session.add(eleve)
        db_session.commit()

        resp = client.delete(f"/api/tuteurs/{tuteur.id}", headers=auth_headers)
        assert resp.status_code == 409


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/tuteurs/")
        assert resp.status_code == 401

    def test_creer_sans_token_401(self, client):
        resp = client.post("/api/tuteurs/", json=TUTEUR_DATA)
        assert resp.status_code == 401
