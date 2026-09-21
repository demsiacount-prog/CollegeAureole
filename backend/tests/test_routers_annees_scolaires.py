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

    def test_modifier_annee_cloturee_409(self, client, auth_headers):
        annee = _creer_annee(client, auth_headers, active=False).json()
        client.put(f"/api/anneesScolaires/{annee['id']}/cloturer", headers=auth_headers)
        resp = client.put(
            f"/api/anneesScolaires/{annee['id']}",
            json={"libelle": "X", "date_debut": "2025-09-01", "date_fin": "2026-06-30"},
            headers=auth_headers,
        )
        assert resp.status_code == 409


class TestSuppression:
    def test_supprimer_annee_sans_trimestres(self, client, auth_headers, db_session):
        """On ne peut pas supprimer une année qui a des trimestres
        (auto-générés à la création). On enlève d'abord les trimestres."""
        from models.trimestres import Trimestres

        annee = _creer_annee(client, auth_headers).json()
        # Supprimer les trimestres auto-générés directement en DB
        db_session.query(Trimestres).filter(
            Trimestres.annee_scolaire_id == annee["id"]
        ).delete()
        db_session.commit()
        resp = client.delete(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers)
        assert resp.status_code == 204

    def test_supprimer_annee_avec_trimestres_409(self, client, auth_headers):
        """On ne peut PAS supprimer une année qui a des trimestres."""
        annee = _creer_annee(client, auth_headers).json()
        resp = client.delete(f"/api/anneesScolaires/{annee['id']}", headers=auth_headers)
        assert resp.status_code == 409


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/anneesScolaires/")
        assert resp.status_code == 401
