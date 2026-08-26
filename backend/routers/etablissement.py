import os
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
import models
import schemas
from security import require_role

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


@router.put("", response_model=schemas.EtablissementResponse, dependencies=[Depends(require_role("admin"))])
def update_etablissement(payload: schemas.EtablissementUpdate, db: Session = Depends(get_db)):
    fiche = _fiche_ou_404(db)
    for key, value in payload.model_dump().items():
        setattr(fiche, key, value)
    db.commit()
    db.refresh(fiche)
    return fiche


def enregistrer_logo(file: UploadFile) -> str:
    """Valide l'image du logo, l'enregistre sur disque et retourne son chemin
    public. Le lien avec la fiche établissement est établi séparément (PUT de
    l'établissement ou fiche d'initialisation)."""
    if file.content_type not in _LOGO_MIME_TO_EXT:
        raise HTTPException(
            status_code=400,
            detail="Format d'image non autorisé",
        )
    file.file.seek(0, 2)
    taille = file.file.tell()
    file.file.seek(0)
    if taille > _LOGO_MAX_SIZE:
        raise HTTPException(status_code=400, detail="Image trop volumineuse")

    ext = _LOGO_MIME_TO_EXT[file.content_type]

    os.makedirs(_UPLOADS_LOGOS_DIR, exist_ok=True)
    filename = f"logo_{uuid.uuid4().hex[:12]}{ext}"
    with open(os.path.join(_UPLOADS_LOGOS_DIR, filename), "wb") as f:
        shutil.copyfileobj(file.file, f)

    return f"/uploads/logos/{filename}"


@router.post("/logo", dependencies=[Depends(require_role("admin"))])
def upload_logo(file: UploadFile = File(...)):
    """Enregistre l'image du logo et retourne son chemin public (la fiche n'est
    modifiée qu'au prochain PUT de l'établissement)."""
    return {"logo": enregistrer_logo(file)}
