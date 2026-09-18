"""Tests du registre de notes (synthèse élève × période pour une matière)."""
from datetime import date

import models
from services.registre_notes import registre_notes


def _contexte(db, niveau: str):
    """Année, 3 périodes, classe, cours et élève notés sur chaque période."""
    annee = models.AnneesScolaires(
        libelle="2025-2026", date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30), active=True
    )
    db.add(annee)
    db.flush()

    type_periode = "COMPOSITION" if niveau in ("1ère Année", "5ème Année") else "TRIMESTRE"
    periodes = []
    for i, nom in enumerate(("1er Trimestre", "2e Trimestre", "3e Trimestre"), start=1):
        t = models.Trimestres(
            nom=nom, type=type_periode,
            date_debut=date(2025, 9, 1), date_fin=date(2025, 12, 20),
            annee_scolaire_id=annee.id,
        )
        db.add(t)
        periodes.append(t)
    db.flush()

    classe = models.Classes(
        niveau=niveau, nom=f"{niveau} A", frais_inscription=0, mensualite=0
    )
    db.add(classe)
    db.flush()

    enseignant = models.Enseignants(
        matricule="ENS0099", nom="Ndiaye", prenom="Cheikh",
        email="cheikh.ndiaye@test.com", telephone="0102030406",
        adresse="Test", specialite="Maths",
    )
    db.add(enseignant)
    db.flush()

    tuteur = models.Tuteurs(
        nom="Paul", prenom="Marc", email="marc.paul@test.com",
        telephone="0102030405", adresse="Test", profession="Commerçant",
    )
    db.add(tuteur)
    db.flush()

    eleve = models.Eleves(
        matricule="EL209901", nom="Diop", prenom="Awa",
        date_de_naissance=date(2012, 5, 5), lieu_de_naissance="Dakar",
        sexe="F", statut="actif", tuteur_id=tuteur.id, classe_id=classe.id,
    )
    db.add(eleve)
    db.flush()

    cours = models.Cours(
        nom="Mathématiques", description="", volume_horaire=4,
        matricule_enseignant=enseignant.matricule,
    )
    db.add(cours)
    db.flush()
    ef1 = niveau in ("1ère Année", "5ème Année")
    db.add(models.AffectationCoursClasse(
        id_classe=classe.id, id_cours=cours.id, coefficient=1.0 if ef1 else 2.0,
    ))
    db.flush()
    return {"annee": annee, "periodes": periodes, "classe": classe, "cours": cours, "eleve": eleve}


def test_registre_60_40_et_moyenne_annuelle(db_session):
    """Registre 7ème : note classe/comp, moyenne 60/40, moyenne annuelle."""
    ctx = _contexte(db_session, "7ème Année")
    e, c, t1, t2, t3 = ctx["eleve"], ctx["cours"], *ctx["periodes"]

    db_session.add(models.Notes(
        date=date.today(), note=16.0, note_classe=10.0,
        matricule_eleve=e.matricule, id_cours=c.id, id_classe=ctx["classe"].id,
        matricule_enseignant="ENS0099", id_trimestre=t1.id,
    ))
    db_session.add(models.Notes(
        date=date.today(), note=15.0, note_classe=11.0,
        matricule_eleve=e.matricule, id_cours=c.id, id_classe=ctx["classe"].id,
        matricule_enseignant="ENS0099", id_trimestre=t2.id,
    ))
    db_session.add(models.Notes(
        date=date.today(), note=14.0, note_classe=12.0,
        matricule_eleve=e.matricule, id_cours=c.id, id_classe=ctx["classe"].id,
        matricule_enseignant="ENS0099", id_trimestre=t3.id,
    ))
    db_session.commit()

    payload = registre_notes(db_session, ctx["classe"].id, c.id, ctx["annee"].id)
    assert payload["bareme"] == 20
    assert payload["cours"]["coefficient"] == 2.0
    assert [t["nom"] for t in payload["trimestres"]] == ["1er Trimestre", "2e Trimestre", "3e Trimestre"]
    assert len(payload["eleves"]) == 1

    ligne = payload["eleves"][0]
    assert len(ligne["lignes"]) == 3
    # 60 % comp + 40 % classe
    assert ligne["lignes"][0]["moyenne"] == round(0.6 * 16 + 0.4 * 10, 2)   # 13.6
    assert ligne["lignes"][1]["moyenne"] == round(0.6 * 15 + 0.4 * 11, 2)   # 13.4
    assert ligne["lignes"][2]["moyenne"] == round(0.6 * 14 + 0.4 * 12, 2)   # 13.2
    # Coefficient appliqué (7ème → TRIMESTRE coefficienté)
    assert ligne["lignes"][0]["points"] == round(13.6 * 2, 2)               # 27.2
    assert ligne["moyenne_annuelle"] == round((13.6 + 13.4 + 13.2) / 3, 2)  # 13.4


