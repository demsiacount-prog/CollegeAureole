"""Import / Export, sauvegardes et restauration.

- GET  /export          → classeur XLSX historique (un onglet par table).
- GET  /export/complet  → archive ZIP de sauvegarde complète (données +
                         BLOB des documents + fichiers uploads/), conservée
                         aussi sur disque dans sauvegardes/.
- POST /sauvegarde      → crée une sauvegarde serveur à la demande.
- GET  /sauvegardes     → liste les sauvegardes disponibles sur disque.
- POST /import          → restauration symétrique (remplacement complet,
                         transactionnel, avec snapshot automatique avant).
"""
import io
import logging

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from ratelimit import L_IMPORT, L_SAUVEGARDE, limiter
from security import require_admin
from services import sauvegardes

router = APIRouter(
    prefix="/api/import-export",
    tags=["Import / Export"],
    dependencies=[Depends(require_admin)],
)

logger = logging.getLogger("college_aureole")

# En-tête d'armement exigé pour toute opération de restauration destructrice.
IMPORT_CONFIRM_HEADER = "X-Confirm"
IMPORT_CONFIRM_TOKEN = "RESTAURATION-DONNEES"


def _sauvegarde_zip(db: Session) -> StreamingResponse:
    """Archive ZIP complète des données (classeur + documents + uploads)."""
    contenu = sauvegardes.construire_archive(db)
    ts = sauvegardes._horodatage()
    return StreamingResponse(
        io.BytesIO(contenu),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="collegeaureole_sauvegarde_{ts}.zip"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/export")
def exporter(db: Session = Depends(get_db)):
    """Classeur Excel : un onglet par table (hors BLOB documents)."""
    contenu = sauvegardes.construire_classeur_export(db)
    ts = sauvegardes._horodatage()
    return StreamingResponse(
        io.BytesIO(contenu),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="collegeaureole_export_{ts}.xlsx"'},
    )


@router.get(
    "/export/complet",
    dependencies=[limiter("sauvegarde", *L_SAUVEGARDE)],
)
def exporter_complet(db: Session = Depends(get_db)):
    """Sauvegarde complète téléchargeable, également archivée sur le serveur
    (dossier sauvegardes/, rotation SAUVEGARDES_MAX).

    L'archivage sur disque est best-effort : si le dossier sauvegardes/ n'est
    pas accessible en écriture, le téléchargement reste possible (l'archive est
    construite en mémoire) ; seul un avertissement est loggé."""
    try:
        sauvegardes.ecrire_sauvegarde(db)
    except OSError:
        logger.exception(
            "Archivage sur disque impossible (dossier sauvegardes/ inaccessible ?) — "
            "téléchargement servi sans archive serveur."
        )
    return _sauvegarde_zip(db)


@router.post(
    "/sauvegarde",
    dependencies=[limiter("sauvegarde", *L_SAUVEGARDE)],
)
def creer_sauvegarde(db: Session = Depends(get_db)):
    """Crée une sauvegarde complète sur disque, à la demande de l'admin."""
    try:
        nom = sauvegardes.ecrire_sauvegarde(db).name
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Impossible d'écrire la sauvegarde : le dossier sauvegardes/ "
            "n'est pas accessible en écriture sur le serveur.",
        )
    return {"sauvegarde": nom}


@router.get("/sauvegardes")
def lister_sauvegardes():
    """Liste des sauvegardes disponibles (nom, taille, date)."""
    try:
        return {"sauvegardes": sauvegardes.lister_sauvegardes()}
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Impossible de lister les sauvegardes : dossier sauvegardes/ "
            "inaccessible.",
        )


@router.post("/import", dependencies=[limiter("import", *L_IMPORT)])
def importer(
    fichier: UploadFile = File(...),
    remplacer: bool = Form(False),
    x_confirm: str | None = Header(default=None, alias="X-Confirm"),
    _admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Restaure une sauvegarde complète (fichier `.zip` produit par
    /export/complet). Le contenu courant est REMPLACÉ intégralement :
    un snapshot automatique du présent est donc écrit au préalable, et la
    restauration exige `remplacer=true` + l'en-tête
    `X-Confirm: RESTAURATION-DONNEES`. Transactionnelle : au moindre échec,
    aucune donnée n'est modifiée."""
    if not remplacer:
        raise HTTPException(status_code=400, detail="Confirmation requise : remplacer=true")
    if x_confirm != IMPORT_CONFIRM_TOKEN:
        raise HTTPException(status_code=400, detail="Confirmation requise : en-tête X-Confirm attendu.")

    contenu = fichier.file.read()
    if not contenu:
        raise HTTPException(status_code=400, detail="Fichier vide")

    # Snapshot avant toute destruction : la base actuelle reste récupérable.
    try:
        sauvegardes.sauvegarde_avant_destruction(db, "restauration")
    except OSError:
        raise HTTPException(
            status_code=500,
            detail="Impossible d'écrire le snapshot de sécurité avant restauration : opération annulée.",
        )

    try:
        resume = sauvegardes.restaurer(db, contenu)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="La restauration a échoué : aucune donnée modifiée.")

    return {
        "message": "Restauration terminée.",
        "lignes_importees": resume["lignes_importees"],
        "sauvegarde_avant_restauration": "oui",
    }