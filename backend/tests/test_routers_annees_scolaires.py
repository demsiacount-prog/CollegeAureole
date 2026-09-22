"""Tests d'intégration du router Années Scolaires via TestClient.

Couverture : CRUD, activation, clôture, trimestres auto-générés,
duplication refusée, protection suppression.
"""
import pytest


def _creer_annee(client, auth_headers, **overrides):
    data = {
        "libelle": "2025-2026",
        "date_debut": "2025-09-01",
        "date_fin": "2026-06-30",
        "active": False,
        **overrides,
    }
    return client.post("/api/anneesScolaires/", json=data, headers=auth_headers)


class TestCreation:
    def test_creer_annee(self, client, auth_headers):
        resp = _creer_annee(client, auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["libelle"] == "2025-2026"
        assert body["active"] is False
        assert body["cloturee"] is False

    def test_creer_annee_active(self, client, auth_headers):
        resp = _creer_annee(client, auth_headers, active=True)
        assert resp.status_code == 201
        assert resp.json()["active"] is True

    def test_doublon_libelle_400(self, client, auth_headers):
        _creer_annee(client, auth_headers)
        resp = _creer_annee(client, auth_headers)
        assert resp.status_code == 400

    def test_dates_inverses_refusee(self, client, auth_headers):
        resp = _creer_annee(client, auth_headers, date_debut="2026-06-30", date_fin="2025-09-01")
        assert resp.status_code >= 400

    def test_trimestres_auto_generes(self, client, auth_headers):
        """La création génère les périodes par défaut (trimestres + compositions)."""
        resp = _creer_annee(client, auth_headers)
        annee = resp.json()
        detail = client.get(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers)
        assert detail.status_code == 200
        body = detail.json()
        assert len(body["trimestres"]) > 0

    def test_compositions_auto_generees_nommees_par_mois(self, client, auth_headers):
        """Les compositions portent le nom de leur mois, sans doublon."""
        resp = _creer_annee(client, auth_headers)
        annee = resp.json()
        detail = client.get(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers)
        assert detail.status_code == 200
        compos = [t for t in detail.json()["trimestres"] if t["type"] == "COMPOSITION"]
        assert len(compos) == 9
        noms = [t["nom"] for t in compos]
        assert all(nom.startswith("Composition ") for nom in noms)
        assert all(nom != "Composition 1" for nom in noms)
        assert len(set(noms)) == len(noms)


class TestLecture:
    def test_liste(self, client, auth_headers):
        _creer_annee(client, auth_headers)
        resp = client.get("/api/anneesScolaires/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_annee_active(self, client, auth_headers):
        _creer_annee(client, auth_headers, active=True)
        resp = client.get("/api/anneesScolaires/active", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["active"] is True

    def test_aucune_annee_active_404(self, client, auth_headers):
        resp = client.get("/api/anneesScolaires/active", headers=auth_headers)
        assert resp.status_code == 404


class TestActivation:
    def test_activer_annee_desactive_autres(self, client, auth_headers):
        a1 = _creer_annee(client, auth_headers, libelle="2024-2025", active=True).json()
        a2 = _creer_annee(client, auth_headers, libelle="2025-2026", active=False).json()
        resp = client.put(f"/api/anneesScolaires/{a2['id']}/activer", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["active"] is True
        detail = client.get(f"/api/anneesScolaires/{a1['id']}", headers=auth_headers)
        assert detail.json()["active"] is False

    def test_activer_annee_cloturee_refuse(self, client, auth_headers):
        """Une année clôturée ne peut plus être (ré)activée : plus de consultation d'une année archivée."""
        annee = _creer_annee(client, auth_headers, active=False).json()
        client.put(f"/api/anneesScolaires/{annee['id']}/cloturer", headers=auth_headers)
        resp = client.put(f"/api/anneesScolaires/{annee['id']}/activer", headers=auth_headers)
        assert resp.status_code == 409


class TestCloture:
    def test_cloturer_annee_inactive(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers, active=False).json()
        resp = client.put(f"/api/anneesScolaires/{annee['id']}/cloturer", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["cloturee"] is True

    def test_cloturer_annee_active_400(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers, active=True).json()
        resp = client.put(f"/api/anneesScolaires/{annee['id']}/cloturer", headers=auth_headers)
        assert resp.status_code == 400


class TestModification:
    def test_modifier_annee(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers).json()
        resp = client.put(
            f"/api/anneesScolaires/{annee['id']}",
            json={"libelle": "2026-2027", "date_debut": "2026-09-01", "date_fin": "2027-06-30"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["libelle"] == "2026-2027"

    def test_modifier_annee_sans_active_conserve_letat(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers, active=True).json()
        resp = client.put(
            f"/api/anneesScolaires/{annee['id']}",
            json={"libelle": "2025-2026 bis", "date_debut": "2025-09-01", "date_fin": "2026-06-30"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["active"] is True

    def test_modifier_annee_cloturee_409(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers, active=False).json()
        client.put(f"/api/anneesScolaires/{annee['id']}/cloturer", headers=auth_headers)
        resp = client.put(
            f"/api/anneesScolaires/{annee['id']}",
            json={"libelle": "X", "date_debut": "2025-09-01", "date_fin": "2026-06-30"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_activation_via_put_desactive_les_autres(self, client, auth_headers):
        a1 = _creer_annee(
            client, auth_headers,
            libelle="2024-2025", date_debut="2024-09-01", date_fin="2025-06-30", active=True,
        ).json()
        a2 = _creer_annee(client, auth_headers, libelle="2025-2026", active=False).json()
        resp = client.put(
            f"/api/anneesScolaires/{a2['id']}",
            json={"libelle": "2025-2026", "date_debut": "2025-09-01", "date_fin": "2026-06-30", "active": True},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["active"] is True
        detail = client.get(f"/api/anneesScolaires/{a1['id']}", headers=auth_headers)
        assert detail.json()["active"] is False

    def test_impossible_desactiver_lannee_active_via_put(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers, active=True).json()
        resp = client.put(
            f"/api/anneesScolaires/{annee['id']}",
            json={"libelle": "2025-2026", "date_debut": "2025-09-01", "date_fin": "2026-06-30", "active": False},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    def test_chevauchement_de_periode_409(self, client, auth_headers):
        _creer_annee(client, auth_headers, libelle="2025-2026", active=False).json()
        autre = _creer_annee(client, auth_headers, libelle="2026-2027", active=False).json()
        resp = client.put(
            f"/api/anneesScolaires/{autre['id']}",
            json={"libelle": "2024-2025", "date_debut": "2025-11-01", "date_fin": "2027-06-30", "active": False},
            headers=auth_headers,
        )
        assert resp.status_code == 409
        assert "chevauch" in resp.json()["detail"].lower()


class TestSuppression:
    def test_supprimer_annee_vide_avec_trimestres_204(self, client, auth_headers):
        """Une année sans donnée métier se supprime : ses trimestres
        auto-générés sont emportés par la cascade contrôlée."""
        annee = _creer_annee(client, auth_headers).json()
        resp = client.delete(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers)
        assert resp.status_code == 204
        assert client.get(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers).status_code == 404

    def test_supprimer_annee_avec_trimestres_manuels_204(self, client, auth_headers):
        """Des trimestres (même ajoutés à la main) ne bloquent pas la suppression."""
        from models.trimestres import Trimestres

        annee = _creer_annee(client, auth_headers).json()
        resp = client.delete(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_supprimer_annee_avec_inscription_409_detail(self, client, auth_headers, db_session):
        """Une année portant une inscription ne se supprime pas : 409 détaillé."""
        from datetime import date
        import models

        annee = _creer_annee(client, auth_headers).json()

        tuteur = models.Tuteurs(
            nom="T", prenom="T", email="t@t.ml",
            telephone="+22376000000", adresse="Bamako", profession="M",
        )
        db_session.add(tuteur)
        db_session.flush()
        eleve = models.Eleves(
            nom="Konaté", prenom="Amadou",
            date_de_naissance=date(2012, 3, 15),
            lieu_de_naissance="Bamako", sexe="M",
            tuteur_id=tuteur.id,
        )
        db_session.add(eleve)
        db_session.flush()
        db_session.add(models.Inscriptions(
            matricule_eleve=eleve.matricule,
            id_annee_scolaire=annee["id"],
        ))
        db_session.commit()

        resp = client.delete(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers)
        assert resp.status_code == 409
        assert "inscription" in resp.json()["detail"].lower()
        # L'année et l'inscription sont intactes après le refus.
        assert client.get(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers).status_code == 200
        assert db_session.query(models.Inscriptions).count() == 1


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/anneesScolaires/")
        assert resp.status_code == 401
