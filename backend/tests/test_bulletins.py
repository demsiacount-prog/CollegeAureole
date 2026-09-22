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


def test_bulletin_utilise_classe_de_l_annee_du_trimestre(db_session):
    """Régressions : la classe d'un bulletin est celle de l'INSCRIPTION de
    l'année du trimestre, jamais Eleves.classe_id (classe ACTUELLE de l'élève).

    Un élève qui a changé de classe depuis doit retrouver l'ancien bulletin
    avec les coefficients et le barème de son ancienne classe.
    """
    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")  # 2025-2026
    s = _Seed(db_session, "7ème", periode)
    s.ajouter_note(s.cours[0][0], 16.0)
    s.ajouter_note(s.cours[1][0], 12.0)
    s.ajouter_note(s.cours[2][0], 10.0)

    # L'élève a depuis changé de classe : classe B en 2026-2027.
    annee2 = models.AnneesScolaires(
        libelle="2026-2027", date_debut=date(2026, 9, 1), date_fin=date(2027, 6, 30), active=True
    )
    db_session.add(annee2)
    db_session.flush()
    classe_b = models.Classes(niveau="7ème", nom="7ème B", frais_inscription=0, mensualite=0)
    db_session.add(classe_b)
    db_session.flush()

    # Inscription de l'élève en 2025-2026 dans la classe A : source de vérité.
    db_session.add(models.Inscriptions(
        matricule_eleve=s.eleve.matricule,
        id_classe=s.classe.id,
        id_annee_scolaire=periode.annee_scolaire_id,
        statut="Inscrit",
    ))
    s.eleve.classe_id = classe_b.id
    db_session.commit()

    calcul = _calculer_bulletin(db_session, s.eleve.matricule, periode.id)
    assert calcul["id_classe"] == s.classe.id  # classe de l'année 1, pas la B
    details = {d["id_cours"]: d["coefficient"] for d in calcul["details"]}
    assert details[s.cours[0][0].id] == 4.0  # coefficients de la classe A
    # Moyenne pondérée avec les coefficients A (4, 4, 3) : (16*4+12*4+10*3)/11.
    assert calcul["moyenne_generale"] == round(142 / 11, 2)


def test_generation_classe_union_inscription_et_effectifs(db_session):
    """L'effectif de génération d'une classe pour un trimestre est l'UNION des
    inscriptions de (classe, année du trimestre) et des élèves actuellement
    dans la classe — jamais uniquement les inscriptions, ni uniquement la
    classe actuelle.

    - élève inscrit en A pour l'année du trimestre → inclus ;
    - élève dans A aujourd'hui mais SANS inscription de l'année (données
      incomplètes) → inclus (régressions si on le perd) ;
    - élève passé en classe B l'année suivante → exclu de A.
    """
    from schemas import BulletinGenerateClasseRequest
    from routers.bulletins import generer_bulletins_classe

    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")  # 2025-2026
    annee1 = (
        db_session.query(models.AnneesScolaires)
        .filter(models.AnneesScolaires.id == periode.annee_scolaire_id)
        .first()
    )
    s = _Seed(db_session, "4ème", periode)

    # Élève 1 : inscrit en A pour l'année du trimestre.
    db_session.add(models.Inscriptions(
        matricule_eleve=s.eleve.matricule, id_classe=s.classe.id,
        id_annee_scolaire=annee1.id, statut="Inscrit",
    ))
    s.ajouter_note(s.cours[0][0], 8.0)
    s.ajouter_note(s.cours[1][0], 7.0)
    s.ajouter_note(s.cours[2][0], 6.0)

    # Élève 2 : dans la classe A aujourd'hui, sans inscription 2025-2026.
    eleve2 = models.Eleves(
        nom="Diallo", prenom="Moussa", date_de_naissance=date(2012, 1, 1),
        lieu_de_naissance="Dakar", sexe="M", statut="actif",
        tuteur_id=s.tuteur.id, classe_id=s.classe.id,
    )
    db_session.add(eleve2)
    db_session.flush()
    for cours, _ in s.cours:
        db_session.add(models.Notes(
            date=date.today(), note=8.0, matricule_eleve=eleve2.matricule,
            id_cours=cours.id, id_classe=s.classe.id,
            matricule_enseignant=s.enseignant.matricule, id_trimestre=periode.id,
        ))

    # Élève 3 : passé en classe B l'année suivante → ne doit pas figurer en A.
    annee2 = models.AnneesScolaires(
        libelle="2026-2027", date_debut=date(2026, 9, 1), date_fin=date(2027, 6, 30), active=True
    )
    db_session.add(annee2)
    db_session.flush()
    classe_b = models.Classes(niveau="4ème", nom="4ème B", frais_inscription=0, mensualite=0)
    db_session.add(classe_b)
    db_session.flush()
    eleve3 = models.Eleves(
        nom="Ka", prenom="Binta", date_de_naissance=date(2012, 2, 2),
        lieu_de_naissance="Thiès", sexe="F", statut="actif",
        tuteur_id=s.tuteur.id, classe_id=classe_b.id,
    )
    db_session.add(eleve3)
    db_session.flush()
    db_session.add(models.Inscriptions(
        matricule_eleve=eleve3.matricule, id_classe=classe_b.id,
        id_annee_scolaire=annee2.id, statut="Inscrit",
    ))
    db_session.commit()

    resultats = generer_bulletins_classe(
        BulletinGenerateClasseRequest(id_classe=s.classe.id, id_trimestre=periode.id), db_session
    )
    matricules = sorted(r.matricule_eleve for r in resultats.bulletins)
    assert s.eleve.matricule in matricules
    assert eleve2.matricule in matricules
    assert eleve3.matricule not in matricules
    assert resultats.erreurs == []


