"""Tests du point de réconciliation financière.

Couverture : GET /api/finances/recapitulatif — encaissé, dépenses, solde et
impayés sur tout l'historique puis sur l'année scolaire active. L'encaissé de
l'année ne compte que les versements des inscriptions de cette année (pas les
impayés réglés d'années antérieures) et les échéances REPORTE sources sont
exclues de l'impayé (dette déjà transférée).
"""
from datetime import date

import models


def _seed(db):
    annee = models.AnneesScolaires(
        libelle="2024-2025", date_debut=date(2024, 10, 1), date_fin=date(2025, 6, 30), active=True
    )
    db.add(annee)
    db.flush()
    ancienne = models.AnneesScolaires(
        libelle="2023-2024", date_debut=date(2023, 10, 1), date_fin=date(2024, 6, 30), active=False
    )
    db.add(ancienne)
    db.flush()
    classe = models.Classes(niveau="1ère Année", nom="1ère Année A", frais_inscription=0, mensualite=0)
    db.add(classe)
    db.flush()
    tuteur = models.Tuteurs(
        nom="T", prenom="T", email="t@fin.com", telephone="010200300",
        adresse="Bamako", profession="M",
    )
    db.add(tuteur)
    db.flush()

    e1 = models.Eleves(
        nom="E1", prenom="E1", date_de_naissance=date(2013, 1, 1),
        lieu_de_naissance="Bamako", sexe="M", tuteur_id=tuteur.id, classe_id=classe.id,
    )
    db.add(e1)
    db.flush()
    e2 = models.Eleves(
        nom="E2", prenom="E2", date_de_naissance=date(2012, 2, 2),
        lieu_de_naissance="Bamako", sexe="F", tuteur_id=tuteur.id, classe_id=classe.id,
    )
    db.add(e2)
    db.flush()

    insc_act = models.Inscriptions(
        matricule_eleve=e1.matricule, id_classe=classe.id, id_annee_scolaire=annee.id,
        date_inscription=date(2024, 10, 1), montant_total=10000,
    )
    db.add(insc_act)
    db.flush()

    soldee = models.Echeances(
        id_inscription=insc_act.id, id_classe=classe.id, type_echeance="INSCRIPTION",
        date_echeance=date(2024, 10, 1), montant_du=10000, montant_paye=10000, statut="SOLDE",
    )
    db.add(soldee)
    db.flush()
    db.add(models.Paiements(
        id_inscription=insc_act.id, id_echeance=soldee.id,
        date=date(2024, 10, 15), montant=10000, mode="ESPECES",
    ))
    db.add(models.Echeances(
        id_inscription=insc_act.id, id_classe=classe.id, type_echeance="MENSUALITE",
        mois="Octobre", date_echeance=date(2024, 11, 5), montant_du=4000, montant_paye=0,
        statut="EN_ATTENTE",
    ))

    insc_old = models.Inscriptions(
        matricule_eleve=e2.matricule, id_classe=classe.id, id_annee_scolaire=ancienne.id,
        date_inscription=date(2023, 10, 1), montant_total=0,
    )
    db.add(insc_old)
    db.flush()
    source = models.Echeances(
        id_inscription=insc_old.id, id_classe=classe.id, type_echeance="MENSUALITE",
        mois="Septembre", date_echeance=date(2023, 9, 5), montant_du=2500, montant_paye=0,
        statut="REPORTE",
    )
    db.add(source)
    db.flush()
    db.add(models.Echeances(
        id_inscription=insc_act.id, id_classe=classe.id, type_echeance="MENSUALITE",
        mois="Septembre", date_echeance=date(2025, 9, 5), montant_du=2500, montant_paye=0,
        statut="REPORTE", id_echeance_origine=source.id,
    ))
    db.add(models.Echeances(
        id_inscription=insc_old.id, id_classe=classe.id, type_echeance="INSCRIPTION",
        date_echeance=date(2023, 10, 1), montant_du=5000, montant_paye=0, statut="EN_ATTENTE",
    ))
    # Impayé d'une ancienne année réglé DANS l'année active : encaissé
    # (historique), mais pas de l'année (inscription d'une autre année).
    db.add(models.Paiements(
        id_inscription=insc_old.id, date=date(2025, 1, 10), montant=2000, mode="CHEQUE",
    ))
    db.add(models.Depenses(
        libelle="D1", montant=3000, categorie="FOURNITURES", date=date(2025, 1, 15),
        code_depense="DEP0001",
    ))
    db.commit()
    return annee, insc_act


class TestRecapitulatif:
    def test_sur_base_vide(self, client, auth_headers):
        resp = client.get("/api/finances/recapitulatif", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["annee"] is None
        assert body["annee_id"] is None
        assert body["historique"] == {
            "total_encaisse": 0.0, "total_depenses": 0.0, "solde": 0.0,
            "montant_impaye": 0.0, "nb_echeances_impayees": 0, "nb_echeances_soldees": 0,
        }

    def test_recapitulatif_global_et_annee(self, client, auth_headers, db_session):
        annee, _ = _seed(db_session)
        resp = client.get("/api/finances/recapitulatif", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()

        assert body["annee_id"] == annee.id
        assert body["annee_libelle"] == "2024-2025"

        hist = body["historique"]
        assert hist["total_encaisse"] == 12000.0  # 10000 année courante + 2000 impayé réglé
        assert hist["total_depenses"] == 3000.0
        assert hist["solde"] == 9000.0
        # Impayé : 4000 + 2500 (année courante) + 5000 (ancienne inscription).
        assert hist["montant_impaye"] == 11500.0
        assert hist["nb_echeances_impayees"] == 3
        assert hist["nb_echeances_soldees"] == 1

        an = body["annee"]
        # L'encaissé de l'année exclut l'impayé d'ancienne année réglé en 2025.
        assert an["total_encaisse"] == 10000.0
        assert an["total_depenses"] == 3000.0
        assert an["solde"] == 7000.0
        assert an["montant_impaye"] == 6500.0  # 4000 + 2500, sans le 5000 d'avant
        assert an["nb_echeances_impayees"] == 2
        assert an["nb_echeances_soldees"] == 1