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


class TestTropPerçuTraçable:
    def test_trop_percu_trace_et_total_encaisse_exact(self, client, auth_headers, db_session):
        """Le trop-perçu est tracé par une ligne Paiements sans échéance et
        total_encaisse ne compte jamais deux fois le crédit réutilisé."""
        _, _, _, inscription = _seed_base(db_session)
        ech1 = _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Octobre")
        db_session.commit()

        resp = client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 15000,
            "date": "2024-10-05", "mode": "ESPECES",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["nb_paiements_crees"] == 2
        assert body["credit_disponible"] == 5000.0
        assert body["reste_global"] == 0.0

        db_session.expire_all()
        ech1 = db_session.get(models.Echeances, ech1.id)
        assert ech1.montant_paye == 10000.0
        assert ech1.statut == "SOLDE"

        lignes = (
            db_session.query(models.Paiements)
            .filter(models.Paiements.id_inscription == inscription.id)
            .all()
        )
        assert len(lignes) == 2
        ligne_echeance = next(l for l in lignes if l.id_echeance == ech1.id)
        ligne_trop_percu = next(l for l in lignes if l.id_echeance is None)
        assert ligne_echeance.montant == 10000.0
        assert ligne_trop_percu.montant == 5000.0

        stats = client.get("/api/paiements/stats", headers=auth_headers).json()
        assert stats["total_encaisse"] == 15000.0

        # Réutilisation du crédit : pas de double comptage dans total_encaisse.
        ech2 = _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Novembre")
        db_session.commit()
        resp = client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 3000,
            "date": "2024-10-06", "mode": "ESPECES",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        assert resp.json()["credit_disponible"] == 0.0
        assert resp.json()["reste_global"] == 2000.0

        db_session.expire_all()
        ech2 = db_session.get(models.Echeances, ech2.id)
        # 5000 de crédit + 3000 d'espèces = 8000 payés sur l'échéance
        assert ech2.montant_paye == 8000.0
        assert ech2.statut == "PARTIEL"

        stats = client.get("/api/paiements/stats", headers=auth_headers).json()
        assert stats["total_encaisse"] == 18000.0

    def test_trop_percu_supprimable(self, client, auth_headers, db_session):
        _, _, _, inscription = _seed_base(db_session)
        _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Octobre")
        db_session.commit()
        client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 15000,
            "date": "2024-10-05", "mode": "ESPECES",
        }, headers=auth_headers)

        trop_percu = db_session.query(models.Paiements).filter(
            models.Paiements.id_inscription == inscription.id,
            models.Paiements.id_echeance.is_(None),
        ).first()
        assert trop_percu is not None
        resp = client.delete(f"/api/paiements/{trop_percu.id}", headers=auth_headers)
        assert resp.status_code == 204

        db_session.expire_all()
        inscription = db_session.get(models.Inscriptions, inscription.id)
        assert inscription.credit_disponible == 0.0
        stats = client.get("/api/paiements/stats", headers=auth_headers).json()
        assert stats["total_encaisse"] == 10000.0

    def test_trop_percu_modifiable(self, client, auth_headers, db_session):
        _, _, _, inscription = _seed_base(db_session)
        _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Octobre")
        db_session.commit()
        client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 15000,
            "date": "2024-10-05", "mode": "ESPECES",
        }, headers=auth_headers)

        trop_percu = db_session.query(models.Paiements).filter(
            models.Paiements.id_inscription == inscription.id,
            models.Paiements.id_echeance.is_(None),
        ).first()
        resp = client.put(f"/api/paiements/{trop_percu.id}", json={"montant": 3000}, headers=auth_headers)
        assert resp.status_code == 200, resp.text

        db_session.expire_all()
        inscription = db_session.get(models.Inscriptions, inscription.id)
        assert inscription.credit_disponible == 3000.0
        stats = client.get("/api/paiements/stats", headers=auth_headers).json()
        assert stats["total_encaisse"] == 13000.0

    def test_modifier_paiement_depassant_la_cap_refuse(self, client, auth_headers, db_session):
        """Augmenter un paiement au-delà du montant_du est refusé : l'excédent
        doit être enregistré comme un versement sans échéance (crédit), jamais
        scellé dans un paiement plafonné qui corromprait le crédit à sa
        suppression."""
        _, _, _, inscription = _seed_base(db_session)
        ech = _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Octobre")
        db_session.commit()
        client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 10000,
            "date": "2024-10-05", "mode": "ESPECES",
        }, headers=auth_headers)

        paiement = db_session.query(models.Paiements).filter(
            models.Paiements.id_inscription == inscription.id,
            models.Paiements.id_echeance == ech.id,
        ).first()
        resp = client.put(f"/api/paiements/{paiement.id}", json={"montant": 15000}, headers=auth_headers)
        assert resp.status_code == 400

        db_session.expire_all()
        ech = db_session.get(models.Echeances, ech.id)
        assert ech.montant_paye == 10000.0
        assert ech.statut == "SOLDE"
        inscription = db_session.get(models.Inscriptions, inscription.id)
        assert inscription.credit_disponible == 0.0  # aucun surplus créé
        stats = client.get("/api/paiements/stats", headers=auth_headers).json()
        assert stats["total_encaisse"] == 10000.0

    def test_suppression_trop_percu_consomme_refuse(self, client, auth_headers, db_session):
        """Supprimer un trop-perçu déjà consommé (crédit utilisé sur des
        échéances) est refusé au lieu de silencieusement casser le total."""
        _, _, _, inscription = _seed_base(db_session)
        _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Octobre")
        db_session.commit()
        client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 15000,
            "date": "2024-10-05", "mode": "ESPECES",
        }, headers=auth_headers)
        assert inscription.credit_disponible == 5000.0
        # Le crédit (5000) + 3000 d'espèces couvrent le 2e mois → crédit à 0.
        _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Novembre")
        db_session.commit()
        resp = client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 3000,
            "date": "2024-10-15", "mode": "ESPECES",
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["credit_disponible"] == 0.0

        trop_percu = db_session.query(models.Paiements).filter(
            models.Paiements.id_inscription == inscription.id,
            models.Paiements.id_echeance.is_(None),
        ).first()
        assert trop_percu is not None
        resp = client.delete(f"/api/paiements/{trop_percu.id}", headers=auth_headers)
        assert resp.status_code == 400

    def test_modification_trop_percu_consomme_refuse(self, client, auth_headers, db_session):
        """Réduire un trop-perçu déjà consommé dont le crédit est épuisé est
        refusé (pas de clamp silencieux qui ferait perdre de l'argent)."""
        _, _, _, inscription = _seed_base(db_session)
        _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Octobre")
        db_session.commit()
        client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 15000,
            "date": "2024-10-05", "mode": "ESPECES",
        }, headers=auth_headers)
        _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Novembre")
        db_session.commit()
        client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 3000,
            "date": "2024-10-15", "mode": "ESPECES",
        }, headers=auth_headers)

        trop_percu = db_session.query(models.Paiements).filter(
            models.Paiements.id_inscription == inscription.id,
            models.Paiements.id_echeance.is_(None),
        ).first()
        assert trop_percu is not None
        resp = client.put(f"/api/paiements/{trop_percu.id}", json={"montant": 1000}, headers=auth_headers)
        assert resp.status_code == 400


