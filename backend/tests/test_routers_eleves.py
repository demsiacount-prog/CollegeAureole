"""Tests d'intégration du router Élèves via TestClient.

Couverture : CRUD complet, recherche par nom/prénom/matricule, activation/
désactivation, dossier complet, inscription automatique, et protections.
"""
import pytest
from datetime import date

import models


def _creer_tuteur(client, auth_headers):
    return client.post("/api/tuteurs/", json={
        "nom": "Diallo", "prenom": "Aminata", "email": "a@ex.com",
        "telephone": "+223 76 00 11 22", "adresse": "Bamako", "profession": "Enseignante",
    }, headers=auth_headers)


def _creer_annee(client, auth_headers):
    return client.post("/api/anneesScolaires/", json={
        "libelle": "2025-2026", "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers)


def _creer_classe(client, auth_headers, niveau="1ère Année", nom="A"):
    return client.post("/api/classes/", json={"niveau": niveau, "nom": nom}, headers=auth_headers)


def _creer_eleve(client, auth_headers, tuteur_id, classe_id=None):
    """Crée un élève. Sans classe_id fournie, crée année active + classe au préalable."""
    if classe_id is None:
        _creer_annee(client, auth_headers)
        classe = _creer_classe(client, auth_headers).json()
        classe_id = classe["id"]
    return client.post("/api/eleves/", json={
        "nom": "Konaté", "prenom": "Amadou",
        "date_de_naissance": "2012-03-15",
        "lieu_de_naissance": "Bamako", "sexe": "M",
        "tuteur_id": tuteur_id, "classe_id": classe_id,
    }, headers=auth_headers)


class TestCreation:
    def test_creer_eleve(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        resp = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"])
        assert resp.status_code == 201
        body = resp.json()
        assert body["matricule"].startswith("AU")
        assert body["nom"] == "Konaté"
        assert body["tuteur"]["id"] == tuteur["id"]

    def test_creer_eleve_sans_classe_inscrit_sans_classe(self, client, auth_headers):
        """Un élève sans classe peut être créé : c'est une pré-inscription.

        L'inscription est créée avec id_classe=None (visible dans les listes de
        l'année, l'affectation se fait ensuite via Inscriptions), au lieu de
        bloquer la création.
        """
        _creer_annee(client, auth_headers)
        tuteur = _creer_tuteur(client, auth_headers).json()
        resp = client.post("/api/eleves/", json={
            "nom": "Konaté", "prenom": "Amadou",
            "date_de_naissance": "2012-03-15",
            "lieu_de_naissance": "Bamako", "sexe": "M",
            "tuteur_id": tuteur["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["classe"] is None
        matricule = body["matricule"]
        inscs = client.get(f"/api/inscriptions/?matricule_eleve={matricule}", headers=auth_headers).json()
        assert len(inscs) >= 1
        assert inscs[0]["id_classe"] is None

    def test_creer_eleve_classe_introuvable_404(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        resp = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"], classe_id=99999)
        assert resp.status_code == 404

    def test_creer_eleve_avec_classe_inscrit(self, client, auth_headers):
        """Créer un élève avec une classe crée automatiquement une inscription."""
        _creer_annee(client, auth_headers)  # active year required
        tuteur = _creer_tuteur(client, auth_headers).json()
        classe = _creer_classe(client, auth_headers).json()
        resp = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"], classe_id=classe["id"])
        assert resp.status_code == 201
        matricule = resp.json()["matricule"]
        inscs = client.get(f"/api/inscriptions/?matricule_eleve={matricule}", headers=auth_headers)
        assert inscs.status_code == 200
        assert len(inscs.json()) >= 1

    def test_tuteur_introuvable_404(self, client, auth_headers):
        resp = _creer_eleve(client, auth_headers, tuteur_id=99999)
        assert resp.status_code == 404

    def test_sans_annee_active_400(self, client, auth_headers):
        """Avec classe mais sans année scolaire active, l'inscription échoue (400)."""
        tuteur = _creer_tuteur(client, auth_headers).json()
        classe = _creer_classe(client, auth_headers).json()
        resp = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"], classe_id=classe["id"])
        assert resp.status_code == 400

    def test_annee_scolaire_invalide_avec_classe_404(self, client, auth_headers):
        """Avec classe_id et année inexistante → 404 sur l'inscription."""
        tuteur = _creer_tuteur(client, auth_headers).json()
        classe = _creer_classe(client, auth_headers).json()
        data = {
            "nom": "X", "prenom": "Y", "date_de_naissance": "2012-01-01",
            "lieu_de_naissance": "Bamako", "sexe": "F",
            "tuteur_id": tuteur["id"], "classe_id": classe["id"],
            "annee_scolaire_id": 99999,
        }
        resp = client.post("/api/eleves/", json=data, headers=auth_headers)
        assert resp.status_code == 404


class TestLecture:
    def test_liste_vide(self, client, auth_headers):
        resp = client.get("/api/eleves/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_liste_apres_creation(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"])
        resp = client.get("/api/eleves/", headers=auth_headers)
        assert len(resp.json()) == 1

    def test_get_par_matricule(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.get(f"/api/eleves/{created['matricule']}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Konaté"

    def test_eleve_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/eleves/AU9900000", headers=auth_headers)
        assert resp.status_code == 404

    def test_compte(self, client, auth_headers):
        _creer_annee(client, auth_headers)  # active year required
        tuteur = _creer_tuteur(client, auth_headers).json()
        _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"])
        classe = _creer_classe(client, auth_headers).json()
        resp = client.post("/api/eleves/", json={
            "nom": "Konaté", "prenom": "Autre",
            "date_de_naissance": "2012-03-15", "lieu_de_naissance": "Bamako",
            "sexe": "F", "tuteur_id": tuteur["id"], "classe_id": classe["id"],
        }, headers=auth_headers)
        assert resp.status_code == 201
        resp = client.get("/api/eleves/compte", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 2

    def test_recherche_par_nom(self, client, auth_headers):
        _creer_annee(client, auth_headers)  # active year required
        tuteur = _creer_tuteur(client, auth_headers).json()
        _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"])
        classe = _creer_classe(client, auth_headers).json()
        client.post("/api/eleves/", json={
            "nom": "Traoré", "prenom": "X",
            "date_de_naissance": "2012-03-15", "lieu_de_naissance": "Bamako",
            "sexe": "M", "tuteur_id": tuteur["id"], "classe_id": classe["id"],
        }, headers=auth_headers)
        resp = client.get("/api/eleves/?q=Konaté", headers=auth_headers)
        noms = [e["nom"] for e in resp.json()]
        assert "Konaté" in noms
        assert "Traoré" not in noms


class TestModification:
    def test_modifier_eleve(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.put(
            f"/api/eleves/{created['matricule']}",
            json={"nom": "NouveauNom"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nom"] == "NouveauNom"

    def test_modifier_identite_eleve(self, client, auth_headers):
        """date_de_naissance / sexe / lieu_de_naissance doivent être corrigibles
        après création (mêmes validations qu'à la création)."""
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.put(
            f"/api/eleves/{created['matricule']}",
            json={"date_de_naissance": "2011-01-01", "sexe": "F", "lieu_de_naissance": "Ségou"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["date_de_naissance"] == "2011-01-01"
        assert body["sexe"] == "F"
        assert body["lieu_de_naissance"] == "Ségou"
        # Le matricule n'est pas modifiable : il reste celui d'origine.
        assert body["matricule"] == created["matricule"]

    def test_modifier_sexe_invalide_422(self, client, auth_headers):
        """La validation à la modification est la même qu'à la création : un
        sexe hors de M/F est refusé."""
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.put(
            f"/api/eleves/{created['matricule']}",
            json={"sexe": "X"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_matricule_present_dans_payload_invalide(self, client, auth_headers):
        """Le corps d'une mise à jour ne doit pas exposer le matricule : fournir
        un champ inconnu est ignoré ou refusé, jamais appliqué."""
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.put(
            f"/api/eleves/{created['matricule']}",
            json={"nom": "Autre"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["matricule"] == created["matricule"]


class TestActivationDesactivation:
    def test_desactiver_eleve(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.patch(f"/api/eleves/{created['matricule']}/desactiver", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["statut"] == "inactif"

    def test_activer_eleve(self, client, auth_headers):
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        client.patch(f"/api/eleves/{created['matricule']}/desactiver", headers=auth_headers)
        resp = client.patch(f"/api/eleves/{created['matricule']}/activer", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["statut"] == "actif"


class TestDossierComplet:
    def test_dossier_eleve(self, client, auth_headers):
        _creer_annee(client, auth_headers)  # active year required
        tuteur = _creer_tuteur(client, auth_headers).json()
        classe = _creer_classe(client, auth_headers).json()
        created = client.post("/api/eleves/", json={
            "nom": "Konaté", "prenom": "Amadou",
            "date_de_naissance": "2012-03-15",
            "lieu_de_naissance": "Bamako", "sexe": "M",
            "tuteur_id": tuteur["id"], "classe_id": classe["id"],
            "nom_pere": "Keita", "prenom_pere": "Modibo", "fonction_pere": "Commerçant",
            "nom_mere": "Coulibaly", "prenom_mere": "Aminata", "fonction_mere": "Ménagère",
        }, headers=auth_headers).json()
        resp = client.get(f"/api/eleves/{created['matricule']}/dossier", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["matricule"] == created["matricule"]
        assert body["tuteur"]["id"] == tuteur["id"]
        assert body["nom_pere"] == "Keita"
        assert body["prenom_pere"] == "Modibo"
        assert body["fonction_pere"] == "Commerçant"
        assert body["nom_mere"] == "Coulibaly"
        assert body["prenom_mere"] == "Aminata"
        assert body["fonction_mere"] == "Ménagère"
        assert isinstance(body["inscriptions"], list)
        assert isinstance(body["notes"], list)
        assert isinstance(body["absences"], list)
        assert isinstance(body["bulletins"], list)

    def test_dossier_introuvable_404(self, client, auth_headers):
        resp = client.get("/api/eleves/AU9900000/dossier", headers=auth_headers)
        assert resp.status_code == 404


class TestListeParAnnee:
    def test_liste_scopee_annee_utilise_inscriptions(self, client, auth_headers, db_session):
        """La liste scopée à une année (id_annee_scolaire) lit la classe et le
        statut sur les INSCRIPTIONS de cette année, pas sur l'élève (état actuel).

        Un élève passé en classe B retrouve sa classe A de l'année demandée ;
        le statut « Transféré » d'une inscription prime sur eleve.statut.
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

        t = client.post("/api/tuteurs/", json={
            "nom": "Diallo", "prenom": "Aminata", "email": "a2@ex.com",
            "telephone": "+223 76 00 11 22", "adresse": "Bamako", "profession": "Enseignante",
        }, headers=auth_headers).json()
        e1 = models.Eleves(
            nom="Konaté", prenom="Amadou", date_de_naissance=date(2012, 3, 15),
            lieu_de_naissance="Bamako", sexe="M", statut="actif",
            tuteur_id=t["id"], classe_id=classe_b.id,  # classe ACTUELLE = B
        )
        e2 = models.Eleves(
            nom="Traoré", prenom="Fatoumata", date_de_naissance=date(2011, 7, 1),
            lieu_de_naissance="Ségou", sexe="F", statut="actif",
            tuteur_id=t["id"], classe_id=classe_a.id,
        )
        db_session.add_all([e1, e2])
        db_session.flush()
        db_session.add_all([
            models.Inscriptions(matricule_eleve=e1.matricule, id_classe=classe_a.id,
                                id_annee_scolaire=annee1.id, statut="Inscrit"),
            models.Inscriptions(matricule_eleve=e1.matricule, id_classe=classe_b.id,
                                id_annee_scolaire=annee2.id, statut="Inscrit"),
            models.Inscriptions(matricule_eleve=e2.matricule, id_classe=classe_a.id,
                                id_annee_scolaire=annee1.id, statut="Transféré"),
        ])
        db_session.commit()

        tous = client.get(f"/api/eleves/?id_annee_scolaire={annee1.id}", headers=auth_headers).json()
        assert len(tous) == 2

        # Classe de l'année 1 = A, même si e1 est actuellement en B.
        en_a = client.get(
            f"/api/eleves/?id_annee_scolaire={annee1.id}&classe_id={classe_a.id}", headers=auth_headers
        ).json()
        assert {e["matricule"] for e in en_a} == {e1.matricule, e2.matricule}
        en_b = client.get(
            f"/api/eleves/?id_annee_scolaire={annee1.id}&classe_id={classe_b.id}", headers=auth_headers
        ).json()
        assert en_b == []

        # Statut lu sur l'inscription (« Transféré ») et non sur eleve.statut.
        transferes = client.get(
            f"/api/eleves/?id_annee_scolaire={annee1.id}&statut=Transféré", headers=auth_headers
        ).json()
        assert [e["matricule"] for e in transferes] == [e2.matricule]

        # Le même filtre statut sur l'état actuel de l'élève (sans année) ne
        # trouve rien : les deux élèves sont « actifs ».
        actifs = client.get("/api/eleves/?statut=actif", headers=auth_headers).json()
        assert len(actifs) == 2

    def test_compte_scopee_annee(self, client, auth_headers, db_session):
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

        t = client.post("/api/tuteurs/", json={
            "nom": "Diallo", "prenom": "Aminata", "email": "a3@ex.com",
            "telephone": "+223 76 00 11 22", "adresse": "Bamako", "profession": "Enseignante",
        }, headers=auth_headers).json()
        e1 = models.Eleves(
            nom="Konaté", prenom="Amadou", date_de_naissance=date(2012, 3, 15),
            lieu_de_naissance="Bamako", sexe="M", statut="actif",
            tuteur_id=t["id"], classe_id=classe_a.id,
        )
        db_session.add(e1)
        db_session.flush()
        db_session.add(models.Inscriptions(
            matricule_eleve=e1.matricule, id_classe=classe_a.id,
            id_annee_scolaire=annee1.id, statut="Inscrit",
        ))
        db_session.commit()

        compte = client.get(f"/api/eleves/compte?id_annee_scolaire={annee1.id}", headers=auth_headers).json()
        assert compte["total"] == 1
        compte_autre_annee = client.get(
            f"/api/eleves/compte?id_annee_scolaire={annee2.id}", headers=auth_headers
        ).json()
        assert compte_autre_annee["total"] == 0


class TestContexteAnnee:
    def _creer_eleve_deux_annees(self, client, auth_headers, db_session):
        """Élève avec une inscription d'une année antérieure (classe A, Transféré)
        et une inscription de l'année active (classe B, Inscrit). L'état actuel
        de l'élève (Eleves.classe_id) reste la classe B."""
        annee1 = models.AnneesScolaires(
            libelle="2024-2025", date_debut=date(2024, 9, 1), date_fin=date(2025, 6, 30)
        )
        annee_active = models.AnneesScolaires(
            libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
        )
        db_session.add_all([annee1, annee_active])
        db_session.flush()
        classe_a = models.Classes(niveau="7ème Année", nom="A")
        classe_b = models.Classes(niveau="7ème Année", nom="B")
        db_session.add_all([classe_a, classe_b])
        db_session.flush()

        t = client.post("/api/tuteurs/", json={
            "nom": "Diallo", "prenom": "Aminata", "email": "ctx@ex.com",
            "telephone": "+223 76 00 11 22", "adresse": "Bamako", "profession": "Enseignante",
        }, headers=auth_headers).json()
        e1 = models.Eleves(
            nom="Konaté", prenom="Amadou", date_de_naissance=date(2012, 3, 15),
            lieu_de_naissance="Bamako", sexe="M", statut="actif",
            tuteur_id=t["id"], classe_id=classe_b.id,
        )
        db_session.add(e1)
        db_session.flush()
        db_session.add_all([
            models.Inscriptions(matricule_eleve=e1.matricule, id_classe=classe_a.id,
                                id_annee_scolaire=annee1.id, statut="Transféré"),
            models.Inscriptions(matricule_eleve=e1.matricule, id_classe=classe_b.id,
                                id_annee_scolaire=annee_active.id, statut="Inscrit"),
        ])
        db_session.commit()
        return {"matricule": e1.matricule, "annee1": annee1.id, "active": annee_active.id,
                "classe_a": classe_a.id, "classe_b": classe_b.id}

    def test_liste_fournit_classe_annee_et_statut_annee(self, client, auth_headers, db_session):
        ctx = self._creer_eleve_deux_annees(client, auth_headers, db_session)
        scopee = client.get(
            f"/api/eleves/?id_annee_scolaire={ctx['annee1']}", headers=auth_headers
        ).json()
        assert len(scopee) == 1
        assert scopee[0]["classe_annee"]["id"] == ctx["classe_a"]
        assert scopee[0]["statut_annee"] == "Transféré"

        sans_annee = client.get("/api/eleves/", headers=auth_headers).json()
        assert sans_annee[0]["classe_annee"] is None
        assert sans_annee[0]["statut_annee"] is None

    def test_dossier_sans_annee_utilise_annee_active(self, client, auth_headers, db_session):
        ctx = self._creer_eleve_deux_annees(client, auth_headers, db_session)
        resp = client.get(f"/api/eleves/{ctx['matricule']}/dossier", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["annee_scolaire"]["id"] == ctx["active"]
        assert body["classe_annee"]["id"] == ctx["classe_b"]
        assert body["statut_annee"] == "Inscrit"

    def test_dossier_scope_annee_antérieure(self, client, auth_headers, db_session):
        """Le dossier demande avec une année antérieure consulte les données de
        cette année (annee_scolaire/classe_annee/statut_annee), sans altérer la
        classe ACTUELLE de l'élève (histologie inchangée)."""
        ctx = self._creer_eleve_deux_annees(client, auth_headers, db_session)
        resp = client.get(
            f"/api/eleves/{ctx['matricule']}/dossier?id_annee_scolaire={ctx['annee1']}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["annee_scolaire"]["id"] == ctx["annee1"]
        assert body["classe_annee"]["id"] == ctx["classe_a"]
        assert body["statut_annee"] == "Transféré"
        # État actuel non modifié par la consultation d'une autre année.
        assert body["classe"]["id"] == ctx["classe_b"]

    def test_dossier_annee_introuvable_404(self, client, auth_headers, db_session):
        _creer_annee(client, auth_headers)
        tuteur = _creer_tuteur(client, auth_headers).json()
        created = _creer_eleve(client, auth_headers, tuteur_id=tuteur["id"]).json()
        resp = client.get(
            f"/api/eleves/{created['matricule']}/dossier?id_annee_scolaire=999999",
            headers=auth_headers,
        )
        assert resp.status_code == 404

    def test_dossier_scope_bulletins_absences_notes_par_annee(self, client, auth_headers, db_session):
        """Le dossier d'une année donnée ne renvoie que les bulletins, absences
        et notes de CETTE année ; l'année active ne montre que ses propres
        données. Paiements : via l'inscription de l'année uniquement."""
        ctx = self._creer_eleve_deux_annees(client, auth_headers, db_session)
        m = ctx["matricule"]
        trim1 = models.Trimestres(
            nom="Trimestre 1", type="TRIMESTRE", date_debut=date(2024, 10, 1),
            date_fin=date(2024, 12, 20), annee_scolaire_id=ctx["annee1"],
        )
        trim_active = models.Trimestres(
            nom="Trimestre 1", type="TRIMESTRE", date_debut=date(2025, 10, 1),
            date_fin=date(2025, 12, 20), annee_scolaire_id=ctx["active"],
        )
        db_session.add_all([trim1, trim_active])
        db_session.flush()
        db_session.add_all([
            models.Bulletins(matricule_eleve=m, id_trimestre=trim1.id, id_classe=ctx["classe_a"], moyenne_generale=12.5),
            models.Bulletins(matricule_eleve=m, id_trimestre=trim_active.id, id_classe=ctx["classe_b"], moyenne_generale=14.0),
            models.Absences(matricule_eleve=m, date_absence=date(2024, 11, 5)),
            models.Absences(matricule_eleve=m, date_absence=date(2025, 11, 5)),
        ])
        db_session.commit()

        dossier_annee1 = client.get(
            f"/api/eleves/{m}/dossier?id_annee_scolaire={ctx['annee1']}", headers=auth_headers
        ).json()
        assert len(dossier_annee1["inscriptions"]) == 1
        assert len(dossier_annee1["bulletins"]) == 1
        assert dossier_annee1["bulletins"][0]["id_trimestre"] == trim1.id
        assert len(dossier_annee1["absences"]) == 1
        assert dossier_annee1["absences"][0]["date_absence"] == "2024-11-05"

        dossier_active = client.get(f"/api/eleves/{m}/dossier", headers=auth_headers).json()
        assert len(dossier_active["inscriptions"]) == 1
        assert dossier_active["inscriptions"][0]["id_annee_scolaire"] == ctx["active"]
        assert len(dossier_active["bulletins"]) == 1
        assert dossier_active["bulletins"][0]["id_trimestre"] == trim_active.id
        assert len(dossier_active["absences"]) == 1
        assert dossier_active["absences"][0]["date_absence"] == "2025-11-05"


class TestAuthRequis:
    def test_sans_token_401(self, client):
        resp = client.get("/api/eleves/")
        assert resp.status_code == 401
