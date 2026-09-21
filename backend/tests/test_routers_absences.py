"""Tests d'intégration du router Absences via TestClient.

Couverture : CRUD complet, justification, alertes absences, filtrage,
élève introuvable.
"""
import pytest
from datetime import date

import models


def _creer_tuteur(client, auth_headers):
    return client.post("/api/tuteurs/", json={
        "nom": "T", "prenom": "T", "email": "t@ex.com",
        "telephone": "+22376000000", "adresse": "Bamako", "profession": "M",
    }, headers=auth_headers)


def _creer_eleve(db_session, tuteur_id, nom="Konaté", prenom="Amadou"):
    """Crée un élève directement en base, sans classe ni inscription.

    La création via l'API exige désormais une classe → pour tester les
    absences, on insère l'élève à la main (les absences n'ont pas besoin
    d'une classe ni d'une inscription).
    """
    eleve = models.Eleves(
        nom=nom, prenom=prenom,
        date_de_naissance=date(2012, 3, 15),
        lieu_de_naissance="Bamako", sexe="M",
        tuteur_id=tuteur_id,
    )
    db_session.add(eleve)
    db_session.commit()
    db_session.refresh(eleve)
    return eleve


class TestCreation:
    def test_creer_absence(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        resp = client.post("/api/absences/", json={
            "matricule_eleve": eleve.matricule,
            "date_absence": "2025-10-15",
        }, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["matricule_eleve"] == eleve.matricule
        assert body["justifiee"] is False

    def test_eleve_introuvable_404(self, client, auth_headers):
        resp = client.post("/api/absences/", json={
            "matricule_eleve": "AU9900000",
            "date_absence": "2025-10-15",
        }, headers=auth_headers)
        assert resp.status_code == 404


class TestLecture:
    def test_liste(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        client.post("/api/absences/", json={
            "matricule_eleve": eleve.matricule, "date_absence": "2025-10-15",
        }, headers=auth_headers)
        resp = client.get("/api/absences/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_filtre_par_matricule(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        e1 = _creer_eleve(db_session, t["id"])
        e2 = _creer_eleve(db_session, t["id"], nom="Traoré", prenom="Fatoumata")
        client.post("/api/absences/", json={
            "matricule_eleve": e1.matricule, "date_absence": "2025-10-15",
        }, headers=auth_headers)
        client.post("/api/absences/", json={
            "matricule_eleve": e2.matricule, "date_absence": "2025-10-16",
        }, headers=auth_headers)
        resp = client.get(f"/api/absences/?matricule_eleve={e1.matricule}", headers=auth_headers)
        assert len(resp.json()) == 1

    def test_compte(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        client.post("/api/absences/", json={
            "matricule_eleve": eleve.matricule, "date_absence": "2025-10-15",
        }, headers=auth_headers)
        resp = client.get("/api/absences/compte", headers=auth_headers)
        assert resp.json()["total"] == 1


class TestJustification:
    def test_justifier_absence(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        absence = client.post("/api/absences/", json={
            "matricule_eleve": eleve.matricule, "date_absence": "2025-10-15",
        }, headers=auth_headers).json()
        resp = client.patch(f"/api/absences/{absence['id']}/justifier", json={
            "justifiee": True, "motif": "Raison médicale",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["justifiee"] is True
        assert resp.json()["motif"] == "Raison médicale"


class TestAlertes:
    def test_alertes_absences(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        for i in range(4):
            client.post("/api/absences/", json={
                "matricule_eleve": eleve.matricule,
                "date_absence": f"2025-10-{15+i}",
            }, headers=auth_headers)
        resp = client.get("/api/absences/alertes?seuil=3", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
        assert resp.json()[0]["nb_absences_non_justifiees"] == 4


class TestModification:
    def test_modifier_absence(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        absence = client.post("/api/absences/", json={
            "matricule_eleve": eleve.matricule, "date_absence": "2025-10-15",
        }, headers=auth_headers).json()
        resp = client.put(f"/api/absences/{absence['id']}", json={
            "matricule_eleve": eleve.matricule,
            "date_absence": "2025-10-20",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["date_absence"] == "2025-10-20"


class TestSuppression:
    def test_supprimer_absence(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        absence = client.post("/api/absences/", json={
            "matricule_eleve": eleve.matricule, "date_absence": "2025-10-15",
        }, headers=auth_headers).json()
        resp = client.delete(f"/api/absences/{absence['id']}", headers=auth_headers)
        assert resp.status_code == 204


class TestFiltreClasseParAnnee:
    def test_filtre_classe_par_inscription_annee(self, client, auth_headers, db_session):
        """Filtre par classe : s'appuie sur l'inscription de l'année scolaire qui
        couvre la date d'absence, jamais sur Eleves.classe_id (classe actuelle).

        Un élève passé en classe B retrouve ses absences d'ancienne année sous
        sa classe d'alors (A), pas sous sa classe actuelle.
        """
        annee1 = models.AnneesScolaires(
            libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
        )
        annee2 = models.AnneesScolaires(
            libelle="2026-2027", date_debut=date(2026, 9, 1), date_fin=date(2027, 6, 30)
        )
        db_session.add_all([annee1, annee2])
        db_session.flush()
        classe_a = models.Classes(niveau="7ème Année", nom="A")
        classe_b = models.Classes(niveau="7ème Année", nom="B")
        db_session.add_all([classe_a, classe_b])
        db_session.flush()

        t = _creer_tuteur(client, auth_headers).json()
        eleve = models.Eleves(
            nom="Konaté", prenom="Amadou",
            date_de_naissance=date(2012, 3, 15),
            lieu_de_naissance="Bamako", sexe="M",
            tuteur_id=t["id"], classe_id=classe_b.id,  # classe ACTUELLE = B
        )
        db_session.add(eleve)
        db_session.flush()
        db_session.add_all([
            models.Inscriptions(matricule_eleve=eleve.matricule, id_classe=classe_a.id,
                                id_annee_scolaire=annee1.id, statut="Inscrit"),
            models.Inscriptions(matricule_eleve=eleve.matricule, id_classe=classe_b.id,
                                id_annee_scolaire=annee2.id, statut="Inscrit"),
        ])
        db_session.commit()

        # Absence pendant l'année 1 (2025-2026), alors qu'il était en classe A.
        client.post("/api/absences/", json={
            "matricule_eleve": eleve.matricule, "date_absence": "2026-03-15",
        }, headers=auth_headers)

        resp_a = client.get(f"/api/absences/?classe_id={classe_a.id}", headers=auth_headers)
        assert resp_a.status_code == 200
        assert len(resp_a.json()) == 1
        assert resp_a.json()[0]["matricule_eleve"] == eleve.matricule

        resp_b = client.get(f"/api/absences/?classe_id={classe_b.id}", headers=auth_headers)
        assert resp_b.json() == []


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/absences/")
        assert resp.status_code == 401