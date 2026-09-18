"""Tests d'intégration du routeur Rapports & Documents.

Couvre l'acte de naissance, la fiche de suivi au second cycle (7è/8è/9è), le
rapport des moyennes annuelles, la proposition de passage et le seul PDF
conservé côté rapports : le relevé de notes (fiche de notes/compositions).
Les classes de jardin d'enfants n'ont pas de notes chiffrées ni de passage.
"""
from datetime import date

import models


class _Seed:
    """Petite instanciation : une année active (2 trimestres), une classe EF2,
    une 9ème (transfert), une classe de jardin, deux élèves notés, un élève
    jardin et un historique d'une année pour le parcours."""

    def __init__(self, db):
        self.db = db
        self.annee = models.AnneesScolaires(
            libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
        )
        self.annee_prev = models.AnneesScolaires(
            libelle="2024-2025", date_debut=date(2024, 9, 1), date_fin=date(2025, 6, 30), active=False
        )
        db.add_all([self.annee, self.annee_prev])
        db.flush()

        self.t1 = models.Trimestres(
            nom="Trimestre 1", type="TRIMESTRE",
            date_debut=date(2025, 9, 1), date_fin=date(2025, 12, 20),
            annee_scolaire_id=self.annee.id,
        )
        self.t2 = models.Trimestres(
            nom="Trimestre 2", type="TRIMESTRE",
            date_debut=date(2026, 1, 5), date_fin=date(2026, 3, 30),
            annee_scolaire_id=self.annee.id,
        )
        self.t_prev = models.Trimestres(
            nom="Trimestre 1", type="TRIMESTRE",
            date_debut=date(2024, 9, 1), date_fin=date(2024, 12, 20),
            annee_scolaire_id=self.annee_prev.id,
        )
        db.add_all([self.t1, self.t2, self.t_prev])
        db.flush()

        self.classe_ef2 = models.Classes(niveau="7ème Année", nom="EF2-A", frais_inscription=0, mensualite=0)
        self.classe_9 = models.Classes(niveau="9ème Année", nom="EF2-C", frais_inscription=0, mensualite=0)
        self.classe_jardin = models.Classes(niveau="Petite Section", nom="PG", frais_inscription=0, mensualite=0)
        db.add_all([self.classe_ef2, self.classe_9, self.classe_jardin])
        db.flush()

        self.tuteur = models.Tuteurs(
            nom="Paul", prenom="Marc", email="marc.paul@test.com",
            telephone="0102030405", adresse="Bamako", profession="Commerçant",
        )
        db.add(self.tuteur)
        db.flush()

        self.enseignant = models.Enseignants(
            matricule="ENS0001", nom="Ndiaye", prenom="Cheikh",
            email="cheikh.ndiaye@test.com", telephone="0102030406",
            adresse="Bamako", specialite="Maths",
        )
        db.add(self.enseignant)
        db.flush()

        self.maths = models.Cours(
            nom="Mathématiques", description="Cours de maths", volume_horaire=4,
            matricule_enseignant=self.enseignant.matricule,
        )
        self.francais = models.Cours(
            nom="Français", description="Cours de français", volume_horaire=3,
            matricule_enseignant=self.enseignant.matricule,
        )
        db.add_all([self.maths, self.francais])
        db.flush()

        self.eleve_a = models.Eleves(
            matricule="EL202501", nom="Diop", prenom="Awa",
            date_de_naissance=date(2012, 5, 5), lieu_de_naissance="Bamako",
            sexe="F", statut="actif", tuteur_id=self.tuteur.id, classe_id=self.classe_ef2.id,
        )
        self.eleve_b = models.Eleves(
            matricule="EL202502", nom="Traore", prenom="Moussa",
            date_de_naissance=date(2012, 8, 12), lieu_de_naissance="Ségou",
            sexe="M", statut="actif", tuteur_id=self.tuteur.id, classe_id=self.classe_ef2.id,
        )
        self.eleve_j = models.Eleves(
            matricule="EL202503", nom="Keita", prenom="Fatou",
            date_de_naissance=date(2019, 3, 2), lieu_de_naissance="Bamako",
            sexe="F", statut="actif", tuteur_id=self.tuteur.id, classe_id=self.classe_jardin.id,
            nom_pere="Keita", prenom_pere="Modibo", fonction_pere="Commerçant",
            nom_mere="Coulibaly", prenom_mere="Aminata", fonction_mere="Ménagère",
        )
        self.eleve_9 = models.Eleves(
            matricule="EL202504", nom="Sissoko", prenom="Oumar",
            date_de_naissance=date(2009, 11, 1), lieu_de_naissance="Mopti",
            sexe="M", statut="actif", tuteur_id=self.tuteur.id, classe_id=self.classe_9.id,
            nom_pere="Sissoko", prenom_pere="Bakary", fonction_pere="Commerçant",
            nom_mere="Diarra", prenom_mere="Fanta", fonction_mere="Ménagère",
        )
        db.add_all([self.eleve_a, self.eleve_b, self.eleve_j, self.eleve_9])
        db.flush()

        self.mat_a = self.eleve_a.matricule
        self.mat_b = self.eleve_b.matricule
        self.mat_j = self.eleve_j.matricule
        self.mat_9 = self.eleve_9.matricule

        for eleve, classe in [
            (self.eleve_a, self.classe_ef2),
            (self.eleve_b, self.classe_ef2),
            (self.eleve_j, self.classe_jardin),
            (self.eleve_9, self.classe_9),
        ]:
            db.add(models.Inscriptions(
                matricule_eleve=eleve.matricule, id_classe=classe.id,
                id_annee_scolaire=self.annee.id,
            ))
        db.add(models.Inscriptions(
            matricule_eleve=self.eleve_a.matricule, id_classe=self.classe_ef2.id,
            id_annee_scolaire=self.annee_prev.id, statut_passage="ADMIS",
        ))
        db.flush()

        self.ajouter_bulletin(self.t1, self.eleve_a.matricule, 15.0)
        self.ajouter_bulletin(self.t2, self.eleve_a.matricule, 15.0)
        self.ajouter_bulletin(self.t1, self.eleve_b.matricule, 13.0)
        self.ajouter_bulletin(self.t2, self.eleve_b.matricule, 13.0)
        self.ajouter_bulletin(self.t1, self.eleve_9.matricule, 12.0)
        self.ajouter_bulletin(self.t_prev, self.eleve_a.matricule, 14.0)

        self.ajouter_note(self.t1, self.eleve_a.matricule, self.maths.id, 14.0)
        self.ajouter_note(self.t2, self.eleve_a.matricule, self.maths.id, 16.0)
        self.ajouter_note(self.t1, self.eleve_a.matricule, self.francais.id, 15.0)
        self.ajouter_note(self.t2, self.eleve_a.matricule, self.francais.id, 15.0)
        self.ajouter_note(self.t1, self.eleve_9.matricule, self.maths.id, 12.0)

        self.ajouter_absence(self.eleve_a.matricule, date(2025, 10, 3), justifiee=True)
        self.ajouter_absence(self.eleve_a.matricule, date(2026, 2, 10), justifiee=False)
        self.ajouter_absence(self.eleve_9.matricule, date(2025, 11, 15), justifiee=True)
        db.flush()

    def ajouter_bulletin(self, trimestre, matricule, moyenne):
        bulletin = models.Bulletins(
            matricule_eleve=matricule, id_trimestre=trimestre.id,
            id_classe=self._classe_de(matricule).id,
            moyenne_generale=moyenne, statut="BROUILLON",
        )
        self.db.add(bulletin)
        self.db.flush()
        self.db.add(models.BulletinDetails(
            id_bulletin=bulletin.id, id_cours=self.maths.id,
            moyenne=moyenne, coefficient=1.0,
        ))

    def _classe_de(self, matricule):
        return {
            self.mat_a: self.classe_ef2,
            self.mat_b: self.classe_ef2,
            self.mat_j: self.classe_jardin,
            self.mat_9: self.classe_9,
        }[matricule]

    def ajouter_note(self, trimestre, matricule, id_cours, note):
        self.db.add(models.Notes(
            date=trimestre.date_debut, note=note,
            matricule_eleve=matricule, id_cours=id_cours,
            id_classe=self.classe_ef2.id, matricule_enseignant=self.enseignant.matricule,
            id_trimestre=trimestre.id,
        ))

    def ajouter_absence(self, matricule, date_absence, justifiee):
        self.db.add(models.Absences(
            matricule_eleve=matricule, date_absence=date_absence, justifiee=justifiee,
        ))


