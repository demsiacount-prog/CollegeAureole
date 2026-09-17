"""Tests d'intégration du router Inscriptions via TestClient.

Couverture : création inscription avec echeancier, dossier complet,
historique, modification, suppression, passage-annee.
"""
import pytest
from datetime import date

import models


def _creer_tuteur(client, auth_headers):
    return client.post("/api/tuteurs/", json={
        "nom": "T", "prenom": "T", "email": "t@ex.com",
        "telephone": "+22376000000", "adresse": "Bamako", "profession": "M",
    }, headers=auth_headers)


def _creer_classe(client, auth_headers, frais=50000, mensualite=10000):
    return client.post("/api/classes/", json={
        "niveau": "7ème Année", "nom": "A",
        "frais_inscription": frais, "mensualite": mensualite,
    }, headers=auth_headers)


def _creer_annee(client, auth_headers, **overrides):
    return client.post("/api/anneesScolaires/", json={
        "libelle": "2025-2026", "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
        **overrides,
    }, headers=auth_headers)


def _creer_eleve(db_session, tuteur_id):
    """Crée un élève directement en base, sans classe ni inscription.

    La création via l'API exige désormais une classe (et génère une
    inscription) : pour tester le module Inscriptions (inscrire un élève
    existant), on insère l'élève à la main.
    """
    eleve = models.Eleves(
        nom="Konaté", prenom="Amadou",
        date_de_naissance=date(2012, 3, 15),
        lieu_de_naissance="Bamako", sexe="M",
        tuteur_id=tuteur_id,
    )
    db_session.add(eleve)
    db_session.commit()
    db_session.refresh(eleve)
    return eleve


class TestCreationInscription:
    def test_creer_inscription(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        resp = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
            "statut": "Inscrit",
        }, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["code_inscription"].startswith("INS")
        assert body["montant_total"] >= 50000  # au minimum les frais d'inscription
        assert body["montant_total"] == 50000  # prorata: date_inscription > fin année => 0 mensualités

    def test_creer_inscription_avec_nb_redoublements(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        resp = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
            "statut": "Redoublant",
            "nb_redoublements": 3,
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["nb_redoublements"] == 3

    def test_creer_inscription_nb_redoublements_defaut(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        resp = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["nb_redoublements"] == 0

    def test_eleve_introuvable_404(self, client, auth_headers):
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        resp = client.post("/api/inscriptions/", json={
            "matricule_eleve": "EL9900000",
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_doublon_409(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        payload = {
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }
        resp1 = client.post("/api/inscriptions/", json=payload, headers=auth_headers)
        assert resp1.status_code == 201
        resp2 = client.post("/api/inscriptions/", json=payload, headers=auth_headers)
        assert resp2.status_code == 409

    def test_annee_cloturee_409(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers, active=False).json()
        client.put(f"/api/anneesScolaires/{annee['id']}/cloturer", headers=auth_headers)
        eleve = _creer_eleve(db_session, t["id"])
        resp = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 409


class TestDossierComplet:
    def test_creer_dossier_complet_avec_tuteur_existant(self, client, auth_headers):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        resp = client.post("/api/inscriptions/dossier-complet", json={
            "tuteur_id": t["id"],
            "eleve": {
                "nom": "Nouveau", "prenom": "Élève",
                "date_de_naissance": "2012-01-01",
                "lieu_de_naissance": "Bamako", "sexe": "F",
            },
            "classe_id": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201

    def test_creer_dossier_complet_avec_nouveau_tuteur(self, client, auth_headers):
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        resp = client.post("/api/inscriptions/dossier-complet", json={
            "tuteur": {
                "nom": "Nouveau", "prenom": "Tuteur",
                "email": "nouveau@ex.com",
                "telephone": "+22376000000",
                "adresse": "Bamako", "profession": "M",
            },
            "eleve": {
                "nom": "Élève", "prenom": "Nouveau",
                "date_de_naissance": "2012-01-01",
                "lieu_de_naissance": "Bamako", "sexe": "M",
            },
            "classe_id": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201

    def test_dossier_complet_persiste_etat_civil(self, client, auth_headers):
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        resp = client.post("/api/inscriptions/dossier-complet", json={
            "tuteur": {
                "nom": "Nouveau", "prenom": "Tuteur",
                "email": "etat@ex.com",
                "telephone": "+22376000001",
                "adresse": "Bamako", "profession": "M",
            },
            "eleve": {
                "nom": "Élève", "prenom": "Nouveau",
                "date_de_naissance": "2012-01-01",
                "lieu_de_naissance": "Bamako", "sexe": "M",
                "acte_naissance": True,
                "numero_acte": "N° 1234/25",
                "jugement_suppletif": None,
                "date_acte": "2025-03-10",
                "delivre_par": "Mairie de Bamako",
            },
            "classe_id": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201
        matricule = resp.json()["matricule_eleve"]
        eleve = client.get(f"/api/eleves/{matricule}", headers=auth_headers).json()
        assert eleve["acte_naissance"] is True
        assert eleve["numero_acte"] == "N° 1234/25"
        assert eleve["date_acte"] == "2025-03-10"
        assert eleve["delivre_par"] == "Mairie de Bamako"

    def test_tuteur_manquant_400(self, client, auth_headers):
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        resp = client.post("/api/inscriptions/dossier-complet", json={
            "eleve": {
                "nom": "Élève", "prenom": "Nouveau",
                "date_de_naissance": "2012-01-01",
                "lieu_de_naissance": "Bamako", "sexe": "M",
            },
            "classe_id": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 400


class TestListeFiltrage:
    def test_liste_avec_filtres(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        resp = client.get(f"/api/inscriptions/?matricule_eleve={eleve.matricule}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_compte(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        resp = client.get("/api/inscriptions/compte", headers=auth_headers)
        assert resp.json()["total"] == 1


class TestModification:
    def test_modifier_inscription(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        insc = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers).json()
        resp = client.put(f"/api/inscriptions/{insc['id']}", json={
            "observation": "Nouvelle observation",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["observation"] == "Nouvelle observation"


class TestSuppression:
    def test_supprimer_inscription(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        insc = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers).json()
        resp = client.delete(f"/api/inscriptions/{insc['id']}", headers=auth_headers)
        assert resp.status_code == 204


class TestHistoriqueEleve:
    def test_historique(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        resp = client.get(f"/api/inscriptions/eleve/{eleve.matricule}/historique", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/inscriptions/")
        assert resp.status_code == 401
