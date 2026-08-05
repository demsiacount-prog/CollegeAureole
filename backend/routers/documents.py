import os
import re
import mimetypes
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/documents", tags=["Documents"], dependencies=[Depends(get_current_user)])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg", "image/png", "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo


def _nettoyer_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:60]
    ext = re.sub(r"[^a-zA-Z0-9]", "", ext)[:10]
    return f"{name}.{ext}" if ext else name


def _deviner_media_type(nom_fichier: str) -> str:
    media_type, _ = mimetypes.guess_type(nom_fichier)
    return media_type or "application/octet-stream"


def _verifier_upload(file: UploadFile):
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Type de fichier non autorisé : {file.content_type}")
    file.file.seek(0, 2)
    taille = file.file.tell()
    file.file.seek(0)
    if taille > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"Fichier trop volumineux ({taille} octets). Maximum : {MAX_FILE_SIZE} octets.")


def _enregistrer_document(
    db: Session,
    *,
    type_document: str,
    file: UploadFile,
    matricule_eleve: Optional[str] = None,
    matricule_enseignant: Optional[str] = None,
    code_tuteur: Optional[str] = None,
):
    _verifier_upload(file)

    if matricule_eleve:
        entite = db.query(models.Eleves).filter(models.Eleves.matricule == matricule_eleve).first()
        if not entite:
            raise HTTPException(status_code=404, detail="Élève introuvable.")
    elif matricule_enseignant:
        entite = db.query(models.Enseignants).filter(models.Enseignants.matricule == matricule_enseignant).first()
        if not entite:
            raise HTTPException(status_code=404, detail="Enseignant introuvable.")
    elif code_tuteur:
        entite = db.query(models.Tuteurs).filter(models.Tuteurs.code_tuteur == code_tuteur).first()
        if not entite:
            raise HTTPException(status_code=404, detail="Tuteur introuvable.")
    else:
        raise HTTPException(status_code=400, detail="Entité cible manquante.")

    contenu = file.file.read()

    # Nom de fichier normalisé : <type_document>_<nom>_<prenom>.<extension>
    _, ext = os.path.splitext(file.filename or "")
    ext = re.sub(r"[^a-zA-Z0-9]", "", ext)[:10]
    base = _nettoyer_filename(f"{type_document}_{entite.nom}_{entite.prenom}")
    filename = f"{base}{('.' + ext) if ext else ''}"
    mime_type = file.content_type or _deviner_media_type(filename)

    doc = models.Documents(
        matricule_eleve=matricule_eleve,
        matricule_enseignant=matricule_enseignant,
        code_tuteur=code_tuteur,
        type_document=type_document,
        filename=filename,
        filepath=filename,  # valeur logique : le contenu est stocké en base
        contenu=contenu,
        taille=len(contenu),
        mime_type=mime_type,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ── Uploads (admin/directeur) ────────────────────────────────────────────────
_ROLE_UPLOAD = [Depends(require_role("admin", "directeur"))]


@router.post("/upload", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=_ROLE_UPLOAD)
def upload_document_eleve(
    matricule_eleve: str = Form(...),
    type_document: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return _enregistrer_document(
        db, matricule_eleve=matricule_eleve, type_document=type_document, file=file
    )


@router.post("/enseignant/upload", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=_ROLE_UPLOAD)
def upload_document_enseignant(
    matricule_enseignant: str = Form(...),
    type_document: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return _enregistrer_document(
        db, matricule_enseignant=matricule_enseignant, type_document=type_document, file=file
    )


@router.post("/tuteur/upload", response_model=schemas.DocumentResponse, status_code=status.HTTP_201_CREATED, dependencies=_ROLE_UPLOAD)
def upload_document_tuteur(
    code_tuteur: str = Form(...),
    type_document: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return _enregistrer_document(
        db, code_tuteur=code_tuteur, type_document=type_document, file=file
    )


# ── Listes ───────────────────────────────────────────────────────────────────
@router.get("/{matricule}", response_model=List[schemas.DocumentResponse])
def lister_documents_eleve(matricule: str, db: Session = Depends(get_db)):
    return (
        db.query(models.Documents)
        .filter(models.Documents.matricule_eleve == matricule)
        .order_by(models.Documents.uploaded_at.desc())
        .all()
    )


@router.get("/enseignant/{matricule}", response_model=List[schemas.DocumentResponse])
def lister_documents_enseignant(matricule: str, db: Session = Depends(get_db)):
    return (
        db.query(models.Documents)
        .filter(models.Documents.matricule_enseignant == matricule)
        .order_by(models.Documents.uploaded_at.desc())
        .all()
    )


@router.get("/tuteur/{code}", response_model=List[schemas.DocumentResponse])
def lister_documents_tuteur(code: str, db: Session = Depends(get_db)):
    return (
        db.query(models.Documents)
        .filter(models.Documents.code_tuteur == code)
        .order_by(models.Documents.uploaded_at.desc())
        .all()
    )


# ── Téléchargement ───────────────────────────────────────────────────────────
@router.get("/file/{document_id}")
def telecharger_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Documents).filter(models.Documents.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable.")

    if doc.contenu is not None:
        return Response(
            content=doc.contenu,
            media_type=doc.mime_type or _deviner_media_type(doc.filename),
            headers={"Content-Disposition": f'attachment; filename="{doc.filename}"'},
        )

    # Fallback : anciens documents stockés sur disque avant la migration BLOB.
    if not os.path.exists(doc.filepath):
        raise HTTPException(status_code=404, detail="Fichier introuvable.")
    return FileResponse(
        doc.filepath,
        filename=doc.filename,
        media_type=_deviner_media_type(doc.filepath),
    )


# ── Suppression ──────────────────────────────────────────────────────────────
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def supprimer_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Documents).filter(models.Documents.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable.")
    if doc.filepath and os.path.exists(doc.filepath) and os.path.isfile(doc.filepath):
        try:
            os.remove(doc.filepath)
        except OSError:
            pass
    db.delete(doc)
    db.commit()
    return None
