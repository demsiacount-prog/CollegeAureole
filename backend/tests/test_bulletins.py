"""Tests du calcul des bulletins, et en particulier de la règle de la 6ème.

La 6ème est une classe spéciale du 1er cycle (barème /10) :
- les TRIMESTRES sont coefficientés (moyenne pondérée, toujours sur /10) ;
- les COMPOSITIONS restent en moyenne simple (coefficient 1.0).
Les autres classes d'EF1 (1ère-5ème) sont toujours en moyenne simple.
"""
from datetime import date
from fastapi import HTTPException

import models
from routers.bulletins import _calculer_bulletin
from services import pdf as pdf_service
from services.bulletins_annuels import bulletin_annuel


class _Seed:
    """Mini-grammaire : élève dans une classe (niveau donné) avec des notes."""

    def __init__(self, db, niveau: str, trimestre: models.Trimestres):
        self.db = db
        self.classe = models.Classes(
            niveau=niveau, nom=f"{niveau} A", frais_inscription=0, mensualite=0
        )
        db.add(self.classe)
        db.flush()

        self.enseignant = models.Enseignants(
            matricule="ENS0001", nom="Ndiaye", prenom="Cheikh",
            email="cheikh.ndiaye@test.com", telephone="0102030406",
            adresse="Test", specialite="Maths",
        )
        db.add(self.enseignant)
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

        self.cours = []
        for nom, coef in (("Rédaction", 4.0), ("Mathématique", 4.0), ("Physique – Chimie", 3.0)):
            c = models.Cours(
                nom=nom, description="", volume_horaire=3,
                matricule_enseignant=self.enseignant.matricule,
            )
            db.add(c)
            db.flush()
            db.add(models.AffectationCoursClasse(
                id_classe=self.classe.id, id_cours=c.id, coefficient=coef,
            ))
            db.flush()
            self.cours.append((c, coef))

        self.trimestre = trimestre

    def ajouter_note(self, cours, note, note_classe=None):
        self.db.add(models.Notes(
            date=date.today(), note=note, note_classe=note_classe,
            matricule_eleve=self.eleve.matricule, id_cours=cours.id,
            id_classe=self.classe.id, matricule_enseignant=self.enseignant.matricule,
            id_trimestre=self.trimestre.id,
        ))


def _periode(db, nom, type_periode):
    annee = models.AnneesScolaires(
        libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
    )
    db.add(annee)
    db.flush()
    t = models.Trimestres(
        nom=nom, type=type_periode,
        date_debut=date(2025, 9, 1), date_fin=date(2025, 12, 20),
        annee_scolaire_id=annee.id,
    )
    db.add(t)
    db.flush()
    return t


def test_6eme_trimestre_pondere_sur_10(db_session):
    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")
    s = _Seed(db_session, "6ème", periode)
    # Notes /10 avec coefficients (4, 4, 3) :
    # (8*4 + 7*4 + 6*3) / (4+4+3) = (32 + 28 + 18) / 11 = 78/11 ≈ 7.09
    s.ajouter_note(s.cours[0][0], 8.0)
    s.ajouter_note(s.cours[1][0], 7.0)
    s.ajouter_note(s.cours[2][0], 6.0)
    db_session.commit()

    calcul = _calculer_bulletin(db_session, s.eleve.matricule, periode.id)
    assert calcul["moyenne_generale"] == round(78 / 11, 2)  # ≈ 7.09 → 70,9 % → Bien
    assert calcul["appreciation"] == "Bien"
    # Les coefficients réels sont conservés dans les détails.
    details = {d["id_cours"]: d["coefficient"] for d in calcul["details"]}
    assert details[s.cours[0][0].id] == 4.0
    assert details[s.cours[2][0].id] == 3.0


