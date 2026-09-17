"""Tests d'intégration du router Paiements axés sur la synthèse « payé / impayé ».

Couverture : endpoint GET /api/paiements/stats — total encaissé, montant
impayé (avec gestion du double comptage des échéances REPORTE), et compteurs
d'échéances soldées / impayées.
"""
from datetime import date

import models


def _seed_base(db, annee_debut=date(2024, 10, 1), annee_fin=date(2025, 6, 30)):
    """Mini-grammaire : année active, classe, élève, inscription, échéances."""
    annee = models.AnneesScolaires(
        libelle="2024-2025", date_debut=annee_debut, date_fin=annee_fin, active=True
    )
    db.add(annee)
    db.flush()

    classe = models.Classes(niveau="1ère Année", nom="1ère Année A", frais_inscription=0, mensualite=0)
    db.add(classe)
    db.flush()

    tuteur = models.Tuteurs(
        nom="Traoré", prenom="Moussa", email="moussa.traore@test.com",
        telephone="0100200300", adresse="Bamako", profession="Commerçant",
    )
    db.add(tuteur)
    db.flush()

    eleve = models.Eleves(
        matricule="EL0001", nom="Diallo", prenom="Fatou",
        date_de_naissance=date(2014, 3, 3), lieu_de_naissance="Bamako",
        sexe="F", statut="actif",
        tuteur_id=tuteur.id, classe_id=classe.id,
    )
    db.add(eleve)
    db.flush()

    inscription = models.Inscriptions(
        code_inscription="INS0001", matricule_eleve=eleve.matricule,
        id_classe=classe.id, id_annee_scolaire=annee.id,
        date_inscription=date(2024, 10, 1), montant_total=30000,
    )
    db.add(inscription)
    db.flush()

    return annee, classe, eleve, inscription


def _echeance(db, inscription, statut, montant_du, montant_paye, mois=None, id_echeance_origine=None):
    ech = models.Echeances(
        id_inscription=inscription.id, id_classe=inscription.id_classe,
        type_echeance="MENSUALITE" if mois else "INSCRIPTION", mois=mois,
        date_echeance=inscription.date_inscription,
        montant_du=montant_du, montant_paye=montant_paye, statut=statut,
        id_echeance_origine=id_echeance_origine,
    )
    db.add(ech)
    db.flush()
    return ech


def _paiement(db, inscription, echeance, montant, date_paiement):
    db.add(models.Paiements(
        id_inscription=inscription.id, id_echeance=echeance.id,
        date=date_paiement, montant=montant, mode="ESPECES",
    ))


class TestStatsPaiements:
    def test_stats_sur_base_vide(self, client, auth_headers):
        resp = client.get("/api/paiements/stats", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == {
            "total_encaisse": 0.0,
            "montant_impaye": 0.0,
            "nb_echeances_soldees": 0,
            "nb_echeances_impayees": 0,
        }

    def test_stats_basiques(self, client, auth_headers, db_session):
        _, _, _, inscription = _seed_base(db_session)
        solde = _echeance(db_session, inscription, "SOLDE", 10000, 10000, mois="Octobre")
        _paiement(db_session, inscription, solde, 10000, date(2024, 10, 5))
        _echeance(db_session, inscription, "EN_ATTENTE", 9000, 0, mois="Novembre")
        partiel = _echeance(db_session, inscription, "PARTIEL", 8000, 3000, mois="Décembre")
        _paiement(db_session, inscription, partiel, 3000, date(2024, 12, 10))
        db_session.commit()

        resp = client.get("/api/paiements/stats", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        # 10000 + 3000 encaissés ; impayé = 5000 (partiel) + 9000 (en attente)
        assert body["total_encaisse"] == 13000.0
        assert body["montant_impaye"] == 14000.0
        assert body["nb_echeances_soldees"] == 1
        assert body["nb_echeances_impayees"] == 2

    def test_report_n_est_pas_compte_deux_fois(self, client, auth_headers, db_session):
        """Une échéance REPORTE source (d'une année précédente) ne doit pas être
        comptée dans l'impayé : son reste a été transféré vers l'échéance REPORTE
        portée (id_echeance_origine non NULL), seule représentante de l'impayé."""
        _, _, _, inscription = _seed_base(db_session)
        source = _echeance(db_session, inscription, "REPORTE", 10000, 0, id_echeance_origine=None)
        portee = _echeance(
            db_session, inscription, "REPORTE", 7000, 0,
            mois="Octobre", id_echeance_origine=source.id,
        )
        db_session.commit()

        resp = client.get("/api/paiements/stats", headers=auth_headers)
        assert resp.json()["montant_impaye"] == 7000.0
        assert resp.json()["nb_echeances_impayees"] == 1