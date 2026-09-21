"""Sauvegarde et restauration complètes des données.

Remplace l'ancien export XLSX manuel, qui ignorait le contenu binaire des
documents et les fichiers téléversés (uploads/), et qui n'avait AUCUN pendant
d'import symétrique : une base corrompue ou supprimée par erreur était
irrécupérable sans intervention SQL manuelle.

Format d'archive ZIP autonome (fonctionne sur SQLite comme PostgreSQL) :
    ├─ donnees.xlsx          → un onglet par table (hors BLOB documents)
    ├─ documents/<id>_<nom>  → contenu binaire des pièces jointes
    ├─ uploads/…             → fichiers téléversés (logos, photos…)
    └─ manifest.json         → métadonnées (format, date, version, moteur)

Ce module centralise l'export, l'écriture disque avec rotation, la sauvegarde
automatique (démarrage, idempotente) et la restauration symétrique `restaurer`
purge puis ré-insert Core par table dans l'ordre de dépendance, y compris les
BLOB de documents et les fichiers uploads/.
"""
import io
import json
import logging
import os
import re
import zipfile
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook, load_workbook
from sqlalchemy import Date, DateTime, Integer, Time
from sqlalchemy.orm import Session

import models

logger = logging.getLogger("college_aureole")

FORMAT_ARCHIVE = 1

# Ordre d'export/import (respect des clés étrangères).
_TABLES = [
    ("etablissement", models.Etablissement),
    ("infrastructures", models.EtablissementInfrastructures),
    ("utilisateurs", models.Utilisateurs),
    ("annees_scolaires", models.AnneesScolaires),
    ("trimestres", models.Trimestres),
    ("tuteurs", models.Tuteurs),
    ("enseignants", models.Enseignants),
    ("salles", models.Salles),
    ("classes", models.Classes),
    ("cours", models.Cours),
    ("classe_cours", models.AffectationCoursClasse),
    ("eleves", models.Eleves),
    ("inscriptions", models.Inscriptions),
    ("echeances", models.Echeances),
    ("paiements", models.Paiements),
    ("remises", models.Remises),
    ("notes", models.Notes),
    ("absences", models.Absences),
    ("bulletins", models.Bulletins),
    ("bulletin_details", models.BulletinDetails),
    ("depenses", models.Depenses),
    ("cloture_alertes", models.ClotureAlertes),
    ("documents", models.Documents),
    ("seances", models.Seances),
]

# Colonnes ignorées du classeur (BLOB trop lourd pour un tableur) : leur
# contenu est restauré depuis les fichiers de l'archive.
_SKIP_EXPORT = {"documents": {"contenu"}}

# Colonnes auto-générées par before_insert : incluses dans l'export (données
# existantes) et restaurées telles quelles via Core insert (bypass ORM).
_AUTO_GEN_COLUMNS = {
    "eleves": {"matricule"},
    "enseignants": {"matricule"},
    "classes": {"code_classe"},
    "cours": {"code_cours"},
    "tuteurs": {"code_tuteur"},
    "salles": {"code_salle"},
    "depenses": {"code_depense"},
    "inscriptions": {"code_inscription"},
    "paiements": {"code_paiement"},
}

_NOM_SAUF = re.compile(r"[^A-Za-z0-9._-]+")


def _base_persistante() -> Path:
    """Dossier de base des fichiers persistés (uploads). Sous exécutable gelé
    (service Windows / installeur), __file__ pointe vers un dossier temporaire
    non persistant : l'installeur impose alors AUREOLE_UPLOADS_DIR pour que les
    fichiers tiennent dans un répertoire d'installation inscriptible."""
    base = os.environ.get("AUREOLE_UPLOADS_DIR") or os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
    )
    return Path(base)