def test_6eme_composition_moyenne_simple_sur_10(db_session):
    periode = _periode(db_session, "1ère Composition", "COMPOSITION")
    s = _Seed(db_session, "6ème", periode)
    # Compos. : moyenne simple /10, coefficients ignorés (forcés à 1.0).
    s.ajouter_note(s.cours[0][0], 8.0)
    s.ajouter_note(s.cours[1][0], 7.0)
    s.ajouter_note(s.cours[2][0], 6.0)
    db_session.commit()

    calcul = _calculer_bulletin(db_session, s.eleve.matricule, periode.id)
    assert calcul["moyenne_generale"] == round((8 + 7 + 6) / 3, 2)
    # Coefficients ramenés à 1.0 pour la composition.
    details = {d["id_cours"]: d["coefficient"] for d in calcul["details"]}
    assert all(coef == 1.0 for coef in details.values())


def test_5eme_moyenne_simple_sur_10(db_session):
    periode = _periode(db_session, "1ère Composition", "COMPOSITION")
    s = _Seed(db_session, "5ème", periode)
    s.ajouter_note(s.cours[0][0], 8.0)
    s.ajouter_note(s.cours[1][0], 7.0)
    s.ajouter_note(s.cours[2][0], 6.0)
    db_session.commit()

    calcul = _calculer_bulletin(db_session, s.eleve.matricule, periode.id)
    assert calcul["moyenne_generale"] == round((8 + 7 + 6) / 3, 2)


def test_ef2_bulletin_pondere_sur_20(db_session):
    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")
    s = _Seed(db_session, "7ème", periode)
    # Notes /20 avec coefficients (4, 4, 3) :
    # (16*4 + 12*4 + 10*3) / 11 = (64 + 48 + 30) / 11 = 142/11 ≈ 12.91
    s.ajouter_note(s.cours[0][0], 16.0)
    s.ajouter_note(s.cours[1][0], 12.0)
    s.ajouter_note(s.cours[2][0], 10.0)
    db_session.commit()

    calcul = _calculer_bulletin(db_session, s.eleve.matricule, periode.id)
    assert calcul["moyenne_generale"] == round(142 / 11, 2)
    details = {d["id_cours"]: d["coefficient"] for d in calcul["details"]}
    assert details[s.cours[0][0].id] == 4.0


def test_ef2_moyenne_matiere_60_40_comp_classe(db_session):
    """Moyenne matière = 60% note de composition + 40% note de classe.

    Avec note de classe absente, la note de composition fait foi.
    """
    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")
    s = _Seed(db_session, "7ème", periode)
    # Compos./classe : (16, 10), (12, 8), (10, absent) → moyennes 13.6, 10.4, 10.0
    s.ajouter_note(s.cours[0][0], 16.0, note_classe=10.0)
    s.ajouter_note(s.cours[1][0], 12.0, note_classe=8.0)
    s.ajouter_note(s.cours[2][0], 10.0)
    db_session.commit()

    calcul = _calculer_bulletin(db_session, s.eleve.matricule, periode.id)
    details = {d["id_cours"]: d for d in calcul["details"]}
    assert details[s.cours[0][0].id]["moyenne"] == round(0.6 * 16 + 0.4 * 10, 2)  # 13.6
    assert details[s.cours[1][0].id]["moyenne"] == round(0.6 * 12 + 0.4 * 8, 2)   # 10.4
    assert details[s.cours[2][0].id]["moyenne"] == 10.0  # fallback composition
    # (13.6*4 + 10.4*4 + 10.0*3) / 11 = 126 / 11
    assert calcul["moyenne_generale"] == round(126 / 11, 2)


def test_notes_manquantes_declenche_erreur(db_session):
    periode = _periode(db_session, "1ère Composition", "COMPOSITION")
    s = _Seed(db_session, "6ème", periode)
    # Seulement 2 matières notées sur 3 affectées.
    s.ajouter_note(s.cours[0][0], 8.0)
    s.ajouter_note(s.cours[1][0], 7.0)
    db_session.commit()

    try:
        _calculer_bulletin(db_session, s.eleve.matricule, periode.id)
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "Notes manquantes" in str(exc.detail)
    else:
        raise AssertionError("Une erreur de notes manquantes était attendue")


