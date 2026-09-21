"""Tests des correctifs de robustesse (sauvegardes, restauration, reset/purge
protégés, durabilité SQLite, verifier_eleve, alertes de clôture, AUTO_CREATE)."""
import io
import os
import zipfile
from datetime import date
from pathlib import Path
from unittest import mock

import pytest

import models
from database import Base
from services import protections, sauvegardes
from services.sauvegardes import (
    construire_archive, construire_classeur_export, ecrire_sauvegarde,
    lister_sauvegardes, restaurer, sauvegarde_auto,
)

# ── Fix 5 : PRAGMA de durabilité ────────────────────────────────────────────


def test_pragma_durabilite_database_py():
    """database.py doit forcer FULL par défaut et journal WAL."""
    import inspect
    import database as module_database

    contenu = inspect.getsource(module_database)
    assert "synchronous=FULL" in contenu
    assert "journal_mode=WAL" in contenu
    assert "busy_timeout" in contenu
    assert "SQLITE_SYNCHRONOUS" in contenu


# ── Fix 6 : verifier_eleve ──────────────────────────────────────────────────


def _creer_tuteur(db_session):
    t = models.Tuteurs(nom="T", prenom="T", email="t@x.com", telephone="+2230000", adresse="B", profession="M")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


def _creer_eleve(db_session, tuteur_id):
    e = models.Eleves(
        nom="Konaté", prenom="Amadou", date_de_naissance=date(2015, 2, 1),
        lieu_de_naissance="Bamako", sexe="M", tuteur_id=tuteur_id,
    )
    db_session.add(e)
    db_session.commit()
    db_session.refresh(e)
    return e


def test_verifier_eleve_sans_historique_passe(db_session):
    tuteur = _creer_tuteur(db_session)
    eleve = _creer_eleve(db_session, tuteur.id)
    protections.verifier_eleve(db_session, eleve.matricule)


def test_verifier_eleve_avec_inscription_bloque(db_session):
    from fastapi import HTTPException

    tuteur = _creer_tuteur(db_session)
    eleve = _creer_eleve(db_session, tuteur.id)
    annee = models.AnneesScolaires(
        libelle="2025-2026", active=True, cloturee=False,
        date_debut=date(2025, 9, 1), date_fin=date(2026, 6, 30),
    )
    db_session.add(annee)
    db_session.commit()
    db_session.add(models.Inscriptions(
        matricule_eleve=eleve.matricule, id_annee_scolaire=annee.id, statut="Inscrit",
    ))
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        protections.verifier_eleve(db_session, eleve.matricule)
    assert exc.value.status_code == 409
    assert "inscription" in exc.value.detail


# ── Export/Import symétrique (Fix 1/3/4) ────────────────────────────────────