def _dossier_sauvegardes() -> Path:
    """Dossier des archives de sauvegarde.

    Par défaut, les sauvegardes sont écrites À CÔTÉ du dossier des uploads
    (frère de AUREOLE_UPLOADS_DIR) : l'installeur impose AUREOLE_UPLOADS_DIR
    pour persister hors du dossier temporaire gelé, mais PAS
    AUREOLE_SAUVEGARDES_DIR — sinon les archives iraient dans <gelé>/sauvegardes,
    non persistant et souvent non inscriptible (erreur interne au clic sur
    « Télécharger la sauvegarde »)."""
    base = os.environ.get("AUREOLE_SAUVEGARDES_DIR") or (
        _base_persistante().parent / "sauvegardes"
    )
    path = Path(base)
    os.makedirs(path, exist_ok=True)
    return path


def _upl_uploads() -> Path:
    return _base_persistante()


def _nom_fichier_document(doc_id: int, filename: str) -> str:
    propre = _NOM_SAUF.sub("_", str(filename)).strip("._")[:60] or "document"
    return f"{doc_id}_{propre}"


def _cell_value(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, time):
        return v.strftime("%H:%M:%S")
    if isinstance(v, Decimal):
        return float(v)
    if hasattr(v, "value"):
        return v.value
    return v


def _restaurer_valeur(colonne, valeur):
    """Inverse de `_cell_value` : valeur lue openpyxl → type SQLAlchemy."""
    if valeur is None:
        return None
    if isinstance(colonne.type, DateTime):
        return datetime.fromisoformat(valeur) if isinstance(valeur, str) else valeur
    if isinstance(colonne.type, Date):
        return date.fromisoformat(str(valeur)[:10]) if not isinstance(valeur, date) else valeur
    if isinstance(colonne.type, Time):
        if isinstance(valeur, str):
            parties = valeur.split(":")
            return time(int(parties[0]), int(parties[1]), int(float(parties[2])))
        return valeur
    if isinstance(colonne.type, Integer):
        return int(valeur) if isinstance(valeur, (int, float, str)) else valeur
    return valeur


# ── Construction du classeur / de l'archive ─────────────────────────────────