class TestFicheSuivi:
    def test_fiche_9eme_transfert_vrai(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(f"/api/rapports/eleves/{s.mat_9}/fiche-suivi", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transfert"] is True
        assert data["moyenne_annuelle"] == 12.0
        assert data["est_jardin"] is False
        assert data["date_de_naissance"] == "2009-11-01"
        assert data["pere"] == "Bakary Sissoko"
        assert data["mere"] == "Fanta Diarra"

    def test_fiche_9eme_parcours_et_absences(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(f"/api/rapports/eleves/{s.mat_9}/fiche-suivi", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transfert"] is True
        assert data["nb_absences"] == 1
        assert data["nb_absences_justifiees"] == 1
        assert data["nb_absences_injustifiees"] == 0
        assert len(data["moyennes_trimestres"]) == 2
        matieres = {m["matiere"]: m["moyenne"] for m in data["notes_par_matiere"]}
        assert matieres == {"Mathématiques": 12.0}
        annees_parcours = [p["annee_label"] for p in data["parcours"]]
        assert annees_parcours == ["2025-2026"]

    def test_fiche_9eme_grille_officielle(self, client, auth_headers, db_session):
        """La grille reproduit le formulaire officiel : 7 matières fixes, le cadre
        fixe 23 colonnes (7 périodes × 18 trimestres, la colonne hachurée et
        les 3 colonnes "Fois"), la zone Tendance, l'orientation et les remarques
        officielles."""
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(f"/api/rapports/eleves/{s.mat_9}/fiche-suivi", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()

        # Le cadrillage officiel : 7 périodes fixes, sous-colonnes 3/3/3/3/2/2/2.
        assert [c["label"] for c in data["colonnes"]] == [
            "7ème 1ère Fois", "7ème 2ème Fois", "8ème 1ère Fois", "8ème 2ème Fois",
            "9ème 1ère Fois", "9ème 2ème Fois", "9ème 3ème Fois",
        ]
        assert [len(c["moyennes"]) for c in data["colonnes"]] == [3, 3, 3, 3, 2, 2, 2]
        assert [c["effectue"] for c in data["colonnes"]] == [False] * 4 + [True] + [False] * 2
        assert data["fois_x"] == 1

        # Un seul passage réel : 9ème 1ère Fois (2 trimestres notes dans la base).
        col = data["colonnes"][4]
        assert col["niveau"] == "9ème Année"
        assert col["passage"] == 1
        assert col["annee_label"] == "2025-2026"
        assert col["moyennes"] == [12.0, None]

        assert [m["matiere"] for m in data["lignes"]] == [
            "Rédaction", "Dictée et Questions", "Histoire-Géographie", "Langue",
            "Mathématiques", "Physique-Chimie", "Sciences Naturelles",
        ]
        # Chaque ligne vaut 18 cellules de notes alignées sur la grille.
        assert all(len(m["valeurs"]) == 18 for m in data["lignes"])
        maths = next(m for m in data["lignes"] if m["matiere"] == "Mathématiques")
        assert maths["valeurs"] == [None] * 12 + [12.0, None] + [None] * 4
        # Un seul passage disponible : pas encore de flèche de tendance.
        assert maths["tendance"] is None
        # Aucune matière littéraire renseignée : orientation indéterminée.
        assert data["orientation"] is None
        assert data["remarques"] == [
            "En aucun cas, la fiche ne sera remise ni à l'élève ni à ses parents ;",
            "En cas de changement d'établissement, cette fiche sera transmise au Directeur de CAP qui reçoit l'élève ;",
            "Cette fiche ne doit comporte aucune surcharge ni rature sous peine de nullité ;",
            "La non production de cette fiche entraine la non orientation de l'élève ;",
            "Lorsque l'élève est admis au DEF, envoyer la fiche à l'Académie de l'enseignement immédiatement après les résultats.",
        ]

    def test_fiche_7eme_accessible(self, client, auth_headers, db_session):
        """La fiche se délivre aussi aux élèves de 7ème et 8ème année."""
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(f"/api/rapports/eleves/{s.mat_a}/fiche-suivi", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["transfert"] is False
        assert data["colonnes"][0]["label"] == "7ème 1ère Fois"
        assert data["colonnes"][0]["effectue"] is True
        # La 9ème n'a jamais été suivie : colonnes vides.
        assert data["colonnes"][-1]["effectue"] is False
        assert all(v is None for v in data["lignes"][4]["valeurs"][16:])

    def test_fiche_refusee_hors_second_cycle(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        # Élève du jardin d'enfants : pas de fiche.
        resp = client.get(f"/api/rapports/eleves/{s.mat_j}/fiche-suivi", headers=auth_headers)
        assert resp.status_code == 403


class TestMoyennesAnnuelles:
    def test_rapport_par_classe(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get("/api/rapports/moyennes-annuelles", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["annee_label"] == "2025-2026"
        classes = {c["niveau"]: c for c in data["classes"]}
        assert "7ème Année" in classes
        ef2 = classes["7ème Année"]
        assert ef2["effectif"] == 2
        assert ef2["moyenne_classe"] == 14.0  # (15 + 13) / 2
        eleves = {e["matricule"]: e for e in ef2["eleves"]}
        assert eleves[s.mat_a]["moyenne_annuelle"] == 15.0
        assert eleves[s.mat_a]["rang"] == 1
        assert eleves[s.mat_b]["rang"] == 2

    def test_rapport_filtre_sur_une_classe(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get("/api/rapports/moyennes-annuelles?classe_id=1", headers=auth_headers)
        assert resp.status_code == 200
        classes = resp.json()["classes"]
        assert all(c["id_classe"] == 1 for c in classes)

    def test_toutes_classes_exclut_jardin(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get("/api/rapports/moyennes-annuelles", headers=auth_headers)
        assert resp.status_code == 200
        niveaux = [c["niveau"] for c in resp.json()["classes"]]
        assert "Petite Section" not in niveaux
        assert "7ème Année" in niveaux

    def test_jardin_refuse(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(
            f"/api/rapports/moyennes-annuelles?classe_id={s.classe_jardin.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestPropositionPassage:
    def test_proposition_et_exclusion_jardin(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get("/api/rapports/proposition-passage", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        niveaux = [c["niveau"] for c in data["classes"]]
        assert niveaux == ["7ème Année", "9ème Année"]  # jardin exclu
        ef2 = next(c for c in data["classes"] if c["niveau"] == "7ème Année")
        assert ef2["seuil"] == 10.0
        assert ef2["admis"] == 2
        assert ef2["recales"] == 0
        propositions = {e["matricule"]: e["proposition"] for e in ef2["eleves"]}
        assert propositions[s.mat_a] == "ADMIS"  # 15 ≥ 10
        assert propositions[s.mat_b] == "ADMIS"  # 13 ≥ 10
        nine = next(c for c in data["classes"] if c["niveau"] == "9ème Année")
        assert nine["est_fin_cycle"] is True

    def test_annees_passees_classe_depuis_historique(self, client, auth_headers, db_session):
        """Le nombre d'années dans la classe vient de l'historique des inscriptions."""
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get("/api/rapports/proposition-passage", headers=auth_headers)
        assert resp.status_code == 200
        ef2 = next(c for c in resp.json()["classes"] if c["niveau"] == "7ème Année")
        annees = {e["matricule"]: e["annees_passees_classe"] for e in ef2["eleves"]}
        # Élève A : même classe en 2024-2025 puis 2025-2026 → 2 ans.
        assert annees[s.mat_a] == 2
        # Élève B : première année dans la classe → 1 an.
        assert annees[s.mat_b] == 1

    def test_recale_conserve_son_statut(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.query(models.Inscriptions).filter(
            models.Inscriptions.matricule_eleve == s.mat_b
        ).update({"statut_passage": "RECALE"})
        db_session.commit()

        resp = client.get("/api/rapports/proposition-passage?classe_id=1", headers=auth_headers)
        assert resp.status_code == 200
        ef2 = resp.json()["classes"][0]
        propositions = {e["matricule"]: e["proposition"] for e in ef2["eleves"]}
        assert propositions[s.mat_b] == "RECALE"

    def test_jardin_refuse(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(
            f"/api/rapports/proposition-passage?classe_id={s.classe_jardin.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestClassement:
    def test_classement_par_classe(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get("/api/rapports/classement", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["annee_label"] == "2025-2026"
        classes = {c["niveau"]: c for c in data["classes"]}
        ef2 = classes["7ème Année"]
        assert ef2["effectif"] == 2
        assert ef2["moyenne_classe"] == 14.0
        eleves = ef2["eleves"]
        assert [e["matricule"] for e in eleves] == [s.mat_a, s.mat_b]
        assert [e["rang"] for e in eleves] == [1, 2]

    def test_classement_filtre_sur_une_classe(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(f"/api/rapports/classement?classe_id={s.classe_ef2.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert [c["niveau"] for c in data["classes"]] == ["7ème Année"]

    def test_classement_jardin_refuse(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(
            f"/api/rapports/classement?classe_id={s.classe_jardin.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestFicheRenseignements:
    def test_effectifs_par_niveau(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get("/api/rapports/fiche-renseignements", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["annee_label"] == "2025-2026"
        assert data["ecole"] == "Collège Auréole"

        # 3 lignes récapi presentes : titulaires, redoublants, exclus/transférés.
        lignes = {l["libelle"]: l for l in data["effectifs"]}
        assert set(lignes) == {"Titulaire / Adm.", "Redoublants", "Exclus / Transf."}

        # 7ème : 2 élèves (1 M, 1 F) dans 1 classe ; 9ème : 1 élève M.
        titulaires = lignes["Titulaire / Adm."]
        assert titulaires["sept"]["rc"] == 1
        assert titulaires["sept"]["garcons"] == 1
        assert titulaires["sept"]["filles"] == 1
        assert titulaires["sept"]["total"] == 2
        assert titulaires["neuf"]["rc"] == 1
        assert titulaires["neuf"]["total"] == 1
        # Le jardin d'enfants n'apparaît pas dans la fiche du 2nd cycle.
        assert titulaires["total"]["total"] == 3
        assert lignes["Redoublants"]["total"]["total"] == 0

    def test_personnel_enseignants(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get("/api/rapports/fiche-renseignements", headers=auth_headers)
        assert resp.status_code == 200
        personnel = resp.json()["personnel"]
        assert len(personnel) == 1
        assert personnel[0]["nom"] == "Ndiaye"
        assert personnel[0]["prenom"] == "Cheikh"


class TestFicheNotesCompositions:
    def _affecter(self, db, classe, cours, coefficient):
        db.add(models.AffectationCoursClasse(id_classe=classe.id, id_cours=cours.id, coefficient=coefficient))

    def test_notes_au_dernier_trimestre(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        self._affecter(db_session, s.classe_ef2, s.maths, 2.0)
        self._affecter(db_session, s.classe_ef2, s.francais, 1.0)
        db_session.commit()

        resp = client.get(
            f"/api/rapports/eleves/{s.mat_a}/fiche-notes-compositions",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["niveau"] == "7ème Année"
        assert data["classe"] == "7ème Année EF2-A"
        assert data["est_jardin"] is False
        assert data["annee_label"] == "2025-2026"

        matieres = {m["matiere"]: m for m in data["matieres"]}
        assert set(matieres) == {"Mathématiques", "Français"}
        # T2 : maths 16, français 15 (note de classe absente → composition fait foi).
        assert matieres["Mathématiques"]["note"] == 16.0
        assert matieres["Mathématiques"]["coef"] == 2.0
        assert matieres["Français"]["note"] == 15.0
        assert data["total_notes"] == 31.0
        assert data["moyenne"] == 15.5
        assert data["rang"] == 1
        assert data["effectif"] == 2
        # Annuel : (T1 14,5 + T2 15,5) / 2.
        assert data["moyenne_annuelle"] == 15.0
        assert data["rang_annuel"] == 1

    def test_trimestre_explicite(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        self._affecter(db_session, s.classe_ef2, s.maths, 1.0)
        self._affecter(db_session, s.classe_ef2, s.francais, 1.0)
        db_session.commit()

        resp = client.get(
            f"/api/rapports/eleves/{s.mat_a}/fiche-notes-compositions?trimestre_id={s.t1.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        matieres = {m["matiere"]: m["note"] for m in data["matieres"]}
        assert matieres == {"Mathématiques": 14.0, "Français": 15.0}
        assert data["moyenne"] == 14.5

    def test_notes_compositions_refusees_au_jardin(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(
            f"/api/rapports/eleves/{s.mat_j}/fiche-notes-compositions",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_partie_inexistante_hors_annee(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.commit()

        resp = client.get(
            f"/api/rapports/eleves/INCONNU/fiche-notes-compositions",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestFicheRenseignementsPremierCycle:
    def test_effectifs_1ere_et_personnels(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        classe_1ere = models.Classes(niveau="1ère Année", nom="EF1-A", frais_inscription=0, mensualite=0)
        db_session.add(classe_1ere)
        db_session.flush()
        eleve_1 = models.Eleves(
            matricule="EL202505", nom="Coulibaly", prenom="Mariam",
            date_de_naissance=date(2019, 4, 10), lieu_de_naissance="Bamako",
            sexe="F", statut="actif", tuteur_id=s.tuteur.id, classe_id=classe_1ere.id,
        )
        db_session.add(eleve_1)
        db_session.flush()
        db_session.add(models.Inscriptions(
            matricule_eleve=eleve_1.matricule, id_classe=classe_1ere.id,
            id_annee_scolaire=s.annee.id,
        ))
        admin = models.Enseignants(
            matricule="ENS0002", nom="Diallo", prenom="Adama",
            email="adama.diallo@test.com", telephone="0102030407",
            adresse="Bamako", specialite="Gestion",
            fonction="Secrétaire", diplome="DEF",
        )
        ens = models.Enseignants(
            matricule="ENS0003", nom="Koné", prenom="Boubacar",
            email="boubacar.kone@test.com", telephone="0102030408",
            adresse="Bamako", specialite="Toutes disciplines",
            categorie="MP 2-4", classe_tenue="1ère A", diplome="DEF",
        )
        db_session.add_all([admin, ens])
        db_session.commit()

        resp = client.get("/api/rapports/fiche-renseignements-premier-cycle", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["annee_label"] == "2025-2026"
        assert [l["libelle"] for l in data["effectifs"]] == [
            "Inscrits / Effectifs", "Redoublants (Red)", "Exclus (Excl)",
        ]
        ligne = data["effectifs"][0]
        assert ligne["annee_1"]["rc"] == 1
        assert ligne["annee_1"]["total"] == 1
        assert ligne["annee_1"]["filles"] == 1
        assert ligne["total"]["total"] == 1
        assert [p["nom"] for p in data["personnel_admin"]] == ["Diallo"]
        assert [p["nom"] for p in data["personnel_enseignant"]] == ["Koné", "Ndiaye"]
        assert data["personnel_enseignant"][0]["classe_tenue"] == "1ère A"

    def test_nb_redoublements_alimente_les_effectifs(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        classe_1ere = models.Classes(niveau="1ère Année", nom="EF1-A", frais_inscription=0, mensualite=0)
        db_session.add(classe_1ere)
        db_session.flush()
        eleve_r = models.Eleves(
            matricule="EL202506", nom="Sangaré", prenom="Ibrahim",
            date_de_naissance=date(2019, 6, 12), lieu_de_naissance="Bamako",
            sexe="M", statut="actif", tuteur_id=s.tuteur.id, classe_id=classe_1ere.id,
        )
        db_session.add(eleve_r)
        db_session.flush()
        db_session.add(models.Inscriptions(
            matricule_eleve=eleve_r.matricule, id_classe=classe_1ere.id,
            id_annee_scolaire=s.annee.id, nb_redoublements=2,
        ))
        db_session.commit()

        resp = client.get("/api/rapports/fiche-renseignements-premier-cycle", headers=auth_headers)
        assert resp.status_code == 200
        lignes = {l["libelle"]: l for l in resp.json()["effectifs"]}
        inscrits = lignes["Inscrits / Effectifs"]
        assert inscrits["annee_1"]["total"] == 1
        assert inscrits["annee_1"]["garcons"] == 1
        red = lignes["Redoublants (Red)"]
        assert red["annee_1"]["total"] == 1
        assert red["total"]["total"] == 1


class TestPDF:
    """Seul document PDF des rapports conservé : le relevé de notes (doc7)."""

    def _assert_pdf(self, path, client, auth_headers):
        resp = client.get(path, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF")
        assert "attachment; filename=" in resp.headers["content-disposition"]

    def test_pdf_fiche_notes_compositions(self, client, auth_headers, db_session):
        s = _Seed(db_session)
        db_session.add(models.AffectationCoursClasse(id_classe=s.classe_ef2.id, id_cours=s.maths.id, coefficient=1.0))
        db_session.commit()
        self._assert_pdf(f"/api/rapports/eleves/{s.mat_a}/fiche-notes-compositions/pdf", client, auth_headers)


class TestAuthRequis:
    def test_rapports_sans_token_401(self, client):
        assert client.get("/api/rapports/moyennes-annuelles").status_code == 401
        assert client.get("/api/rapports/classement").status_code == 401
        assert client.get("/api/rapports/fiche-renseignements").status_code == 401
        assert client.get("/api/rapports/fiche-renseignements-premier-cycle").status_code == 401
        assert client.get("/api/rapports/eleves/XL000000/fiche-notes-compositions").status_code == 401