"""Tests d'intégration du router Séances via TestClient.

Couverture : CRUD complet, détection de conflits (classe, enseignant, salle),
capacité salle, filtrage par année/classe/enseignant.
"""
import pytest
from datetime import date, time

import models


def _creer_base(client, auth_headers):
    """Crée la base complète (année, classe, enseignant, cours, salle)."""
    annee = client.post("/api/anneesScolaires/", json={
        "libelle": "2025-2026", "date_debut": "2025-09-01", "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers).json()
    classe = client.post("/api/classes/", json={
        "niveau": "7ème Année", "nom": "A",
    }, headers=auth_headers).json()
    ens = client.post("/api/enseignants/", json={
        "nom": "E", "prenom": "E", "email": "ens@ex.com",
        "telephone": "+22376000000", "adresse": "Bamako", "specialite": "X",
    }, headers=auth_headers).json()
    cours = client.post("/api/cours/", json={
        "nom": "Mathématiques", "description": "Algèbre",
        "volume_horaire": 4, "matricule_enseignant": ens["matricule"],
        "affectations": [{"id_classe": classe["id"], "coefficient": 1.0}],
    }, headers=auth_headers).json()
    salle = client.post("/api/salles/", json={"nom": "A101", "capacite": 40}, headers=auth_headers).json()
    return {"annee": annee, "classe": classe, "enseignant": ens, "cours": cours, "salle": salle}


class TestCreation:
    def test_creer_seance(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        resp = client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "id_salle": base["salle"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["jour_semaine"] == "Lundi"

    def test_conflit_meme_classe_409(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        payload = {
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }
        client.post("/api/seances/", json=payload, headers=auth_headers)
        resp = client.post("/api/seances/", json=payload, headers=auth_headers)
        assert resp.status_code == 409

    def test_conflit_enseignant_409(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        classe2 = client.post("/api/classes/", json={
            "niveau": "7ème Année", "nom": "B",
        }, headers=auth_headers).json()
        # Créer une 2e affectation du cours à classe B
        client.put(f"/api/cours/{base['cours']['id']}", json={
            "nom": "Mathématiques", "description": "Algèbre",
            "volume_horaire": 4, "matricule_enseignant": base["enseignant"]["matricule"],
            "affectations": [
                {"id_classe": base["classe"]["id"], "coefficient": 1.0},
                {"id_classe": classe2["id"], "coefficient": 1.0},
            ],
        }, headers=auth_headers)
        payload1 = {
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Mardi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }
        client.post("/api/seances/", json=payload1, headers=auth_headers)
        payload2 = {
            "id_cours": base["cours"]["id"],
            "id_classe": classe2["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Mardi",
            "heure_debut": "09:00",
            "heure_fin": "11:00",
        }
        resp = client.post("/api/seances/", json=payload2, headers=auth_headers)
        assert resp.status_code == 409

    def test_cours_introuvable_404(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        resp = client.post("/api/seances/", json={
            "id_cours": 99999,
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers)
        assert resp.status_code == 404


class TestLecture:
    def test_liste(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers)
        resp = client.get(f"/api/seances/?id_annee_scolaire={base['annee']['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_seances_classe(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers)
        resp = client.get(
            f"/api/seances/classe/{base['classe']['id']}?id_annee_scolaire={base['annee']['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_seances_enseignant(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers)
        resp = client.get(
            f"/api/seances/enseignant/{base['enseignant']['matricule']}?id_annee_scolaire={base['annee']['id']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1


class TestModification:
    def test_modifier_seance(self, client, auth_headers):
        """Un PUT ne doit plus échouer (SeanceUpdate ne porte pas d'année) : les
        conflits et la capacité sont vérifiés sur l'année de la séance existante."""
        base = _creer_base(client, auth_headers)
        created = client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "id_salle": base["salle"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers).json()
        resp = client.put(f"/api/seances/{created['id']}", json={
            "jour_semaine": "Mardi",
            "heure_debut": "09:00",
            "heure_fin": "11:00",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["jour_semaine"] == "Mardi"
        assert resp.json()["heure_debut"] == "09:00:00"

    def test_modifier_seance_conflit_409(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        payload = {
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }
        a = client.post("/api/seances/", json=payload, headers=auth_headers).json()
        b = client.post("/api/seances/", json={**payload, "jour_semaine": "Mardi"}, headers=auth_headers).json()
        resp = client.put(f"/api/seances/{b['id']}", json={"jour_semaine": "Lundi"}, headers=auth_headers)
        assert resp.status_code == 409

    def test_modifier_seance_heures_inversees_422(self, client, auth_headers):
        """À la modification aussi, heure_fin > heure_debut doit être vérifié
        (même validation qu'à la création), pas seulement à la création."""
        base = _creer_base(client, auth_headers)
        created = client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers).json()
        resp = client.put(f"/api/seances/{created['id']}", json={
            "heure_debut": "10:00",
            "heure_fin": "08:00",
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_modifier_seance_une_bonne_heure_seule_ok(self, client, auth_headers):
        """Un update partiel qui ne fournit qu'une seule borne ne doit pas être
        rejeté : la validation n'est appliquée qu'aux champs fournis."""
        base = _creer_base(client, auth_headers)
        created = client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers).json()
        resp = client.put(f"/api/seances/{created['id']}", json={"heure_debut": "09:00"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["heure_debut"] == "09:00:00"
        assert resp.json()["heure_fin"] == "10:00:00"


class TestCapacite:
    def test_capacite_selon_inscriptions_de_l_annee(self, client, auth_headers, db_session):
        """La capacité est vérifiée sur l'effectif de l'ANNÉE de la séance via
        les inscriptions — pas Eleves.classe_id (effectif d'une autre année)."""
        base = _creer_base(client, auth_headers)
        salle_petite = client.post("/api/salles/", json={
            "nom": "B202", "capacite": 1,
        }, headers=auth_headers).json()

        t = client.post("/api/tuteurs/", json={
            "nom": "T", "prenom": "T", "email": "seance@ex.com",
            "telephone": "+22376000000", "adresse": "Bamako", "profession": "M",
        }, headers=auth_headers).json()
        for i in range(2):
            eleve = models.Eleves(
                nom=f"E{i}", prenom="P", date_de_naissance=date(2012 + i, 3, 15),
                lieu_de_naissance="Bamako", sexe="M", statut="actif",
                tuteur_id=t["id"], classe_id=base["classe"]["id"],
            )
            db_session.add(eleve)
            db_session.flush()
            db_session.add(models.Inscriptions(
                matricule_eleve=eleve.matricule, id_classe=base["classe"]["id"],
                id_annee_scolaire=base["annee"]["id"], statut="Inscrit",
            ))
        db_session.commit()

        resp = client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "id_salle": salle_petite["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Capacité insuffisante"


class TestSuppression:
    def test_supprimer_seance(self, client, auth_headers):
        base = _creer_base(client, auth_headers)
        created = client.post("/api/seances/", json={
            "id_cours": base["cours"]["id"],
            "id_classe": base["classe"]["id"],
            "id_annee_scolaire": base["annee"]["id"],
            "jour_semaine": "Lundi",
            "heure_debut": "08:00",
            "heure_fin": "10:00",
        }, headers=auth_headers).json()
        resp = client.delete(f"/api/seances/{created['id']}", headers=auth_headers)
        assert resp.status_code == 204


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/seances/")
        assert resp.status_code == 401