def construire_classeur_export(db: Session) -> bytes:
    """XLSX complet : un onglet par table, colonnes réelles du schéma."""
    wb = Workbook()
    wb.remove(wb.active)
    for sheet_name, model_cls in _TABLES:
        ws = wb.create_sheet(title=sheet_name)
        table = model_cls.__table__
        skip = _SKIP_EXPORT.get(sheet_name, set())
        colonnes = [c.name for c in table.columns if c.name not in skip]
        ws.append(colonnes)
        for obj in db.query(model_cls).all():
            ws.append([_cell_value(getattr(obj, c)) for c in colonnes])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def construire_archive(db: Session) -> bytes:
    """Archive ZIP complète (classeur + documents binaires + uploads +
    manifeste). C'est LE format de sauvegarde complet."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("donnees.xlsx", construire_classeur_export(db))

        for doc in db.query(models.Documents).all():
            if doc.contenu:
                zf.writestr(
                    f"documents/{_nom_fichier_document(doc.id, doc.filename or str(doc.id))}",
                    doc.contenu,
                )

        racine_uploads = _upl_uploads()
        if racine_uploads.is_dir():
            for chemin in racine_uploads.rglob("*"):
                if chemin.is_file():
                    rel = chemin.relative_to(racine_uploads).as_posix()
                    zf.writestr(f"uploads/{rel}", chemin.read_bytes())

        manifest = {
            "format": FORMAT_ARCHIVE,
            "cree_le": datetime.now().isoformat(),
            "bdd": str(os.getenv("DATABASE_URL", "")).split(":", 1)[0],
        }
        zf.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    buf.seek(0)
    return buf.read()


# ── Sauvegardes sur disque (rotation automatique) ───────────────────────────

def _horodatage() -> str:
    # Millisecondes : deux sauvegardes rapprochées (reset puis purge, auto +
    # manuelle) ne doivent jamais écraser le même fichier.
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


def ecrire_sauvegarde(db: Session, dossier: Path | None = None) -> Path:
    """Écrit une archive complète dans `dossier` (défaut sauvegardes/) et
    purge les archives excédentaires (SAUVEGARDES_MAX)."""
    dossier = dossier or _dossier_sauvegardes()
    os.makedirs(dossier, exist_ok=True)
    chemin = dossier / f"collegeaureole_sauvegarde_{_horodatage()}.zip"
    chemin.write_bytes(construire_archive(db))
    _nettoyer(dossier)
    logger.info("Sauvegarde complète écrite : %s (%d o)", chemin, chemin.stat().st_size)
    return chemin


def lister_sauvegardes(dossier: Path | None = None) -> list[dict]:
    dossier = dossier or _dossier_sauvegardes()
    entrees = []
    for p in sorted(dossier.glob("collegeaureole_sauvegarde_*.zip")):
        entrees.append({
            "nom": p.name,
            "taille_octets": p.stat().st_size,
            "cree_le": datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
        })
    return list(reversed(entrees))


def _nettoyer(dossier: Path, maximum: int | None = None) -> None:
    maximum = maximum or int(os.getenv("SAUVEGARDES_MAX", "30"))
    fichiers = sorted(dossier.glob("collegeaureole_sauvegarde_*.zip"))
    for ancien in fichiers[:-maximum]:
        try:
            ancien.unlink()
            logger.info("Sauvegarde purgée (rotation) : %s", ancien.name)
        except OSError:
            logger.exception("Impossible de supprimer la sauvegarde %s", ancien)


def sauvegarde_auto(db: Session, dossier: Path | None = None) -> Path | None:
    """Sauvegarde automatique idempotente : rien ne re-crée si la plus récente
    archive date de moins de SAUVEGARDES_FREQUENCE_H heures.

    Attention : n'est plus appelée au démarrage du serveur depuis la
    suppression de l'archive automatique au boot (main.py) — l'archive
    complète n'est créée qu'à la clôture d'année via `sauvegarde_cloture`."""
    frequence_h = int(os.getenv("SAUVEGARDES_FREQUENCE_H", "24"))
    dossier = dossier or _dossier_sauvegardes()
    fichiers = sorted(dossier.glob("collegeaureole_sauvegarde_*.zip"))
    if fichiers:
        age_h = (datetime.now().timestamp() - fichiers[-1].stat().st_mtime) / 3600
        if age_h < frequence_h:
            return None
    return ecrire_sauvegarde(db, dossier)


def sauvegarde_avant_destruction(db: Session, raison: str) -> Path:
    """Snapshot complet exigé AVANT toute opération destructrice (reset,
    purge, restauration). Lève une exception si l'écriture échoue : on ne
    détruit JAMAIS de données sans sauvegarde fraîche."""
    chemin = ecrire_sauvegarde(db)
    logger.warning("Sauvegarde pré-opération destructrice (%s) : %s", raison, chemin)
    return chemin


def sauvegarde_cloture(db: Session, dossier: Path | None = None) -> Path | None:
    """Archive complète exigée à chaque clôture d'année.

    Depuis la suppression de la sauvegarde automatique au démarrage (main.py),
    la clôture d'année est le SEUL moment où une archive complète est créée
    automatiquement. Les autres archives sont soit manuelles
    (Paramètres → Sauvegardes / export), soit des garde-fous avant opération
    destructrice (`sauvegarde_avant_destruction`).

    Ignorée en environnement de test (base en mémoire : aucune archive utile
    à écrire sur disque)."""
    if os.getenv("ENVIRONMENT", "").strip().lower() == "test":
        return None
    return ecrire_sauvegarde(db, dossier)


# ── Restauration (import symétrique) ────────────────────────────────────────

def _lire_classeur(donnees_xlsx: bytes) -> dict[str, list[dict]]:
    wb = load_workbook(io.BytesIO(donnees_xlsx), read_only=True, data_only=True)
    resultats: dict[str, list[dict]] = {}
    for feuille in wb.sheetnames:
        ws = wb[feuille]
        lignes = ws.iter_rows(values_only=True)
        try:
            entete = next(lignes)
        except StopIteration:
            continue
        if not entete:
            continue
        colonnes = [str(c) if c is not None else "" for c in entete]
        rows = []
        for ligne in lignes:
            rows.append({colonnes[i]: ligne[i] for i in range(len(colonnes)) if colonnes[i]})
        resultats[feuille] = rows
    wb.close()
    return resultats