def test_bulletin_annuel_3_blocs(db_session):
    """Bulletin annuel : 3 blocs trimestriels, notes classe/comp, agrégats."""
    annee = models.AnneesScolaires(
        libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
    )
    db_session.add(annee)
    db_session.flush()
    t1 = models.Trimestres(
        nom="1er Trimestre", type="TRIMESTRE",
        date_debut=date(2025, 9, 1), date_fin=date(2025, 12, 20),
        annee_scolaire_id=annee.id,
    )
    t2 = models.Trimestres(
        nom="2e Trimestre", type="TRIMESTRE",
        date_debut=date(2026, 1, 5), date_fin=date(2026, 3, 30),
        annee_scolaire_id=annee.id,
    )
    t3 = models.Trimestres(
        nom="3e Trimestre", type="TRIMESTRE",
        date_debut=date(2026, 4, 6), date_fin=date(2026, 6, 30),
        annee_scolaire_id=annee.id,
    )
    db_session.add_all([t1, t2, t3])
    db_session.flush()

    s = _Seed(db_session, "7ème", t1)
    # Bloc T1 : (16, 10), (12, 8), (10 sans classe) → 13.6, 10.4, 10.0
    s.ajouter_note(s.cours[0][0], 16.0, note_classe=10.0)
    s.ajouter_note(s.cours[1][0], 12.0, note_classe=8.0)
    s.ajouter_note(s.cours[2][0], 10.0)

    s.trimestre = t2
    s.ajouter_note(s.cours[0][0], 15.0, note_classe=11.0)
    s.ajouter_note(s.cours[1][0], 11.0, note_classe=9.0)
    s.ajouter_note(s.cours[2][0], 12.0, note_classe=10.0)

    s.trimestre = t3
    s.ajouter_note(s.cours[0][0], 14.0, note_classe=12.0)
    s.ajouter_note(s.cours[1][0], 10.0, note_classe=8.0)
    s.ajouter_note(s.cours[2][0], 13.0, note_classe=11.0)

    # Bulletins trimestriels (moyennes quelconques pour rangs/agrégats).
    db_session.add(models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=t1.id, id_classe=s.classe.id,
        moyenne_generale=11.45, rang=1, statut="PUBLIE",
    ))
    db_session.add(models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=t2.id, id_classe=s.classe.id,
        moyenne_generale=12.0, rang=1, statut="PUBLIE",
    ))
    db_session.add(models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=t3.id, id_classe=s.classe.id,
        moyenne_generale=10.0, rang=1, statut="PUBLIE",
    ))
    db_session.commit()

    payload = bulletin_annuel(db_session, s.eleve.matricule, annee.id)
    assert payload["statut"] == "OK"
    assert payload["bareme"] == 20
    assert len(payload["trimestres"]) == 3

    # La 7ème utilise le bulletin officiel : 15 matières fixes dans l'ordre.
    assert payload["officiel"] is True
    bloc1 = payload["trimestres"][0]
    from services.bulletins_annuels import MATIERES_BULLETIN_OFFICIEL

    assert [l["cours_nom"] for l in bloc1["lignes"]] == [m[0] for m in MATIERES_BULLETIN_OFFICIEL]
    assert len(bloc1["lignes"]) == 15
    par_cours = {l["id_cours"]: l for l in bloc1["lignes"]}
    assert par_cours[s.cours[0][0].id]["moyenne"] == round(0.6 * 16 + 0.4 * 10, 2)  # 13.6
    assert par_cours[s.cours[2][0].id]["moyenne"] == 10.0
    assert par_cours[s.cours[0][0].id]["points"] == round(13.6 * 4, 2)             # 54.4
    assert bloc1["totaux_coefficients"] == 11
    assert bloc1["totaux_points"] == round(13.6 * 4 + 10.4 * 4 + 10.0 * 3, 2)       # 126.0
    assert bloc1["rang"] == 1
    assert bloc1["moyenne_premier"] == 11.45
    # Matières absentes du programme : coefficients officiels, valeurs vides.
    absent = next(l for l in bloc1["lignes"] if l["id_cours"] < 0)
    assert absent["moyenne"] is None
    coefs_officiels = {m[0]: m[1] for m in MATIERES_BULLETIN_OFFICIEL}
    assert absent["coefficient"] == coefs_officiels[absent["cours_nom"]]

    assert payload["moyenne_annuelle"] == round((11.45 + 12.0 + 10.0) / 3, 2)        # 11.15
    assert payload["rang_annuel"] == 1
    assert payload["mention_annuelle"] == "Passable"
    assert payload["decision"] == "Admis en classe supérieure"

