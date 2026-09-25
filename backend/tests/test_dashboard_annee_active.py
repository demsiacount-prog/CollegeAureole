"""Tests du tableau de bord : les fenêtres temporelles sont calées sur
l'année scolaire ACTIVE (et non sur le calendrier civil), pour refléter
l'état réel des données même si on les consulte en pleine période de congé.
"""
from datetime import date

import models


def _seed(db, annee_debut=date(2024, 10, 7), annee_fin=date(2025, 6, 27)):
    annee = models.AnneesScolaires(
        libelle="2024-2025", date_debut=annee_debut, date_fin=annee_fin, active=True
    )
    db.add(annee)
    db.flush()

    classe = models.Classes(niveau="1ère Année", nom="1ère Année A", frais_inscription=0, mensualite=0)
    db.add(classe)
    db.flush()

    tuteur = models.Tuteurs(
        nom="Keita", prenom="Balla", email="balla.keita@test.com",
        telephone="010200300", adresse="Bamako", profession="Enseignant",
    )
    db.add(tuteur)
    db.flush()

    eleves = []
    for i in range(2):
        e = models.Eleves(
            matricule=f"DA{i:04d}", nom="Cissé", prenom=f"Élève {i}",
            date_de_naissance=date(2013, 1, 1), lieu_de_naissance="Bamako",
            sexe="F" if i % 2 == 0 else "M",
            statut="actif", tuteur_id=tuteur.id, classe_id=classe.id,
        )
        db.add(e)
        db.flush()
        eleves.append(e)

    inscriptions = []
    for i, e in enumerate(eleves):
        insc = models.Inscriptions(
            code_inscription=f"INS000{i}", matricule_eleve=e.matricule,
            id_classe=classe.id, id_annee_scolaire=annee.id,
            date_inscription=annee_debut, montant_total=10000,
        )
        db.add(insc)
        db.flush()
        inscriptions.append(insc)
    return annee, eleves, inscriptions


class TestStatsDirectionAnneeActive:
    def test_paiements_et_absences_cales_sur_l_annee_active(self, client, auth_headers, db_session):
        annee, eleves, inscriptions = _seed(db_session)

        # Paiement DANS l'année active (oct 2024) : compté.
        ech1 = models.Echeances(
            id_inscription=inscriptions[0].id, id_classe=inscriptions[0].id_classe,
            type_echeance="INSCRIPTION", date_echeance=annee.date_debut,
            montant_du=10000, montant_paye=10000, statut="SOLDE",
        )
        db_session.add(ech1)
        db_session.flush()
        db_session.add(models.Paiements(
            id_inscription=inscriptions[0].id, id_echeance=ech1.id,
            date=date(2024, 10, 15), montant=10000, mode="ESPECES",
        ))
        # Paiement HORS année active (sept 2026, calendrier réel) : ignoré.
        db_session.add(models.Paiements(
            id_inscription=inscriptions[1].id,
            date=date(2026, 9, 1), montant=5000, mode="CHEQUE",
        ))

        # 2 absences dans l'année active (oct + nov 2024), 1 hors (sept 2026).
        for d in (date(2024, 10, 9), date(2024, 11, 20), date(2026, 9, 3)):
            db_session.add(models.Absences(
                matricule_eleve=eleves[0].matricule, date_absence=d,
            ))

        db_session.commit()

        resp = client.get("/api/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()

        # Nouvelles clés renvoyées.
        assert "paiements_annee" in body and "absences_annee" in body
        assert "paiements_mois" not in body and "absences_7_jours" not in body

        assert body["nb_eleves"] == 2
        assert body["paiements_annee"] == 10000.0  # le paiement 2026 est exclu
        assert body["absences_annee"] == 2  # seule l'absence 2026 est exclue
        assert len(body["absences_par_mois"]) == 9  # Oct→Juin de l'année active
        oct_nov = {a["mois"]: a["absences"] for a in body["absences_par_mois"]}
        assert oct_nov["Oct"] == 1 and oct_nov["Nov"] == 1
        assert all(a["absences"] == 0 for a in body["absences_par_mois"] if a["mois"] not in ("Oct", "Nov"))

    def test_sans_annee_active_retourne_409(self, client, auth_headers, db_session):
        _seed(db_session)
        # Retire l'année active : aucune fenêtre possible.
        db_session.query(models.Inscriptions).delete()
        db_session.query(models.AnneesScolaires).delete()
        db_session.commit()

        resp = client.get("/api/dashboard/stats", headers=auth_headers)
        assert resp.status_code == 409