class TestEcheancesReportées:
    def test_reportee_portee_payable_et_statut_maj(self, client, auth_headers, db_session):
        """Une échéance REPORTE portée est payable ; son statut évolue
        REPORTE → PARTIEL → SOLDE sans jamais toucher l'échéance source."""
        _, _, _, inscription = _seed_base(db_session)
        source = _echeance(db_session, inscription, "REPORTE", 10000, 0, id_echeance_origine=None)
        portee = _echeance(
            db_session, inscription, "REPORTE", 7000, 0,
            mois="Octobre", id_echeance_origine=source.id,
        )
        db_session.commit()

        resp = client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 3000,
            "date": "2024-10-05", "mode": "ESPECES",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        assert resp.json()["reste_global"] == 4000.0

        db_session.expire_all()
        portee = db_session.get(models.Echeances, portee.id)
        assert portee.montant_paye == 3000.0
        assert portee.statut == "PARTIEL"
        source = db_session.get(models.Echeances, source.id)
        assert source.statut == "REPORTE"  # jamais ciblée par un paiement

        resp = client.post("/api/paiements/", json={
            "id_inscription": inscription.id, "montant": 4000,
            "date": "2024-10-06", "mode": "ESPECES",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        assert resp.json()["reste_global"] == 0.0

        db_session.expire_all()
        portee = db_session.get(models.Echeances, portee.id)
        assert portee.statut == "SOLDE"
        stats = client.get("/api/paiements/stats", headers=auth_headers).json()
        assert stats["montant_impaye"] == 0.0
        assert stats["nb_echeances_impayees"] == 0

    def test_paiement_groupe_inclut_reportee_portee(self, client, auth_headers, db_session):
        _, _, _, inscription = _seed_base(db_session)
        source = _echeance(db_session, inscription, "REPORTE", 10000, 0, id_echeance_origine=None)
        portee = _echeance(
            db_session, inscription, "REPORTE", 5000, 0,
            mois="Octobre", id_echeance_origine=source.id,
        )
        db_session.commit()
        tuteur = db_session.query(models.Tuteurs).first()

        resp = client.post("/api/paiements/groupes", json={
            "id_tuteur": tuteur.id, "montant_total": 5000,
            "date": "2024-10-05", "mode": "ESPECES",
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        assert resp.json()["nb_paiements_crees"] == 1
        assert resp.json()["reste_total"] == 0.0

        db_session.expire_all()
        portee = db_session.get(models.Echeances, portee.id)
        assert portee.statut == "SOLDE"


class TestRecuPaiement:
    def test_recu_pdf_200(self, client, auth_headers, db_session):
        _, _, _, inscription = _seed_base(db_session)
        ech = _echeance(db_session, inscription, "EN_ATTENTE", 10000, 0, mois="Octobre")
        db_session.add(models.Paiements(
            id_inscription=inscription.id, id_echeance=ech.id,
            date=date(2024, 10, 5), montant=10000, mode="ESPECES",
        ))
        db_session.commit()

        paiement = db_session.query(models.Paiements).filter(
            models.Paiements.id_inscription == inscription.id,
            models.Paiements.id_echeance == ech.id,
        ).first()
        resp = client.get(f"/api/paiements/{paiement.id}/recu", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.headers["Content-Type"].startswith("application/pdf")

        disposition = resp.headers["Content-Disposition"]
        assert disposition.startswith("inline;")
        assert f"recu-{paiement.code_paiement or paiement.id}.pdf" in disposition

        # Invariant PDF réel (pas une erreur HTML/JSON) : en-tête %PDF.
        assert resp.content[:5] == b"%PDF-"

    def test_recu_404_inconnu(self, client, auth_headers):
        resp = client.get("/api/paiements/999999/recu", headers=auth_headers)
        assert resp.status_code == 404


class TestRelances:
    def _seed(self, db):
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
            nom="T", prenom="T", email="t@relance.com",
            telephone="010200300", adresse="Bamako", profession="M",
        )
        db.add(tuteur)
        db.flush()

        def _eleve():
            e = models.Eleves(
                nom="E", prenom="E",
                date_de_naissance=date(2013, 1, 1), lieu_de_naissance="Bamako",
                sexe="M", tuteur_id=tuteur.id, classe_id=classe.id,
            )
            db.add(e)
            db.flush()
            return e

        e1 = _eleve()
        e2 = _eleve()
        insc_act = models.Inscriptions(
            matricule_eleve=e1.matricule, id_classe=classe.id, id_annee_scolaire=annee.id,
            date_inscription=date(2024, 10, 1), montant_total=0,
        )
        db.add(insc_act)
        db.flush()
        insc_old = models.Inscriptions(
            matricule_eleve=e2.matricule, id_classe=classe.id, id_annee_scolaire=ancienne.id,
            date_inscription=date(2023, 10, 1), montant_total=0,
        )
        db.add(insc_old)
        db.flush()

        source = models.Echeances(
            id_inscription=insc_old.id, id_classe=classe.id, type_echeance="MENSUALITE",
            mois="Octobre", date_echeance=date(2023, 10, 5), montant_du=5000, montant_paye=0,
            statut="REPORTE",
        )
        db.add(source)
        db.flush()
        db.add(models.Echeances(
            id_inscription=insc_act.id, id_classe=classe.id, type_echeance="MENSUALITE",
            mois="Septembre", date_echeance=date(2025, 9, 5), montant_du=4000, montant_paye=0,
            statut="REPORTE", id_echeance_origine=source.id,
        ))
        db.add(models.Echeances(
            id_inscription=insc_act.id, id_classe=classe.id, type_echeance="MENSUALITE",
            mois="Octobre", date_echeance=date(2024, 10, 5), montant_du=3000, montant_paye=0,
            statut="EN_ATTENTE",
        ))
        db.commit()
        return insc_act

    def test_relances_limitees_a_l_annee_active_et_payables(self, client, auth_headers, db_session):
        """Seules les échéances payables et dépassées d'inscriptions de l'année
        active remontent : ni l'impayé d'une ancienne année, ni une échéance
        REPORTE source (non payable)."""
        insc_act = self._seed(db_session)
        resp = client.get("/api/paiements/relances", headers=auth_headers)
        assert resp.status_code == 200
        relances = resp.json()
        assert len(relances) == 2
        matricules = sorted(r["matricule_eleve"] for r in relances)
        assert matricules == [insc_act.matricule_eleve, insc_act.matricule_eleve]
        montants = sorted(r["montant_du"] for r in relances)
        assert montants == [3000.0, 4000.0]