def test_bulletin_annuel_utilise_classe_inscription_annee(db_session):
    """Bulletin annuel : la classe affichée et les agrégats utilisent la classe
    de l'année demandée (inscription), même après un changement de classe."""
    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")
    annee = (
        db_session.query(models.AnneesScolaires)
        .filter(models.AnneesScolaires.id == periode.annee_scolaire_id)
        .first()
    )
    s = _Seed(db_session, "Seconde", periode)
    s.ajouter_note(s.cours[0][0], 16.0)
    s.ajouter_note(s.cours[1][0], 12.0)
    s.ajouter_note(s.cours[2][0], 10.0)
    db_session.add(models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=periode.id, id_classe=s.classe.id,
        moyenne_generale=12.5, rang=1, statut="PUBLIE",
    ))

    # Changement de classe l'année suivante (classe B active).
    annee2 = models.AnneesScolaires(
        libelle="2026-2027", date_debut=date(2026, 9, 1), date_fin=date(2027, 6, 30), active=True
    )
    db_session.add(annee2)
    db_session.flush()
    classe_b = models.Classes(niveau="Première", nom="1ère B", frais_inscription=0, mensualite=0)
    db_session.add(classe_b)
    db_session.flush()
    db_session.add(models.Inscriptions(
        matricule_eleve=s.eleve.matricule,
        id_classe=s.classe.id,
        id_annee_scolaire=annee.id,
        statut="Inscrit",
    ))
    s.eleve.classe_id = classe_b.id
    db_session.commit()

    payload = bulletin_annuel(db_session, s.eleve.matricule, annee.id)
    assert payload["classe"]["id"] == s.classe.id
    assert payload["classe"]["nom"] == s.classe.nom
    assert payload["officiel"] is False  # Seconde → liste dynamique


def test_coefficient_nul_moyenne_generale_none_persistee(db_session):
    """Aucune matière coefficientée (coefficient 0) → moyenne None, pas un 0.0
    fallacieux, et le bulletin est DÉSORMAIS ENREGISTRÉ tel quel (colonne
    `moyenne_generale` désormais nullable)."""
    from routers.bulletins import _upsert_bulletin

    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")
    s = _Seed(db_session, "7ème", periode)
    db_session.query(models.AffectationCoursClasse).update({"coefficient": 0.0})
    s.ajouter_note(s.cours[0][0], 16.0)
    s.ajouter_note(s.cours[1][0], 12.0)
    s.ajouter_note(s.cours[2][0], 10.0)
    db_session.commit()

    calcul = _calculer_bulletin(db_session, s.eleve.matricule, periode.id)
    assert calcul["moyenne_generale"] is None
    assert calcul["appreciation"] is None

    bulletin = _upsert_bulletin(db_session, calcul)
    db_session.commit()
    db_session.refresh(bulletin)
    assert bulletin.moyenne_generale is None
    assert len(bulletin.details) == 3
    # Toujours aucun 0.0 falsifié en base.
    assert bulletin.moyenne_generale != 0.0


def test_generation_par_classe_partielle_documente_les_erreurs(db_session):
    """Bug 3 : la génération par classe retourne une réponse structurée avec
    les élèves en échec (motif), jamais une liste qui les masque."""
    from schemas import BulletinGenerateClasseRequest
    from routers.bulletins import generer_bulletins_classe

    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")
    s = _Seed(db_session, "7ème", periode)
    s.ajouter_note(s.cours[0][0], 16.0)
    s.ajouter_note(s.cours[1][0], 12.0)
    s.ajouter_note(s.cours[2][0], 10.0)

    # Élève 2 : dans la classe (classe_id) mais AUCUNE note → échec documenté.
    eleve2 = models.Eleves(
        nom="Diallo", prenom="Moussa", date_de_naissance=date(2012, 1, 1),
        lieu_de_naissance="Dakar", sexe="M", statut="actif",
        tuteur_id=s.tuteur.id, classe_id=s.classe.id,
    )
    db_session.add(eleve2)
    db_session.commit()

    resultats = generer_bulletins_classe(
        BulletinGenerateClasseRequest(id_classe=s.classe.id, id_trimestre=periode.id), db_session
    )
    assert resultats.nb_succes == 1
    assert resultats.nb_erreurs == 1
    assert [r.matricule_eleve for r in resultats.bulletins] == [s.eleve.matricule]
    assert resultats.erreurs[0].matricule_eleve == eleve2.matricule
    assert resultats.erreurs[0].motif  # motif explicite (Aucune note / notes manquantes)


