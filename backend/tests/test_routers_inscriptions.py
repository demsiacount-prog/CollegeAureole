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

    def test_dossier_complet_persiste_infos_parents(self, client, auth_headers):
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        resp = client.post("/api/inscriptions/dossier-complet", json={
            "tuteur": {
                "nom": "Nouveau", "prenom": "Tuteur",
                "email": "parents@ex.com",
                "telephone": "+22376000002",
                "adresse": "Bamako", "profession": "M",
            },
            "eleve": {
                "nom": "Élève", "prenom": "Nouveau",
                "date_de_naissance": "2012-01-01",
                "lieu_de_naissance": "Bamako", "sexe": "M",
                "nom_pere": "Père",
                "prenom_pere": "Jean",
                "fonction_pere": "Commerçant",
                "nom_mere": "Mère",
                "prenom_mere": "Marie",
                "fonction_mere": "Ménagère",
            },
            "classe_id": cl["id"],
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201
        matricule = resp.json()["matricule_eleve"]
        eleve = client.get(f"/api/eleves/{matricule}", headers=auth_headers).json()
        assert eleve["nom_pere"] == "Père"
        assert eleve["prenom_pere"] == "Jean"
        assert eleve["fonction_pere"] == "Commerçant"
        assert eleve["nom_mere"] == "Mère"
        assert eleve["prenom_mere"] == "Marie"
        assert eleve["fonction_mere"] == "Ménagère"

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


class TestChangementClasse:
    def test_changement_classe_maj_echeances_et_montant_total(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl_a = _creer_classe(client, auth_headers, frais=50000, mensualite=10000).json()
        cl_b = _creer_classe(client, auth_headers, frais=20000, mensualite=5000).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        insc = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl_a["id"], "id_annee_scolaire": annee["id"],
            "date_inscription": "2025-10-01",
        }, headers=auth_headers).json()
        assert insc["montant_total"] == 50000 + 9 * 10000

        resp = client.put(f"/api/inscriptions/{insc['id']}", json={"id_classe": cl_b["id"]}, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        # montant_total = somme des montant_du : frais 20000 + 9 × mensualité 5000
        assert resp.json()["montant_total"] == 20000 + 9 * 5000

        echeances = client.get(f"/api/paiements/echeances/{insc['id']}", headers=auth_headers).json()
        assert len(echeances) == 10
        for ech in echeances:
            assert ech["id_classe"] == cl_b["id"]
        inscription_ech = next(e for e in echeances if e["type_echeance"] == "INSCRIPTION")
        assert inscription_ech["montant_du"] == 20000
        assert all(e["montant_du"] == 5000 for e in echeances if e["type_echeance"] == "MENSUALITE")

    def test_changement_classe_excedent_paye_verse_en_credit(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl_a = _creer_classe(client, auth_headers, frais=50000, mensualite=10000).json()
        cl_b = _creer_classe(client, auth_headers, frais=20000, mensualite=1000).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        insc = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl_a["id"], "id_annee_scolaire": annee["id"],
            "date_inscription": "2025-10-01",
        }, headers=auth_headers).json()

        # Solde l'inscription (50000) + verse 5000 sur le 1er mois.
        resp = client.post("/api/paiements/", json={
            "id_inscription": insc["id"], "montant": 55000,
            "date": "2025-10-01", "mode": "ESPECES",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text

        resp = client.put(f"/api/inscriptions/{insc['id']}", json={"id_classe": cl_b["id"]}, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # INSCRIPTION soldée conserve 50000 ; les 9 mensualités passent à 1000.
        assert body["montant_total"] == 50000 + 9 * 1000
        # 1er mois : 5000 versés pour une mensualité recalibrée à 1000 → 4000 de crédit.
        assert body["credit_disponible"] == 4000.0

    def test_changement_classe_preserve_une_reportee_portee(self, client, auth_headers, db_session):
        """Un impayé REPORTE porté (dette héritée d'une année antérieure) garde
        son montant lors d'un changement de classe : le recalcul ne vaut que
        pour les échéances de l'année courante."""
        t = _creer_tuteur(client, auth_headers).json()
        cl_a = _creer_classe(client, auth_headers, frais=50000, mensualite=10000).json()
        cl_b = _creer_classe(client, auth_headers, frais=20000, mensualite=5000).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        insc = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl_a["id"], "id_annee_scolaire": annee["id"],
            "date_inscription": "2025-12-01",
        }, headers=auth_headers).json()
        inner = db_session.get(models.Inscriptions, insc["id"])

        annee_old = models.AnneesScolaires(
            libelle="2024-2025", date_debut=date(2024, 10, 1), date_fin=date(2025, 6, 30),
            active=False,
        )
        db_session.add(annee_old)
        db_session.flush()
        ancienne = models.Inscriptions(
            matricule_eleve=eleve.matricule, id_classe=cl_a["id"],
            id_annee_scolaire=annee_old.id, date_inscription=date(2024, 10, 1),
            montant_total=7000,
        )
        db_session.add(ancienne)
        db_session.flush()
        source = models.Echeances(
            id_inscription=ancienne.id, id_classe=cl_a["id"], type_echeance="MENSUALITE",
            mois="Octobre", date_echeance=date(2024, 10, 5), montant_du=7000,
            montant_paye=0, statut="REPORTE",
        )
        db_session.add(source)
        db_session.flush()
        # Reportée portée sur l'inscription actuelle (mois non facturé,
        # inscription en décembre : pas de collision sur l'unicité).
        db_session.add(models.Echeances(
            id_inscription=inner.id, id_classe=cl_a["id"], type_echeance="MENSUALITE",
            mois="Octobre", date_echeance=date(2025, 10, 5), montant_du=7000,
            montant_paye=0, statut="REPORTE", id_echeance_origine=source.id,
        ))
        db_session.commit()

        resp = client.put(f"/api/inscriptions/{insc['id']}", json={"id_classe": cl_b["id"]}, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        # INSCRIPTION 20000 + 7 mensualités × 5000 + reportée conservée 7000.
        assert resp.json()["montant_total"] == 20000 + 7 * 5000 + 7000

        echeances = client.get(f"/api/paiements/echeances/{insc['id']}", headers=auth_headers).json()
        portee = next(e for e in echeances if e["mois"] == "Octobre")
        assert portee["montant_du"] == 7000.0
        assert portee["statut"] == "REPORTE"
        assert portee["id_classe"] == cl_b["id"]


class TestPreInscription:
    def test_pre_inscription_sans_classe(self, client, auth_headers, db_session):
        """Une inscription sans classe (id_classe None) est acceptée : pas
        d'échéancier facturé, montant_total à zéro, échéances soldées."""
        t = _creer_tuteur(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        resp = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_annee_scolaire": annee["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["id_classe"] is None
        assert body["montant_total"] == 0.0
        echeances = client.get(f"/api/paiements/echeances/{body['id']}", headers=auth_headers).json()
        assert len(echeances) >= 1
        assert all(e["statut"] == "SOLDE" for e in echeances)


class TestSuppressionAvecRemise:
    def test_suppression_bloquee_si_remise(self, client, auth_headers, db_session):
        t = _creer_tuteur(client, auth_headers).json()
        cl = _creer_classe(client, auth_headers).json()
        annee = _creer_annee(client, auth_headers).json()
        eleve = _creer_eleve(db_session, t["id"])
        insc = client.post("/api/inscriptions/", json={
            "matricule_eleve": eleve.matricule,
            "id_classe": cl["id"], "id_annee_scolaire": annee["id"],
        }, headers=auth_headers).json()
        echeance = client.get(f"/api/paiements/echeances/{insc['id']}", headers=auth_headers).json()[0]
        resp = client.post(f"/api/paiements/echeances/{echeance['id']}/remises", json={
            "montant": 1000, "date": "2025-10-01",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text

        resp = client.delete(f"/api/inscriptions/{insc['id']}", headers=auth_headers)
        assert resp.status_code == 409
        assert "remise" in resp.json()["detail"]


class TestReporterImpayes:
    """Comportement voulu : les échéances REPORTE portées sont re-reportées et
    le crédit non consommé est transféré (et utilisé) sur la nouvelle inscription."""

    def _base(self, db_session):
        annee1 = models.AnneesScolaires(
            libelle="2024-2025", date_debut=date(2024, 9, 1), date_fin=date(2025, 6, 30), active=False
        )
        annee2 = models.AnneesScolaires(
            libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
        )
        db_session.add_all([annee1, annee2])
        db_session.flush()
        tuteur = models.Tuteurs(
            nom="T", prenom="T", email="t@report.com",
            telephone="+22376000000", adresse="Bamako", profession="M",
        )
        db_session.add(tuteur)
        db_session.flush()
        eleve = models.Eleves(
            nom="E", prenom="E", date_de_naissance=date(2012, 1, 1),
            lieu_de_naissance="Bamako", sexe="M", tuteur_id=tuteur.id,
        )
        db_session.add(eleve)
        db_session.flush()
        return annee1, annee2, eleve

    def test_inclut_reportees_portees_et_utilise_credit(self, db_session):
        from routers.inscriptions import _reporter_impayes
        annee1, annee2, eleve = self._base(db_session)
        ancienne = models.Inscriptions(
            matricule_eleve=eleve.matricule, id_classe=None, id_annee_scolaire=annee1.id,
            date_inscription=date(2024, 10, 1), credit_disponible=3000.0,
        )
        db_session.add(ancienne)
        db_session.flush()
        # Source REPORTE (non payable) ; les deux autres sont payables.
        source = models.Echeances(
            id_inscription=ancienne.id, type_echeance="INSCRIPTION", mois=None,
            date_echeance=date(2024, 10, 1), montant_du=12000, montant_paye=0, statut="REPORTE",
        )
        db_session.add(source)
        db_session.flush()
        ech_attente = models.Echeances(
            id_inscription=ancienne.id, type_echeance="MENSUALITE", mois="Octobre",
            date_echeance=date(2024, 10, 5), montant_du=10000, montant_paye=0, statut="EN_ATTENTE",
        )
        db_session.add(ech_attente)
        ech_portee = models.Echeances(
            id_inscription=ancienne.id, type_echeance="MENSUALITE", mois="Novembre",
            date_echeance=date(2024, 11, 5), montant_du=4000, montant_paye=0, statut="REPORTE",
            id_echeance_origine=source.id,
        )
        db_session.add(ech_portee)
        nouvelle = models.Inscriptions(
            matricule_eleve=eleve.matricule, id_classe=None, id_annee_scolaire=annee2.id,
            date_inscription=date(2025, 10, 1),
        )
        db_session.add(nouvelle)
        db_session.flush()

        _reporter_impayes(db_session, eleve.matricule, annee1.id, nouvelle)
        db_session.commit()

        db_session.expire_all()
        nouvelle = db_session.query(models.Inscriptions).filter(
            models.Inscriptions.id_annee_scolaire == annee2.id
        ).first()
        # crédit 3000 entièrement consommé sur les impayés (10000 + 4000 = 14000)
        assert nouvelle.credit_disponible == 0.0
        assert nouvelle.montant_total == 11000.0

        ech_attente = db_session.get(models.Echeances, ech_attente.id)
        ech_portee = db_session.get(models.Echeances, ech_portee.id)
        assert ech_attente.statut == "REPORTE"
        assert ech_portee.statut == "REPORTE"
        # C3 : le crédit consommé pour couvrir un impayé est compté payé sur
        # l'échéance reportée (sinon la dette semble encore due sur l'ancienne
        # inscription).
        assert ech_attente.montant_paye == 3000.0
        assert ech_portee.montant_paye == 0.0

        reportees = db_session.query(models.Echeances).filter(
            models.Echeances.id_inscription == nouvelle.id,
            models.Echeances.statut == "REPORTE",
        ).all()
        assert len(reportees) == 2
        assert sum(e.montant_du for e in reportees) == 11000.0
        assert {e.id_echeance_origine for e in reportees} == {ech_attente.id, ech_portee.id}

    def test_excedent_credit_transfere_sur_nouvelle_inscription(self, db_session):
        from routers.inscriptions import _reporter_impayes
        annee1, annee2, eleve = self._base(db_session)
        ancienne = models.Inscriptions(
            matricule_eleve=eleve.matricule, id_classe=None, id_annee_scolaire=annee1.id,
            date_inscription=date(2024, 10, 1), credit_disponible=20000.0,
        )
        db_session.add(ancienne)
        db_session.flush()
        db_session.add(models.Echeances(
            id_inscription=ancienne.id, type_echeance="MENSUALITE", mois="Octobre",
            date_echeance=date(2024, 10, 5), montant_du=5000, montant_paye=0, statut="EN_ATTENTE",
        ))
        nouvelle = models.Inscriptions(
            matricule_eleve=eleve.matricule, id_classe=None, id_annee_scolaire=annee2.id,
            date_inscription=date(2025, 10, 1),
        )
        db_session.add(nouvelle)
        db_session.flush()

        _reporter_impayes(db_session, eleve.matricule, annee1.id, nouvelle)
        db_session.commit()

        db_session.expire_all()
        nouvelle = db_session.query(models.Inscriptions).filter(
            models.Inscriptions.id_annee_scolaire == annee2.id
        ).first()
        # impayé 5000 couvert par le crédit ; le reste (15000) suit l'élève.
        assert nouvelle.credit_disponible == 15000.0
        assert nouvelle.montant_total == 0.0
        ancienne = db_session.get(models.Inscriptions, ancienne.id)
        assert ancienne.credit_disponible == 0.0
        # C3 : l'échéance couverte par le crédit est bien réputée payée.
        ech_octobre = db_session.query(models.Echeances).filter(
            models.Echeances.id_inscription == ancienne.id
        ).first()
        assert ech_octobre.montant_paye == 5000.0
