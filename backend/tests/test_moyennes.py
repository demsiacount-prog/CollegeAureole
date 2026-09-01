"""Tests d'intégration des calculs de moyennes (services/moyennes.py).

On seed une petite instanciation cohérente (année → trimestre → tuteur →
élève → classe → enseignant → cours → notes → bulletins) puis on vérifie les
trois fonctions de calcul partagées entre les routers eleves et resultats.
"""
from datetime import date

import models
from services.moyennes import (
    calculer_moyenne_annuelle,
    calculer_moyennes_par_trimestre,
    calculer_notes_par_matiere,
)


class _Seed:
    """Mini-grammaire de données pour un élève sur un an."""

    def __init__(self, db):
        self.db = db
        self.annee = models.AnneesScolaires(
            libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
        )
        db.add(self.annee)
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
        db.add_all([self.t1, self.t2])
        db.flush()

        self.classe = models.Classes(
            niveau="7ème Année", nom="EF2-A", frais_inscription=0, mensualite=0
        )
        db.add(self.classe)
        db.flush()

        self.tuteur = models.Tuteurs(
            nom="Paul", prenom="Marc", email="marc.paul@test.com",
            telephone="0102030405", adresse="Test", profession="Commerçant",
        )
        db.add(self.tuteur)
        db.flush()

        self.eleve = models.Eleves(
            matricule="EL202501", nom="Diop", prenom="Awa",
            date_de_naissance=date(2012, 5, 5), lieu_de_naissance="Dakar",
            sexe="F", statut="actif", tuteur_id=self.tuteur.id, classe_id=self.classe.id,
        )
        db.add(self.eleve)
        db.flush()

        self.enseignant = models.Enseignants(
            matricule="ENS0001", nom="Ndiaye", prenom="Cheikh",
            email="cheikh.ndiaye@test.com", telephone="0102030406",
            adresse="Test", specialite="Maths",
        )
        db.add(self.enseignant)
        db.flush()

        self.maths = models.Cours(
            nom="Mathématiques", description="Cours de maths", volume_horaire=4,
            matricule_enseignant=self.enseignant.matricule,
        )
        db.add(self.maths)
        self.francais = models.Cours(
            nom="Français", description="Cours de français", volume_horaire=3,
            matricule_enseignant=self.enseignant.matricule,
        )
        db.add(self.francais)
        db.flush()

    def ajouter_note(self, trimestre, cours, note):
        self.db.add(models.Notes(
            date=trimestre.date_debut, note=note,
            matricule_eleve=self.eleve.matricule, id_cours=cours.id,
            id_classe=self.classe.id, matricule_enseignant=self.enseignant.matricule,
            id_trimestre=trimestre.id,
        ))

    def ajouter_bulletin(self, trimestre, moyenne):
        self.db.add(models.Bulletins(
            matricule_eleve=self.eleve.matricule, id_trimestre=trimestre.id,
            id_classe=self.classe.id, moyenne_generale=moyenne, statut="BROUILLON",
        ))


def _setup(db):
    db.add_all([
        models.AnneesScolaires(libelle="2024-2025", date_debut=date(2024, 9, 1), date_fin=date(2025, 6, 30)),
    ])
    s = _Seed(db)
    db.flush()
    db.commit()
    return s


def test_moyenne_annuelle_moyenne_des_bulletins(db_session):
    s = _setup(db_session)
    s.ajouter_bulletin(s.t1, 15.0)
    s.ajouter_bulletin(s.t2, 13.0)
    db_session.commit()

    moy = calculer_moyenne_annuelle(db_session, s.eleve.matricule, s.annee.id)
    assert moy == 14.0


def test_moyenne_annuelle_sans_bulletin_renvoie_none(db_session):
    s = _setup(db_session)
    db_session.commit()
    assert calculer_moyenne_annuelle(db_session, s.eleve.matricule, s.annee.id) is None


def test_moyenne_annuelle_ignore_les_autres_annees(db_session):
    s = _setup(db_session)
    s.ajouter_bulletin(s.t1, 20.0)
    db_session.commit()
    # Une année sans bulletin pour cet élève → None.
    autre = db_session.query(models.AnneesScolaires).filter(models.AnneesScolaires.libelle == "2024-2025").one()
    assert calculer_moyenne_annuelle(db_session, s.eleve.matricule, autre.id) is None


def test_moyennes_par_trimestre(db_session):
    s = _setup(db_session)
    s.ajouter_bulletin(s.t1, 14.0)
    s.ajouter_bulletin(s.t2, 16.0)
    db_session.commit()

    resultat = calculer_moyennes_par_trimestre(db_session, s.eleve.matricule, s.annee.id)
    assert len(resultat) == 2
    moyennes = {r.periode: r.moyenne for r in resultat}
    assert moyennes["Trimestre 1"] == 14.0
    assert moyennes["Trimestre 2"] == 16.0


def test_notes_par_matiere_agrege_la_moyenne(db_session):
    s = _setup(db_session)
    # Une seule note par (élève, cours, trimestre) — contrainte d'unicité réelle.
    s.ajouter_note(s.t1, s.maths, 12.0)
    s.ajouter_note(s.t2, s.maths, 16.0)
    s.ajouter_note(s.t1, s.francais, 10.0)
    s.ajouter_note(s.t2, s.francais, 18.0)
    db_session.commit()

    matieres = calculer_notes_par_matiere(db_session, s.eleve.matricule, s.annee.id)
    par_matiere = {m.matiere: m for m in matieres}
    assert set(par_matiere) == {"Mathématiques", "Français"}
    assert par_matiere["Mathématiques"].nb_notes == 2
    assert par_matiere["Mathématiques"].moyenne == 14.0  # (12+16)/2
    assert par_matiere["Français"].nb_notes == 2
    assert par_matiere["Français"].moyenne == 14.0  # (10+18)/2


def test_notes_par_matiere_sans_notes_vide(db_session):
    s = _setup(db_session)
    db_session.commit()
    assert calculer_notes_par_matiere(db_session, s.eleve.matricule, s.annee.id) == []
