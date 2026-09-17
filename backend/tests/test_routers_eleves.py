"""Tests d'intégration du router Élèves via TestClient.

Couverture : CRUD complet, recherche par nom/prénom/matricule, activation/
désactivation, dossier complet, inscription automatique, et protections.
"""
import pytest
from datetime import date


def _creer_tuteur(client, auth_headers):
    return client.post("/api/tuteurs/", json={
        "nom": "Diallo", "prenom": "Aminata", "email": "a@ex.com",
        "telephone": "+223 76 00 11 22", "adresse": "Bamako", "profession": "Enseignante",
    }, headers=auth_headers)


def _creer_annee(client, auth_headers):
    return client.post("/api/anneesScolaires/", json={
        "libelle": "2025-2026", "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers)


def _creer_classe(client, auth_headers, niveau="1ère Année", nom="A"):
    return client.post("/api/classes/", json={"niveau": niveau, "nom": nom}, headers=auth_headers)


def _creer_eleve(client, auth_headers, tuteur_id, classe_id=None):
    """Crée un élève. Sans classe_id fournie, crée année active + classe au préalable."""
    if classe_id is None:
        _creer_annee(client, auth_headers)
        classe = _creer_classe(client, auth_headers).json()
        classe_id = classe["id"]
    return client.post("/api/eleves/", json={
        "nom": "Konaté", "prenom": "Amadou",
        "date_de_naissance": "2012-03-15",
        "lieu_de_naissance": "Bamako", "sexe": "M",
        "tuteur_id": tuteur_id, "classe_id": classe_id,
    }, headers=auth_headers)


class TestCreation:
    def test_creer_eleve(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        resp = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"])
        assert resp.status_code == 201
        body = resp.json()
        assert body["matricule"].startswith("AU")
        assert body["nom"] == "Konaté"
        assert body["tuteur"]["id"] == tuteur["id"]

    def test_creer_eleve_sans_classe_422(self, client, auth_headers):
        """Un élève sans classe ne peut plus être créé (422)."""
        tuteur = _creer_tuteur(client, auth_headers).json()
        resp = client.post("/api/eleves/", json={
            "nom": "Konaté", "prenom": "Amadou",
            "date_de_naissance": "2012-03-15",
            "lieu_de_naissance": "Bamako", "sexe": "M",
            "tuteur_id": tuteur["id"],
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_creer_eleve_classe_introuvable_404(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        resp = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"], classe_id=99999)
        assert resp.status_code == 404

    def test_creer_eleve_avec_classe_inscrit(self, client, auth_headers):
        """Créer un élève avec une classe crée automatiquement une inscription."""
        _creer_annee(client, auth_headers)  # active year required
        tuteur = _creer_tuteur(client, auth_headers).json()
        classe = _creer_classe(client, auth_headers).json()
        resp = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"], classe_id=classe["id"])
        assert resp.status_code == 201
        matricule = resp.json()["matricule"]
        inscs = client.get(f"/api/inscriptions/?matricule_eleve={matricule}", headers=auth_headers)
        assert inscs.status_code == 200
        assert len(inscs.json()) >= 1

    def test_tuteur_introuvable_404(self, client, auth_headers):
        resp = _creer_eleve(client, auth_headers, tuteur_id=99999)
        assert resp.status_code == 404

    def test_sans_annee_active_400(self, client, auth_headers):
        """Avec classe mais sans année scolaire active, l'inscription échoue (400)."""
        tuteur = _creer_tuteur(client, auth_headers).json()
        classe = _creer_classe(client, auth_headers).json()
        resp = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"], classe_id=classe["id"])
        assert resp.status_code == 400

    def test_annee_scolaire_invalide_avec_classe_404(self, client, auth_headers):
        """Avec classe_id et année inexistante → 404 sur l'inscription."""
        tuteur = _creer_tuteur(client, auth_headers).json()
        classe = _creer_classe(client, auth_headers).json()
        data = {
            "nom": "X", "prenom": "Y", "date_de_naissance": "2012-01-01",
            "lieu_de_naissance": "Bamako", "sexe": "F",
            "tuteur_id": tuteur["id"], "classe_id": classe["id"],
            "annee_scolaire_id": 99999,
        }
        resp = client.post("/api/eleves/", json=data, headers=auth_headers)
        assert resp.status_code == 404


class TestLecture:
    def test_liste_vide(self, client, auth_headers):
        resp = client.get("/api/eleves/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_liste_apres_creation(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"])
        resp = client.get("/api/eleves/", headers=auth_headers)
        assert len(resp.json()) == 1

    def test_get_par_matricule(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.get(f"/api/eleves/{created['matricule']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Konaté"

    def test_eleve_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/eleves/AU9900000", headers=auth_headers)
        assert resp.status_code == 404

    def test_compte(self, client, auth_headers):
        _creer_annee(client, auth_headers)  # active year required
        tuteur = _creer_tuteur(client, auth_headers).json()
        _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"])
        classe = _creer_classe(client, auth_headers).json()
        resp = client.post("/api/eleves/", json={
            "nom": "Konaté", "prenom": "Autre",
            "date_de_naissance": "2012-03-15", "lieu_de_naissance": "Bamako",
            "sexe": "F", "tuteur_id": tuteur["id"], "classe_id": classe["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201
        resp = client.get("/api/eleves/compte", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_recherche_par_nom(self, client, auth_headers):
        _creer_annee(client, auth_headers)  # active year required
        tuteur = _creer_tuteur(client, auth_headers).json()
        _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"])
        classe = _creer_classe(client, auth_headers).json()
        client.post("/api/eleves/", json={
            "nom": "Traoré", "prenom": "X",
            "date_de_naissance": "2012-03-15", "lieu_de_naissance": "Bamako",
            "sexe": "M", "tuteur_id": tuteur["id"], "classe_id": classe["id"],
        }, headers=auth_headers)
        resp = client.get("/api/eleves/?q=Konaté", headers=auth_headers)
        noms = [e["nom"] for e in resp.json()]
        assert "Konaté" in noms
        assert "Traoré" not in noms


class TestModification:
    def test_modifier_eleve(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.put(
            f"/api/eleves/{created['matricule']}",
            json={"nom": "NouveauNom"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nom"] == "NouveauNom"


class TestActivationDesactivation:
    def test_desactiver_eleve(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.patch(f"/api/eleves/{created['matricule']}/desactiver", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["statut"] == "inactif"

    def test_activer_eleve(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        client.patch(f"/api/eleves/{created['matricule']}/desactiver", headers=auth_headers)
        resp = client.patch(f"/api/eleves/{created['matricule']}/activer", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["statut"] == "actif"


class TestDossierComplet:
    def test_dossier_eleve(self, client, auth_headers):
        _creer_annee(client, auth_headers)  # active year required
        tuteur = _creer_tuteur(client, auth_headers).json()
        classe = _creer_classe(client, auth_headers).json()
        created = client.post("/api/eleves/", json={
            "nom": "Konaté", "prenom": "Amadou",
            "date_de_naissance": "2012-03-15",
            "lieu_de_naissance": "Bamako", "sexe": "M",
            "tuteur_id": tuteur["id"], "classe_id": classe["id"],
            "nom_pere": "Keita", "prenom_pere": "Modibo", "fonction_pere": "Commerçant",
            "nom_mere": "Coulibaly", "prenom_mere": "Aminata", "fonction_mere": "Ménagère",
        }, headers=auth_headers).json()
        resp = client.get(f"/api/eleves/{created['matricule']}/dossier", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["matricule"] == created["matricule"]
        assert body["tuteur"]["id"] == tuteur["id"]
        assert body["nom_pere"] == "Keita"
        assert body["prenom_pere"] == "Modibo"
        assert body["fonction_pere"] == "Commerçant"
        assert body["nom_mere"] == "Coulibaly"
        assert body["prenom_mere"] == "Aminata"
        assert body["fonction_mere"] == "Ménagère"
        assert isinstance(body["inscriptions"], list)
        assert isinstance(body["notes"], list)
        assert isinstance(body["absences"], list)
        assert isinstance(body["bulletins"], list)

    def test_dossier_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/eleves/AU9900000/dossier", headers=auth_headers)
        assert resp.status_code == 404


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/eleves/")
        assert resp.status_code == 401
