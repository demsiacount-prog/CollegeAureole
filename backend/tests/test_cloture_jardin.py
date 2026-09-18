"""Tests de la règle maternelle lors de la clôture d'année.

Règle : chaque année, les élèves du jardin d'enfants passent automatiquement à
la section supérieure (Petite → Moyenne → Grande → 1ère Année) sans décision de
conseil. Ils ne doivent donc plus bloquer la clôture (EN_ATTENTE).
"""
import pytest
from datetime import date

import models


def _creer_tuteur(client, auth_headers):
    return client.post("/api/tuteurs/", json={
        "nom": "T", "prenom": "T", "email": "t@ex.com",
        "telephone": "+22376000000", "adresse": "Bamako", "profession": "M",
    }, headers=auth_headers)


def _creer_classe(client, auth_headers, niveau="Petite Section", nom="A"):
    return client.post("/api/classes/", json={"niveau": niveau, "nom": nom}, headers=auth_headers)


def _creer_annee(client, auth_headers, libelle="2025-2026"):
    return client.post("/api/anneesScolaires/", json={
        "libelle": libelle, "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers)


def _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur_id, classe_id, annee_id,
                                prenom="Amadou", nom="Konaté"):
    """Élève créé directement en base puis inscription via l'API."""
    eleve = models.Eleves(
        nom=nom, prenom=prenom,
        date_de_naissance=date(2018, 3, 15),
        lieu_de_naissance="Bamako", sexe="M",
        tuteur_id=tuteur_id,
    )
    db_session.add(eleve)
    db_session.commit()
    db_session.refresh(eleve)
    resp = client.post("/api/inscriptions/", json={
        "matricule_eleve": eleve.matricule,
        "id_classe": classe_id,
        "id_annee_scolaire": annee_id,
    }, headers=auth_headers)
    return eleve, resp.json()["id"]


class TestClasseSuivanteJardin:
    def test_progression_petite_a_moyenne(self, db_session):
        ps = models.Classes(niveau="Petite Section", nom="A")
        ms = models.Classes(niveau="Moyenne Section", nom="A")
        db_session.add_all([ps, ms])
        db_session.commit()
        from routers.cloture import _classe_suivante
        assert _classe_suivante(db_session, ps) is ms

    def test_progression_moyenne_a_grande(self, db_session):
        ms = models.Classes(niveau="Moyenne Section", nom="A")
        gs = models.Classes(niveau="Grande Section", nom="A")
        db_session.add_all([ms, gs])
        db_session.commit()
        from routers.cloture import _classe_suivante
        assert _classe_suivante(db_session, ms) is gs

    def test_progression_grande_a_premiere_annee(self, db_session):
        gs = models.Classes(niveau="Grande Section", nom="A")
        pa = models.Classes(niveau="1ère Année", nom="A")
        db_session.add_all([gs, pa])
        db_session.commit()
        from routers.cloture import _classe_suivante
        assert _classe_suivante(db_session, gs) is pa

    def test_sans_classe_suivante_renvoie_none(self, db_session):
        gs = models.Classes(niveau="Grande Section", nom="A")
        db_session.add(gs)
        db_session.commit()
        from routers.cloture import _classe_suivante
        assert _classe_suivante(db_session, gs) is None


class TestPreviewJardin:
    def test_jardin_ne_bloque_pas_la_preview(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section").json()
        ms = _creer_classe(client, auth_headers, niveau="Moyenne Section").json()
        _creer_classe(client, auth_headers, niveau="Grande Section").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"], prenom="Awa")
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ms["id"], annee["id"], prenom="Binta")

        resp = client.get("/api/cloture/preview", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["blocants"] == 0
        assert body["peut_executer"] is True
        assert body["compteurs"]["ADMIS_PASSAGE"] == 2
        assert body["compteurs"]["EN_ATTENTE"] == 0
        for eleve in body["eleves"]:
            assert eleve["statut_passage"] == "ADMIS"
            assert eleve["action_prevue"].startswith("Admis – passage en ")

    def test_action_prevue_indique_la_section_cible(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section", nom="Soleil").json()
        ms = _creer_classe(client, auth_headers, niveau="Moyenne Section", nom="Soleil").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"], prenom="Awa")

        resp = client.get("/api/cloture/preview", headers=auth_headers)
        body = resp.json()
        assert body["eleves"][0]["action_prevue"] == "Admis – passage en Moyenne Section Soleil"
        assert ms["id"] is not None

    def test_eleve_fondamental_en_attente_bloque_toujours(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section", nom="A").json()
        sept = _creer_classe(client, auth_headers, niveau="7ème Année", nom="B").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"], prenom="Awa")
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], sept["id"], annee["id"], prenom="Moussa")

        resp = client.get("/api/cloture/preview", headers=auth_headers)
        body = resp.json()
        assert body["blocants"] == 1
        assert body["peut_executer"] is False
        assert body["compteurs"]["ADMIS_PASSAGE"] == 1
        assert body["compteurs"]["EN_ATTENTE"] == 1


class TestExecutionJardin:
    def test_promotion_automatique_vers_sections_superieures(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section", nom="A").json()
        ms = _creer_classe(client, auth_headers, niveau="Moyenne Section", nom="A").json()
        gs = _creer_classe(client, auth_headers, niveau="Grande Section", nom="A").json()
        pa = _creer_classe(client, auth_headers, niveau="1ère Année", nom="A").json()
        eleve_ps, _ = _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"], prenom="Fatou")
        eleve_ms, _ = _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ms["id"], annee["id"], prenom="Ibrahima")
        eleve_gs, _ = _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], gs["id"], annee["id"], prenom="Seydou")

        resp = client.post("/api/cloture/executer", json={
            "nouvelle_annee": {"libelle": "2026-2027", "date_debut": "2026-09-01", "date_fin": "2027-06-30"},
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["rapport"]["admis_passage"] == 3
        assert body["rapport"]["recale_redoublement"] == 0

        nouvelles = db_session.query(models.Inscriptions).filter(
            models.Inscriptions.id_annee_scolaire == body["nouvelle_annee"]["id"]
        ).all()
        par_eleve = {i.matricule_eleve: i for i in nouvelles}
        assert par_eleve[eleve_ps.matricule].id_classe == ms["id"]
        assert par_eleve[eleve_ms.matricule].id_classe == gs["id"]
        assert par_eleve[eleve_gs.matricule].id_classe == pa["id"]
        for i in nouvelles:
            assert i.statut == "Inscrit"

    def test_ancienne_annee_cloturee(self, client, auth_headers, db_session):
        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section", nom="A").json()
        ms = _creer_classe(client, auth_headers, niveau="Moyenne Section", nom="A").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"], prenom="Fatou")

        resp = client.post("/api/cloture/executer", json={
            "nouvelle_annee": {"libelle": "2026-2027", "date_debut": "2026-09-01", "date_fin": "2027-06-30"},
        }, headers=auth_headers)
        assert resp.status_code == 200
        db_session.expire_all()
        old = db_session.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee["id"]).first()
        assert old.active is False
        assert old.cloturee is True

    def test_executer_refuse_si_annee_active_deja_cloturee(self, client, auth_headers, db_session):
        """Une année clôturée ré-##activée pour consultation ne peut pas être clôturée à nouveau."""
        annee = _creer_annee(client, auth_headers).json()
        tuteur = _creer_tuteur(client, auth_headers).json()
        ps = _creer_classe(client, auth_headers, niveau="Petite Section", nom="A").json()
        _creer_eleve_et_inscription(db_session, client, auth_headers, tuteur["id"], ps["id"], annee["id"], prenom="Fatou")

        resp = client.post("/api/cloture/executer", json={
            "nouvelle_annee": {"libelle": "2026-2027", "date_debut": "2026-09-01", "date_fin": "2027-06-30"},
        }, headers=auth_headers)
        assert resp.status_code == 200
        db_session.expire_all()
        old = db_session.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee["id"]).first()
        old.active = True  # revisite de l'année clôturée (mode lecture seule)
        db_session.commit()

        resp = client.post("/api/cloture/executer", json={
            "nouvelle_annee": {"libelle": "2027-2028", "date_debut": "2027-09-01", "date_fin": "2028-06-30"},
        }, headers=auth_headers)
        assert resp.status_code == 409

        preview = client.get("/api/cloture/preview", headers=auth_headers)
        assert preview.status_code == 200
        assert preview.json()["peut_executer"] is False
        assert preview.json()["cloturee"] is True