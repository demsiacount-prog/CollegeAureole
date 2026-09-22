"""Tests d'intégration du router Résultats de passage via TestClient.

Couverture : consultation résultats par classe, calcul automatique,
modification manuelle du statut, année active requise.
"""
import pytest
from datetime import date

import models


def _creer_tuteur(client, auth_headers):
    return client.post("/api/tuteurs/", json={
        "nom": "T", "prenom": "T", "email": "t@ex.com",
        "telephone": "+22376000000", "adresse": "Bamako", "profession": "M",
    }, headers=auth_headers)


def _creer_classe(client, auth_headers, niveau="7ème Année", nom="A"):
    return client.post("/api/classes/", json={"niveau": niveau, "nom": nom}, headers=auth_headers)


def _creer_annee(client, auth_headers):
    return client.post("/api/anneesScolaires/", json={
        "libelle": "2025-2026", "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers)


def _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur_id, classe_id, annee_id, prenom="Amadou"):
    """Crée un élève directement en base SANS classe (la création API
    générerait une inscription auto) puis crée explicitement l'inscription."""
    eleve = models.Eleves(
        nom="Konaté", prenom=prenom,
        date_de_naissance=date(2012, 3, 15),
        lieu_de_naissance="Bamako", sexe="M",
        tuteur_id=tuteur_id,
    )
    db_session.add(eleve)
    db_session.commit()
    db_session.refresh(eleve)
    insc = client.post("/api/inscriptions/", json={
        "matricule_eleve": eleve.matricule,
        "id_classe": classe_id,
        "id_annee_scolaire": annee_id,
    }, headers=auth_headers)
    return eleve, insc.json() if insc.status_code == 201 else None


class TestResultatsClasse:
    def test_classe_sans_eleves(self, client, auth_headers):
        """Retourne 200 avec effectif=0 quand la classe n'a pas d'inscriptions."""
        cl = _creer_classe(client, auth_headers).json()
        _creer_annee(client, auth_headers)
        resp = client.get(f"/api/resultats/{cl['id']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["effectif"] == 0

    def test_avec_eleves(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, t["id"], cl["id"], annee["id"])
        resp = client.get(f"/api/resultats/{cl['id']}", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["effectif"] == 1
        assert body["classe"]["id"] == cl["id"]

    def test_annee_active_peut_decider(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, t["id"], cl["id"], annee["id"])
        body = client.get(f"/api/resultats/{cl['id']}", headers=auth_headers).json()
        assert body["peut_decider"] is True
        assert body["annee_cloturee"] is False

    def test_annee_cloturee_peut_decider_false(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, t["id"], cl["id"], annee["id"])
        db_session.query(models.AnneesScolaires).filter(
            models.AnneesScolaires.id == annee["id"]
        ).update({models.AnneesScolaires.cloturee: True})
        db_session.commit()
        body = client.get(f"/api/resultats/{cl['id']}?annee_id={annee['id']}", headers=auth_headers).json()
        assert body["peut_decider"] is False
        assert body["annee_cloturee"] is True

    def test_classe_introuvable_404(self, client, auth_headers):
        _creer_annee(client, auth_headers)
        resp = client.get("/api/resultats/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestCalculAutomatique:
    def test_sans_notes_en_attente(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, t["id"], cl["id"], annee["id"])
        resp = client.post(f"/api/resultats/{cl['id']}/calcul-auto", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["en_attente"] == 1
        assert body["admis"] == 0

    def test_classe_introuvable_404(self, client, auth_headers):
        _creer_annee(client, auth_headers)
        resp = client.post("/api/resultats/99999/calcul-auto", headers=auth_headers)
        assert resp.status_code == 404

    def test_sans_annee_active_404(self, client, auth_headers):
        cl = _creer_classe(client, auth_headers).json()
        resp = client.post(f"/api/resultats/{cl['id']}/calcul-auto", headers=auth_headers)
        assert resp.status_code == 404

    def test_jardin_non_reconnu_400(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers, niveau="Petite Section").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, t["id"], cl["id"], annee["id"])
        resp = client.post(f"/api/resultats/{cl['id']}/calcul-auto", headers=auth_headers)
        assert resp.status_code == 400


class TestModificationStatut:
    def test_modifier_statut_passage(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        _, insc = _creer_eleve_et_inscription(db_session, client, auth_headers, t["id"], cl["id"], annee["id"])
        resp = client.put(f"/api/resultats/statut/{insc['id']}", json={
            "statut": "ADMIS",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["statut_passage"] == "ADMIS"
        assert resp.json()["diplome"] is False  # 7ème : pas fin de cycle

    def test_admis_fin_cycle_est_diplome(self, client, auth_headers, db_session):
        """Bug 8 : un ADMIS en fin de cycle (9ème) est automatiquement diplômé."""
        annee = _creer_annee(client, auth_headers).json()
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers, niveau="9ème Année", nom="A").json()
        _, insc = _creer_eleve_et_inscription(db_session, client, auth_headers, t["id"], cl["id"], annee["id"])
        admis = client.put(f"/api/resultats/statut/{insc['id']}", json={"statut": "ADMIS"}, headers=auth_headers)
        assert admis.status_code == 200
        assert admis.json()["diplome"] is True

        recale = client.put(f"/api/resultats/statut/{insc['id']}", json={"statut": "RECALE"}, headers=auth_headers)
        assert recale.status_code == 200
        assert recale.json()["statut_passage"] == "RECALE"
        assert recale.json()["diplome"] is False

    def test_inscription_introuvable_404(self, client, auth_headers):
        resp = client.put("/api/resultats/statut/99999", json={"statut": "ADMIS"}, headers=auth_headers)
        assert resp.status_code == 404


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/resultats/1")
        assert resp.status_code == 401