@pytest.fixture()
def jeu_donnees(client, auth_headers, db_session):
    """Un minimum de données réalistes : année, tuteur, élève, inscription,
    document joint + un fichier uploadé."""
    annee = client.post("/api/anneesScolaires/", json={
        "libelle": "2025-2026", "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers).json()
    tuteur = client.post("/api/tuteurs/", json={
        "nom": "T", "prenom": "T", "email": "t@x.com",
        "telephone": "+22376000000", "adresse": "Bamako", "profession": "M",
    }, headers=auth_headers).json()
    eleve = client.post("/api/eleves/", json={
        "nom": "Konaté", "prenom": "Amadou",
        "date_de_naissance": "2015-02-01", "lieu_de_naissance": "Bamako",
        "sexe": "M", "tuteur_id": tuteur["id"],
    }, headers=auth_headers).json()

    contenu_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n%%EOF\n"
    doc = client.post(
        "/api/documents/",
        headers=auth_headers,
        data={"entite_type": "eleve", "entite_id": eleve["matricule"], "categorie": "naissance"},
        files={"fichier": ("acte.pdf", contenu_pdf, "application/pdf")},
    )
    assert doc.status_code in (200, 201), doc.text
    doc = doc.json()
    return {"eleve": eleve, "document_id": doc["id"], "contenu_pdf": contenu_pdf}


def test_export_complet_contient_documents_et_uploads(client, auth_headers, jeu_donnees, tmp_path, monkeypatch):
    monkeypatch.setenv("AUREOLE_UPLOADS_DIR", str(tmp_path / "uploads"))
    racine = tmp_path / "uploads"
    (racine / "logos").mkdir(parents=True)
    (racine / "logos" / "logo_test.png").write_bytes(b"logo")

    resp = client.get("/api/import-export/export/complet", headers=auth_headers)
    assert resp.status_code == 200
    contenu = resp.content
    zf = zipfile.ZipFile(io.BytesIO(contenu))
    noms = zf.namelist()
    assert "donnees.xlsx" in noms
    assert "manifest.json" in noms
    assert any(n.startswith("documents/") for n in noms), "BLOB des documents manquant"
    assert "uploads/logos/logo_test.png" in noms, "uploads/ manquant dans l'archive"
    doc_membre = next(n for n in noms if n.startswith("documents/"))
    assert zf.read(doc_membre) == jeu_donnees["contenu_pdf"]
    zf.close()


def test_dossier_sauvegardes_colocalise_uploads(tmp_path, monkeypatch):
    """Sans AUREOLE_SAUVEGARDES_DIR, les sauvegardes vont dans un dossier frère
    du dossier des uploads (même emplacement persistant et inscriptible)."""
    monkeypatch.setenv("AUREOLE_UPLOADS_DIR", str(tmp_path / "uploads"))
    os.environ.pop("AUREOLE_SAUVEGARDES_DIR", None)

    dossier = sauvegardes._dossier_sauvegardes()
    assert dossier == tmp_path / "sauvegardes"
    assert dossier.is_dir()
    assert dossier.parent.is_dir()

    sujet = dossier / "test_ecriture.zip"
    sujet.write_bytes(b"x")
    assert sujet.exists()


def test_export_complet_reste_disponible_si_archivage_disque_echoue(
    client, auth_headers, jeu_donnees, monkeypatch
):
    """Le téléchargement .zip doit fonctionner même si l'écriture serveur
    échoue (dossier sauvegardes/ inaccessible) : cause du « erreur interne »
    au clic sur « Télécharger la sauvegarde »."""
    def ecriture_en_echec(*args, **kwargs):
        raise OSError("EACCES: permission denied")
    monkeypatch.setattr(sauvegardes, "ecrire_sauvegarde", ecriture_en_echec)

    resp = client.get("/api/import-export/export/complet", headers=auth_headers)
    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    assert "donnees.xlsx" in zf.namelist()
    zf.close()


def test_creer_sauvegarde_erreur_explicite_si_dossier_inaccessible(
    client, auth_headers, monkeypatch
):
    """POST /sauvegarde doit remonter une erreur claire (500 détaillé), pas une
    erreur interne muette, quand le dossier de sauvegarde est inscriptible."""
    def ecriture_en_echec(*args, **kwargs):
        raise OSError("EACCES: permission denied")
    monkeypatch.setattr(sauvegardes, "ecrire_sauvegarde", ecriture_en_echec)

    resp = client.post("/api/import-export/sauvegarde", headers=auth_headers)
    assert resp.status_code == 500
    assert "sauvegardes" in resp.json()["detail"].lower()


def test_sauvegarde_disque_rotation(db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("SAUVEGARDES_MAX", "2")
    tuteur = _creer_tuteur(db_session)
    _creer_eleve(db_session, tuteur.id)

    premier = ecrire_sauvegarde(db_session, dossier=tmp_path)
    assert premier.exists()
    ecrire_sauvegarde(db_session, dossier=tmp_path)
    ecrire_sauvegarde(db_session, dossier=tmp_path)

    restants = lister_sauvegardes(dossier=tmp_path)
    assert len(restants) == 2, "rotation non appliquée"
    assert "nom" in restants[0] and "taille_octets" in restants[0]


def test_sauvegarde_auto_idempotente(db_session, tmp_path):
    tuteur = _creer_tuteur(db_session)
    _creer_eleve(db_session, tuteur.id)
    with mock.patch.dict(os.environ, {"SAUVEGARDES_FREQUENCE_H": "24"}):
        premier = sauvegarde_auto(db_session, dossier=tmp_path)
    assert premier is not None
    nouveau = sauvegarde_auto(db_session, dossier=tmp_path)
    assert nouveau is None, "aucune nouvelle sauvegarde si récente"


def test_import_restaure_transactionnel(client, auth_headers, jeu_donnees, db_session):
    """Export complet → purge de la table → import → les données reviennent
    à l'identique (y compris le BLOB du document)."""
    resp = client.get("/api/import-export/export/complet", headers=auth_headers)
    assert resp.status_code == 200
    archive = resp.content

    # Vidage complet volontaire sur la base du client (on recommence de zéro).
    # Le compte admin est conservé : nécessaire pour rester authentifié
    # jusqu'à l'import (qui, lui, purge tout avant de restaurer).
    for tablename, modele in reversed(sauvegardes._TABLES):
        if tablename == "utilisateurs":
            continue
        db_session.execute(modele.__table__.delete())
    db_session.commit()

    rep = client.post(
        "/api/import-export/import",
        headers={**auth_headers, "X-Confirm": "RESTAURATION-DONNEES"},
        data={"remplacer": "true"},
        files={"fichier": ("sauvegarde.zip", archive, "application/zip")},
    )
    assert rep.status_code == 200, rep.text
    body = rep.json()
    assert body["lignes_importees"] > 0

    depuis_db = client.get(f"/api/eleves/{jeu_donnees['eleve']['matricule']}", headers=auth_headers)
    assert depuis_db.status_code == 200
    assert depuis_db.json()["nom"] == "Konaté"

    # Le document BLOB a bien été restauré.
    docs = db_session.query(models.Documents).all()
    assert docs
    assert docs[0].contenu == jeu_donnees["contenu_pdf"]


def test_restauration_rejette_zip_slip(client, auth_headers, jeu_donnees, tmp_path, monkeypatch):
    """Une archive contrefaite avec des chemins remontants (../, absolu) ne
    doit jamais écrire hors du dossier uploads (écriture arbitraire)."""
    cible = tmp_path / "uploads"
    cible.mkdir(exist_ok=True)
    monkeypatch.setattr(sauvegardes, "_upl_uploads", lambda: cible)

    resp = client.get("/api/import-export/export/complet", headers=auth_headers)
    assert resp.status_code == 200
    archive = resp.content

    # On ajoute des membres piégés à une archive valide.
    with io.BytesIO() as tampon:
        with zipfile.ZipFile(tampon, "w") as zf:
            with zipfile.ZipFile(io.BytesIO(archive)) as src:
                for membre in src.namelist():
                    zf.writestr(membre, src.read(membre))
            zf.writestr("uploads/../../fuite.txt", b"PWNED")
            zf.writestr("uploads//tmp/absolu.txt", b"PWNED")
        archive_piegee = tampon.getvalue()

    rep = client.post(
        "/api/import-export/import",
        headers={**auth_headers, "X-Confirm": "RESTAURATION-DONNEES"},
        data={"remplacer": "true"},
        files={"fichier": ("pirate.zip", archive_piegee, "application/zip")},
    )
    assert rep.status_code == 400
    assert not (tmp_path / "fuite.txt").exists()
    assert not Path("/tmp/absolu.txt").exists()
    assert not list(cible.rglob("fuite.txt"))


def test_import_refuse_sans_confirmation(client, auth_headers, jeu_donnees):
    resp = client.get("/api/import-export/export/complet", headers=auth_headers)
    archive = resp.content

    sans_confirm = client.post(
        "/api/import-export/import",
        headers=auth_headers,
        data={"remplacer": "true"},
        files={"fichier": ("s.zip", archive, "application/zip")},
    )
    assert sans_confirm.status_code == 400

    sans_remplacer = client.post(
        "/api/import-export/import",
        headers={**auth_headers, "X-Confirm": "RESTAURATION-DONNEES"},
        data={"remplacer": "false"},
        files={"fichier": ("s.zip", archive, "application/zip")},
    )
    assert sans_remplacer.status_code == 400


# ── Fix 2 : reset/purge sauvegardent avant destruction ──────────────────────

def _moteurs_sur_bdd_test(monkeypatch, db_session):
    """Branche les moteurs internes de /api/setup sur la base de test.

    En production reset/purge partagent un même fichier SQLite (engine app,
    SessionLocal et moteur Alembic). En mémoire de test ce sont des bases
    distinctes, ce qui fausserait le drop/recréation : on aligne donc
    `setup.engine`/`SessionLocal`/`migrer_schema` sur la base du client.
    """
    import routers.setup as setup
    from sqlalchemy.orm import Session

    moteur = db_session.get_bind()
    monkeypatch.setattr(setup, "engine", moteur)
    monkeypatch.setattr(setup, "SessionLocal", lambda: Session(bind=moteur))
    monkeypatch.setattr(setup, "migrer_schema", lambda: Base.metadata.create_all(bind=moteur))


def test_reset_cree_sauvegarde_avant_drop(client, auth_headers, db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("AUREOLE_SAUVEGARDES_DIR", str(tmp_path))
    _moteurs_sur_bdd_test(monkeypatch, db_session)
    tuteur = _creer_tuteur(db_session)
    _creer_eleve(db_session, tuteur.id)

    resp = client.post("/api/setup/reset", json={"confirm": True}, headers=auth_headers)
    assert resp.status_code == 200
    archives = lister_sauvegardes(dossier=tmp_path)
    assert archives, "aucune sauvegarde créée avant reset"
    assert archives[0]["nom"].startswith("collegeaureole_sauvegarde_")


def test_purge_donnees_cree_sauvegarde(client, auth_headers, db_session, tmp_path, monkeypatch):
    monkeypatch.setenv("AUREOLE_SAUVEGARDES_DIR", str(tmp_path))
    _moteurs_sur_bdd_test(monkeypatch, db_session)
    tuteur = _creer_tuteur(db_session)
    _creer_eleve(db_session, tuteur.id)

    resp = client.post(
        "/api/setup/purge-donnees",
        json={"confirm": True},
        headers={**auth_headers, "X-Confirm": "PURGE-DONNEES"},
    )
    assert resp.status_code == 200, resp.text
    assert lister_sauvegardes(dossier=tmp_path)


# ── Fix 7 : alertes de clôture ──────────────────────────────────────────────

def _cloture_sans_classe_suivante(client, auth_headers, db_session):
    annee = client.post("/api/anneesScolaires/", json={
        "libelle": "2025-2026", "date_debut": "2025-09-01",
        "date_fin": "2026-06-30", "active": True,
    }, headers=auth_headers).json()
    tuteur = _creer_tuteur(db_session)
    eleve = _creer_eleve(db_session, tuteur.id)
    eleve.classe_relation = models.Classes(niveau="Grande Section", nom="A")
    db_session.add(eleve.classe_relation)
    db_session.commit()
    db_session.refresh(eleve.classe_relation)
    client.post("/api/inscriptions/", json={
        "matricule_eleve": eleve.matricule,
        "id_classe": eleve.classe_relation.id,
        "id_annee_scolaire": annee["id"],
    }, headers=auth_headers)
    db_session.query(models.Inscriptions).filter(
        models.Inscriptions.id_annee_scolaire == annee["id"]
    ).update({"statut_passage": "ADMIS"})
    db_session.commit()
    return annee


def test_preview_signale_classes_manquantes(client, auth_headers, db_session):
    _cloture_sans_classe_suivante(client, auth_headers, db_session)
    preview = client.get("/api/cloture/preview", headers=auth_headers)
    assert preview.status_code == 200
    body = preview.json()
    assert body["nb_classes_manquantes"] == 1
    eleve_prevu = next(e for e in body["eleves"] if e["classe_manquante"])
    assert eleve_prevu["statut_passage"] == "ADMIS"


def test_cloture_persiste_alerte_et_liste(client, auth_headers, db_session):
    _cloture_sans_classe_suivante(client, auth_headers, db_session)
    resp = client.post("/api/cloture/executer", json={
        "nouvelle_annee": {"libelle": "2026-2027", "date_debut": "2026-09-01", "date_fin": "2027-06-30"},
    }, headers=auth_headers)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rapport"]["nb_erreurs"] == 1

    alertes = client.get("/api/cloture/alertes", headers=auth_headers)
    assert alertes.status_code == 200
    payload = alertes.json()
    assert payload["nb_en_attente"] == 1
    assert "Classe suivante introuvable" in payload["alertes"][0]["motif"]

    alerte_id = payload["alertes"][0]["id"]
    resolu = client.post(f"/api/cloture/alertes/{alerte_id}/resoudre", headers=auth_headers)
    assert resolu.status_code == 200
    assert resolu.json()["resolue"] is True
    assert lister_apres(client, auth_headers) == 0


def lister_apres(client, auth_headers):
    return client.get("/api/cloture/alertes", headers=auth_headers).json()["nb_en_attente"]


# ── Fix 8 : AUTO_CREATE_TABLES désactivé par défaut ─────────────────────────

def test_auto_create_tables_false_par_defaut(monkeypatch):
    from main import _auto_create_tables_actif

    monkeypatch.delenv("AUTO_CREATE_TABLES", raising=False)
    assert _auto_create_tables_actif() is False

    monkeypatch.setenv("AUTO_CREATE_TABLES", "true")
    assert _auto_create_tables_actif() is True

    monkeypatch.setenv("AUTO_CREATE_TABLES", "0")
    assert _auto_create_tables_actif() is False