def test_rangs_uniquement_pour_bulletins_publies(db_session):
    """Bug 5 : seuls les bulletins PUBLIÉS portent un rang ; les brouillons
    gardent rang=None. Le classement affiché = version officielle."""
    from routers.bulletins import _calculer_rangs_classe

    periode = _periode(db_session, "1er Trimestre", "TRIMESTRE")
    s = _Seed(db_session, "7ème", periode)

    publie = models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=periode.id, id_classe=s.classe.id,
        moyenne_generale=12.0, statut="PUBLIE",
    )
    db_session.add(publie)
    # Brouillon : un AUTRE élève de la même classe (contrainte d'unicité bulletin/trimestre).
    eleve2 = models.Eleves(
        nom="Diallo", prenom="Moussa", date_de_naissance=date(2012, 1, 1),
        lieu_de_naissance="Dakar", sexe="M", statut="actif",
        tuteur_id=s.tuteur.id, classe_id=s.classe.id,
    )
    db_session.add(eleve2)
    db_session.flush()
    brouillon = models.Bulletins(
        matricule_eleve=eleve2.matricule, id_trimestre=periode.id, id_classe=s.classe.id,
        moyenne_generale=15.0, statut="BROUILLON",
    )
    db_session.add(brouillon)
    db_session.commit()

    _calculer_rangs_classe(db_session, s.classe.id, periode.id)
    db_session.commit()
    db_session.expire_all()

    publie = (
        db_session.query(models.Bulletins)
        .filter(models.Bulletins.id == publie.id).first()
    )
    brouillon = (
        db_session.query(models.Bulletins)
        .filter(models.Bulletins.id == brouillon.id).first()
    )
    assert publie.rang == 1
    assert brouillon.rang is None


def test_publier_depublier_verrouille_annee_cloturee(db_session):
    """Bug 4 : publier/dépublier est refusé (409) si l'année du trimestre est clôturée."""
    from schemas import BulletinPublierRequest
    from routers.bulletins import publier_bulletins_classe, depublier_bulletins_classe

    annee = models.AnneesScolaires(
        libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30),
        active=True, cloturee=True,
    )
    db_session.add(annee)
    db_session.flush()
    t = models.Trimestres(
        nom="1er Trimestre", type="TRIMESTRE",
        date_debut=date(2025, 9, 1), date_fin=date(2025, 12, 20),
        annee_scolaire_id=annee.id,
    )
    db_session.add(t)
    db_session.commit()
    payload = BulletinPublierRequest(id_classe=1, id_trimestre=t.id)

    for fn in (publier_bulletins_classe, depublier_bulletins_classe):
        try:
            fn(payload, db_session)
        except HTTPException as exc:
            assert exc.status_code == 409
        else:
            raise AssertionError("Un refus 409 était attendu")


def test_liste_filtre_par_annee(db_session, client, auth_headers):
    """GET /api/bulletins/ accepte `id_annee_scolaire` (alias de `annee_id`) :
    consultation d'une année passée stricte, sans casser les appels existants."""
    annee1 = models.AnneesScolaires(
        libelle="2023-2024", date_debut=date(2023, 9, 1), date_fin=date(2024, 6, 30), active=True
    )
    annee2 = models.AnneesScolaires(
        libelle="2024-2025", date_debut=date(2024, 9, 1), date_fin=date(2025, 6, 30), active=False
    )
    db_session.add_all([annee1, annee2])
    db_session.flush()
    t1 = models.Trimestres(
        nom="1er Trimestre", type="TRIMESTRE",
        date_debut=date(2023, 9, 1), date_fin=date(2023, 12, 20), annee_scolaire_id=annee1.id,
    )
    t2 = models.Trimestres(
        nom="1er Trimestre", type="TRIMESTRE",
        date_debut=date(2024, 9, 1), date_fin=date(2024, 12, 20), annee_scolaire_id=annee2.id,
    )
    db_session.add_all([t1, t2])
    db_session.flush()
    s = _Seed(db_session, "7ème", t1)
    db_session.add(models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=t1.id, id_classe=s.classe.id,
        moyenne_generale=12.0, rang=1, statut="BROUILLON",
    ))
    db_session.add(models.Bulletins(
        matricule_eleve=s.eleve.matricule, id_trimestre=t2.id, id_classe=s.classe.id,
        moyenne_generale=15.0, rang=1, statut="BROUILLON",
    ))
    db_session.commit()

    resp = client.get("/api/bulletins/", params={"id_annee_scolaire": annee1.id}, headers=auth_headers)
    assert resp.status_code == 200
    assert [b["moyenne_generale"] for b in resp.json()] == [12.0]
    resp = client.get("/api/bulletins/", params={"annee_id": annee2.id}, headers=auth_headers)
    assert [b["moyenne_generale"] for b in resp.json()] == [15.0]
    # Sans filtre année, les autres filtres continuent de fonctionner.
    resp = client.get("/api/bulletins/", params={"id_classe": s.classe.id}, headers=auth_headers)
    assert {b["moyenne_generale"] for b in resp.json()} == {12.0, 15.0}