def restaurer(db: Session, contenu_archive: bytes, *, chemin_uploads: Path | None = None) -> dict:
    """Restaure l'intégralité d'une archive `construire_archive` dans la base
    courante : purge en sens inverse des FK puis re-insertion Core dans
    l'ordre de dépendance, documents binaires et uploads compris.

    Transactionnel : toute erreur annule la restauration entière (rollback).
    Retourne un résumé d'import (compteurs par table)."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(contenu_archive))
    except zipfile.BadZipFile:
        raise ValueError("Format invalide : une sauvegarde .zip complète est attendue.")

    with zf:
        if "donnees.xlsx" not in zf.namelist():
            raise ValueError("Archive invalide : le classeur donnees.xlsx est absent.")
        manifest = {}
        if "manifest.json" in zf.namelist():
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))

        feuilles = _lire_classeur(zf.read("donnees.xlsx"))

        documents_par_id: dict[int, bytes] = {}
        for membre in zf.namelist():
            if membre.startswith("documents/"):
                identifiant = Path(membre).name.split("_", 1)[0]
                try:
                    documents_par_id[int(identifiant)] = zf.read(membre)
                except ValueError:
                    continue

        classer_fichiers = [m for m in zf.namelist() if m.startswith("uploads/")]

        # 1) Purge complète existante (enfants d'abord).
        for nom_feuille, _modele in reversed(_TABLES):
            if nom_feuille in feuilles:
                db.execute(_modele.__table__.delete())

        # 2) Ré-insertion Core dans l'ordre de dépendance.
        compteurs: dict[str, int] = {}
        for nom_feuille, modele in _TABLES:
            rows = feuilles.get(nom_feuille, [])
            if not rows:
                compteurs[nom_feuille] = 0
                continue
            table = modele.__table__
            colonnes = {c.name: c for c in table.columns}
            skip = _SKIP_EXPORT.get(nom_feuille, set())
            for brut in rows:
                valeurs = {}
                for cle, valeur in brut.items():
                    if cle in colonnes and cle not in skip:
                        valeurs[cle] = _restaurer_valeur(colonnes[cle], valeur)
                if nom_feuille == "documents" and "id" in valeurs:
                    valeurs["contenu"] = documents_par_id.get(valeurs["id"])
                db.execute(table.insert().values(**valeurs))
            compteurs[nom_feuille] = len(rows)

        db.commit()

        # 3) Restauration des fichiers téléversés hors transaction (après
        # succès de la base, pour ne pas écrire de fichiers sur un rollback).
        if classer_fichiers:
            cible = (chemin_uploads or _upl_uploads()).resolve()
            cible.mkdir(parents=True, exist_ok=True)
            for membre in classer_fichiers:
                rel = Path(membre)
                # Continement : on ne restaure que sous `cible`, jamais un
                # chemin absolu ou remontant (zip-slip via `..`/`..\`).
                if rel.parts and rel.parts[0] == "uploads":
                    rel = Path(*rel.parts[1:])
                if not rel.parts or rel.name in ("", "."):
                    continue  # entrée de dossier, sans risque
                if rel.is_absolute() or rel.name == ".." or ".." in rel.parts:
                    raise ValueError(f"Membre d'archive invalide : {membre}")
                destination = (cible / rel).resolve()
                if not destination.is_relative_to(cible):
                    raise ValueError(f"Membre d'archive invalide : {membre}")
                os.makedirs(destination.parent, exist_ok=True)
                destination.write_bytes(zf.read(membre))
    return {
        "format": manifest.get("format", FORMAT_ARCHIVE),
        "cree_le": manifest.get("cree_le", ""),
        "lignes_importees": sum(compteurs.values()),
        "compteurs": compteurs,
    }


def exporter_evidence_sauvegarde(db: Session) -> bytes:
    """Alias court pour l'export simple (XLSX historique)."""
    return construire_classeur_export(db)