def test_bulletin_annuel_non_officiel_ef1(db_session):
    """Les classes hors 6è-9è gardent la liste dynamique des matières."""
    annee = models.AnneesScolaires(
        libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
    )
    db_session.add(annee)
    db_session.flush()
    t1 = models.Trimestres(
        nom="1er Trimestre", type="TRIMESTRE",
        date_debut=date(2025, 9, 1), date_fin=date(2025, 12, 20),
        annee_scolaire_id=annee.id,
    )
    db_session.add(t1)
    db_session.flush()

    s = _Seed(db_session, "Seconde", t1)
    s.ajouter_note(s.cours[0][0], 16.0)
    s.ajouter_note(s.cours[1][0], 12.0)
    s.ajouter_note(s.cours[2][0], 10.0)
    db_session.add(models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=t1.id, id_classe=s.classe.id,
        moyenne_generale=12.5, rang=1, statut="PUBLIE",
    ))
    db_session.commit()

    payload = bulletin_annuel(db_session, s.eleve.matricule, annee.id)
    assert payload["officiel"] is False
    assert payload["bareme"] == 20
    # Liste dynamique (3 cours), pas de gabarit officiel.
    assert len(payload["trimestres"][0]["lignes"]) == 3
    noms = {l["cours_nom"] for l in payload["trimestres"][0]["lignes"]}
    assert noms == {"Rédaction", "Mathématique", "Physique – Chimie"}


def test_bulletin_officiel_pdf_portrait(db_session):
    """Le bulletin officiel (doc4) tient sur une page A4 portrait."""
    annee = models.AnneesScolaires(
        libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
    )
    db_session.add(annee)
    db_session.flush()
    t1 = models.Trimestres(
        nom="1er Trimestre", type="TRIMESTRE",
        date_debut=date(2025, 9, 1), date_fin=date(2025, 12, 20),
        annee_scolaire_id=annee.id,
    )
    db_session.add(t1)
    db_session.flush()

    s = _Seed(db_session, "7ème", t1)
    s.ajouter_note(s.cours[0][0], 16.0, note_classe=10.0)
    db_session.add(models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=t1.id, id_classe=s.classe.id,
        moyenne_generale=11.45, rang=1, statut="PUBLIE",
    ))
    db_session.commit()

    payload = bulletin_annuel(db_session, s.eleve.matricule, annee.id)
    assert payload["officiel"] is True
    contenu = pdf_service.bulletin_annuel_pdf(payload, None, "2025-2026")
    assert contenu.startswith(b"%PDF")
    # A4 portrait : largeur < hauteur
    import re
    medias = re.findall(rb"/MediaBox \[\s*0 0 ([\d.]+) ([\d.]+)\s*\]", contenu)
    assert medias, "MediaBox introuvable"
    largeur, hauteur = (float(v) for v in medias[0])
    assert hauteur > largeur
    assert round(largeur, 1) == 595.3  # largeur A4 portrait