def test_registre_sans_note_classe_retombe_sur_comp(db_session):
    ctx = _contexte(db_session, "7ème Année")
    e, c, t1 = ctx["eleve"], ctx["cours"], ctx["periodes"][0]
    db_session.add(models.Notes(
        date=date.today(), note=10.0,
        matricule_eleve=e.matricule, id_cours=c.id, id_classe=ctx["classe"].id,
        matricule_enseignant="ENS0099", id_trimestre=t1.id,
    ))
    db_session.commit()

    payload = registre_notes(db_session, ctx["classe"].id, c.id, ctx["annee"].id)
    ligne = payload["eleves"][0]["lignes"][0]
    assert ligne["note_classe"] is None
    assert ligne["moyenne"] == 10.0


def test_registre_ef1_compositions_sur_10(db_session):
    """1ère Année : uniquement les compositions, barème /10, coefficient 1.0."""
    ctx = _contexte(db_session, "1ère Année")
    e, c, t1 = ctx["eleve"], ctx["cours"], ctx["periodes"][0]
    db_session.add(models.Notes(
        date=date.today(), note=8.0, note_classe=7.0,
        matricule_eleve=e.matricule, id_cours=c.id, id_classe=ctx["classe"].id,
        matricule_enseignant="ENS0099", id_trimestre=t1.id,
    ))
    db_session.commit()

    payload = registre_notes(db_session, ctx["classe"].id, c.id, ctx["annee"].id)
    assert payload["bareme"] == 10
    assert payload["cours"]["coefficient"] == 1.0
    assert all(t.type == "COMPOSITION" for t in ctx["periodes"])
    ligne = payload["eleves"][0]["lignes"]
    assert ligne[0]["moyenne"] == round(0.6 * 8 + 0.4 * 7, 2)
    # COMPOSITION → pas de coefficient
    assert ligne[0]["points"] == ligne[0]["moyenne"]


def test_registre_manque_une_periode_et_classe_introuvable(db_session):
    ctx = _contexte(db_session, "7ème Année")
    e, c, t1 = ctx["eleve"], ctx["cours"], ctx["periodes"][0]
    db_session.add(models.Notes(
        date=date.today(), note=12.0,
        matricule_eleve=e.matricule, id_cours=c.id, id_classe=ctx["classe"].id,
        matricule_enseignant="ENS0099", id_trimestre=t1.id,
    ))
    db_session.commit()

    payload = registre_notes(db_session, ctx["classe"].id, c.id, ctx["annee"].id)
    lignes = payload["eleves"][0]["lignes"]
    assert lignes[0]["moyenne"] == 12.0
    assert all(l["moyenne"] is None for l in lignes[1:])
    assert payload["eleves"][0]["moyenne_annuelle"] == 12.0

    try:
        registre_notes(db_session, 99999, c.id, ctx["annee"].id)
    except ValueError:
        pass
    else:
        raise AssertionError("Classe introuvable attendue")


def test_registre_jardin_refuse(db_session):
    ctx = _contexte(db_session, "Grande Section")
    try:
        registre_notes(db_session, ctx["classe"].id, ctx["cours"].id, ctx["annee"].id)
    except ValueError as exc:
        assert "jardin" in str(exc).lower() or "appréciation" in str(exc).lower()
    else:
        raise AssertionError("Jardin refusé attendu")
