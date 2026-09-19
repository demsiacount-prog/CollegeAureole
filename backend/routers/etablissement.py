import os
import shutil
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
import magicbytes
from security import get_current_user, require_admin
import models
import schemas
router = APIRouter(prefix="/api/etablissement", tags=["Établissement"])

_UPLOADS_BASE = os.environ.get("AUREOLE_UPLOADS_DIR") or os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
)
_UPLOADS_LOGOS_DIR = os.path.join(_UPLOADS_BASE, "logos")
# Extension dérivée du type MIME (déjà validé), jamais du nom de fichier
# fourni par le client : un nom de fichier n'est pas fiable (absent,
# trompeur, ou dans une casse/format inattendu) et le faire dépendre de lui
# a par le passé provoqué l'enregistrement de tous les logos non-PNG sous
# une extension .png alors que leur contenu réel restait JPEG/WebP/GIF,
# ce qui cassait l'affichage dans le WebView du client bureau (Tauri).
_LOGO_MIME_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_LOGO_MAX_SIZE = 2 * 1024 * 1024  # 2 Mo


def _fiche_ou_404(db: Session) -> models.Etablissement:
    fiche = db.query(models.Etablissement).first()
    if not fiche:
        raise HTTPException(status_code=404, detail="Établissement introuvable")
    return fiche


@router.get("", response_model=schemas.EtablissementResponse)
def get_etablissement(db: Session = Depends(get_db)):
    return _fiche_ou_404(db)


@router.put("", response_model=schemas.EtablissementResponse)
def update_etablissement(
    payload: schemas.EtablissementUpdate,
    _user: models.Utilisateurs = Depends(require_admin),
    db: Session = Depends(get_db),
):
    fiche = _fiche_ou_404(db)
    for key, value in payload.model_dump().items():
        # academie/cap sont NOT NULL en base : une valeur vide devient ''.
        if key in ("academie", "cap") and value is None:
            value = ""
        if value is not None:
            setattr(fiche, key, value)
    db.commit()
    db.refresh(fiche)
    return fiche


def enregistrer_logo(file: UploadFile) -> str:
    """Valide l'image du logo, l'enregistre sur disque et retourne son chemin
    public. Le lien avec la fiche établissement est établi séparément (PUT de
    l'établissement ou fiche d'initialisation).

    L'extension est dérivée du **type réel du contenu** (magic bytes), jamais
    du Content-Type ou du nom envoyé par le client (peu fiables) : un HTML
    déguisé en `image/png` ne peut pas être enregistré comme logo."""
    file.file.seek(0, 2)
    taille = file.file.tell()
    file.file.seek(0)
    if taille > _LOGO_MAX_SIZE:
        raise HTTPException(status_code=400, detail="Image trop volumineuse")

    entete = file.file.read(16)
    file.file.seek(0)
    type_reel = magicbytes.detecter_type_mime(entete)
    if type_reel not in _LOGO_MIME_TO_EXT:
        raise HTTPException(
            status_code=400,
            detail="Format d'image non autorisé",
        )

    ext = _LOGO_MIME_TO_EXT[type_reel]

    os.makedirs(_UPLOADS_LOGOS_DIR, exist_ok=True)
    filename = f"logo_{uuid.uuid4().hex[:12]}{ext}"
    with open(os.path.join(_UPLOADS_LOGOS_DIR, filename), "wb") as f:
        shutil.copyfileobj(file.file, f)

    return f"/uploads/logos/{filename}"


@router.post("/logo")
def upload_logo(
    file: UploadFile = File(...),
    _user: models.Utilisateurs = Depends(require_admin),
):
    """Enregistre l'image du logo et retourne son chemin public (la fiche n'est
    modifiée qu'au prochain PUT de l'établissement)."""
    return {"logo": enregistrer_logo(file)}


# ─── Infrastructures et mobiliers (fiche renseignements 1er cycle) ────────────

def _infrastructures_4o404(db: Session, annee_id: Optional[int]) -> models.EtablissementInfrastructures:
    """Retourne l'enregistrement d'infrastructures de l'année demandée (ou de
    l'année active), ou 404 s'il n'a pas encore été saisi."""
    if annee_id is None:
        annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()  # noqa: E712
        if not annee:
            raise HTTPException(status_code=404, detail="Aucune année scolaire active")
        annee_id = annee.id
    infra = (
        db.query(models.EtablissementInfrastructures)
        .filter(models.EtablissementInfrastructures.id_annee_scolaire == annee_id)
        .first()
    )
    if not infra:
        raise HTTPException(status_code=404, detail="Infrastructures non renseignées pour cette année scolaire")
    return infra


@router.get("/infrastructures", response_model=schemas.EtablissementInfrastructuresResponse)
def get_infrastructures(
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _user: models.Utilisateurs = Depends(get_current_user),
):
    return _infrastructures_4o404(db, annee_id)


@router.put("/infrastructures", response_model=schemas.EtablissementInfrastructuresResponse)
def put_infrastructures(
    payload: schemas.EtablissementInfrastructuresPayload,
    _user: models.Utilisateurs = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Crée ou met à jour les infrastructures/mobiliers de l'année scolaire
    demandée (par défaut l'année active)."""
    annee_id = payload.id_annee_scolaire
    if annee_id is None:
        annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()  # noqa: E712
        if not annee:
            raise HTTPException(status_code=400, detail="Aucune année scolaire active")
        annee_id = annee.id
    else:
        annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee_id).first()
        if not annee:
            raise HTTPException(status_code=404, detail="Année scolaire introuvable")

    infra = (
        db.query(models.EtablissementInfrastructures)
        .filter(models.EtablissementInfrastructures.id_annee_scolaire == annee_id)
        .first()
    )
    if infra is None:
        infra = models.EtablissementInfrastructures(id_annee_scolaire=annee_id)
        db.add(infra)
    for cle, valeur in payload.model_dump().items():
        if cle == "id_annee_scolaire":
            continue
        setattr(infra, cle, valeur)
    db.commit()
    db.refresh(infra)
    return infra
