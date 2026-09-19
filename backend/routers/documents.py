import os
import re
import mimetypes
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from sqlalchemy.orm import Session
from database import get_db
import magicbytes
import models
import schemas
from security import get_current_user

router = APIRouter(prefix="/api/documents", tags=["Documents"], dependencies=[Depends(get_current_user)])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg", "image/png", "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 Mo

CATEGORIES_VALIDES = {"identite", "photo", "naissance", "scolaire", "medical", "administratif", "autre"}

# Entité cible : (nom de la colonne d'attachement, clé d'accès au modèle).
_ENTITES = {
    "eleve": ("matricule_eleve", models.Eleves, "matricule"),
    "enseignant": ("matricule_enseignant", models.Enseignants, "matricule"),
    "tuteur": ("code_tuteur", models.Tuteurs, "code_tuteur"),
}


def _nettoyer_filename(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)[:60]
    ext = re.sub(r"[^a-zA-Z0-9]", "", ext)[:10]
    return f"{name}.{ext}" if ext else name


def _deviner_media_type(nom_fichier: str) -> str:
    media_type, _ = mimetypes.guess_type(nom_fichier)
    return media_type or "application/octet-stream"


def _nom_affiche(filename: str) -> str:
    """Nom affiché sûr : pas de séparateurs de chemin ni de caractères de contrôle."""
    return re.sub(r"[/\\\x00-\x1f]", "_", filename).strip().rstrip(".") or "document"


def _content_disposition(filename: str, disposition: str = "attachment") -> str:
    """Génère un Content-Disposition RFC 6266 sûr pour les noms non-ASCII."""
    ascii_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    if ascii_name == filename:
        return f'{disposition}; filename="{filename}"'
    from urllib.parse import quote
    return f'{disposition}; filename="{ascii_name}"; filename*=UTF-8\'\'{quote(filename)}'


def _verifier_upload(file: UploadFile) -> str:
    """Valide la taille et le contenu réel d'un fichier ; retourne son type MIME vérifié.

    Le `Content-Type` fourni par le client n'est pas une source fiable : on
    détecte le type par les octets réels (`magicbytes`) et on refuse tout
    contenu inconnu ou incohérent avec le type annoncé (ex. un HTML déguisé
    en image).
    """
    file.file.seek(0, 2)
    taille = file.file.tell()
    file.file.seek(0)
    if taille > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Fichier trop volumineux")

    contenu = file.file.read()
    file.file.seek(0)
    type_reel = magicbytes.type_autorise(contenu, file.content_type, ALLOWED_MIME_TYPES)
    if type_reel is None:
        raise HTTPException(
            status_code=400,
            detail="Type de fichier non reconnu ou incohérent avec le contenu réel",
        )
    return type_reel


def _resoudre_entite(
    db: Session,
    *,
    entite_type: Optional[str] = None,
    entite_id: Optional[str] = None,
    matricule_eleve: Optional[str] = None,
    matricule_enseignant: Optional[str] = None,
    code_tuteur: Optional[str] = None,
):
    """Retrouve l'entité cible et sa colonne d'attachement."""
    cle_cible = None
    if entite_type:
        if entite_type not in _ENTITES:
            raise HTTPException(status_code=400, detail="entite_type invalide")
        cle, modele, _ = _ENTITES[entite_type]
        if not entite_id:
            raise HTTPException(status_code=400, detail="entite_id manquant")
        cle_cible = (cle, entite_id, modele)
    elif matricule_eleve:
        cle_cible = ("matricule_eleve", matricule_eleve, models.Eleves)
    elif matricule_enseignant:
        cle_cible = ("matricule_enseignant", matricule_enseignant, models.Enseignants)
    elif code_tuteur:
        cle_cible = ("code_tuteur", code_tuteur, models.Tuteurs)
    else:
        raise HTTPException(status_code=400, detail="Entité cible manquante")

    cle, identifiant, modele = cle_cible
    if modele is models.Eleves:
        entite = db.query(modele).filter(modele.matricule == identifiant).first()
    elif modele is models.Enseignants:
        entite = db.query(modele).filter(modele.matricule == identifiant).first()
    else:
        entite = db.query(modele).filter(modele.code_tuteur == identifiant).first()
    if not entite:
        raise HTTPException(status_code=404, detail="Entité introuvable")
    return cle, identifiant, entite


def _associer_entite(doc: models.Documents):
    if doc.matricule_eleve:
        return "eleve", doc.matricule_eleve
    if doc.matricule_enseignant:
        return "enseignant", doc.matricule_enseignant
    if doc.code_tuteur:
        return "tuteur", doc.code_tuteur
    return None, None


def _charger_entite_label(
    db: Session, doc: models.Documents,
    eleves=None, enseignants=None, tuteurs=None,
) -> Optional[str]:
    et, eid = _associer_entite(doc)
    if not et or not eid:
        return None
    if et == "eleve":
        entite = eleves.get(eid) if eleves is not None else db.query(models.Eleves).filter(models.Eleves.matricule == eid).first()
        return f"{entite.nom} {entite.prenom}" if entite else f"Élève {eid}"
    if et == "enseignant":
        entite = enseignants.get(eid) if enseignants is not None else db.query(models.Enseignants).filter(models.Enseignants.matricule == eid).first()
        return f"{entite.nom} {entite.prenom}" if entite else f"Enseignant {eid}"
    entite = tuteurs.get(eid) if tuteurs is not None else db.query(models.Tuteurs).filter(models.Tuteurs.code_tuteur == eid).first()
    return f"{entite.nom} {entite.prenom}" if entite else f"Tuteur {eid}"


def _to_read(doc: models.Documents, entite_label: Optional[str] = None) -> schemas.DocumentRead:
    et, eid = _associer_entite(doc)
    return schemas.DocumentRead(
        id=doc.id,
        nom=doc.filename,
        categorie=doc.categorie,
        entite_type=et,
        entite_id=eid,
        nom_fichier_original=doc.nom_fichier_original,
        type_mime=doc.mime_type,
        taille_octets=doc.taille,
        created_at=doc.uploaded_at,
        url_preview=f"/api/documents/{doc.id}/preview",
        url_download=f"/api/documents/{doc.id}/fichier",
        matricule_eleve=doc.matricule_eleve,
        matricule_enseignant=doc.matricule_enseignant,
        code_tuteur=doc.code_tuteur,
        type_document=doc.type_document,
        filename=doc.filename,
        taille=doc.taille,
        mime_type=doc.mime_type,
        uploaded_at=doc.uploaded_at,
        entite_label=entite_label,
    )


def _creer_document(
    db: Session,
    *,
    file: UploadFile,
    nom: Optional[str] = None,
    categorie: str = "autre",
    type_document: Optional[str] = None,
    entite_type: Optional[str] = None,
    entite_id: Optional[str] = None,
    matricule_eleve: Optional[str] = None,
    matricule_enseignant: Optional[str] = None,
    code_tuteur: Optional[str] = None,
):
    mime_type = _verifier_upload(file)
    if categorie not in CATEGORIES_VALIDES:
        raise HTTPException(status_code=400, detail="Catégorie invalide")

    cle, identifiant, entite = _resoudre_entite(
        db,
        entite_type=entite_type,
        entite_id=entite_id,
        matricule_eleve=matricule_eleve,
        matricule_enseignant=matricule_enseignant,
        code_tuteur=code_tuteur,
    )

    contenu = file.file.read()

    # Nom affiché : valeur explicite sinon « <type|catégorie>_<nom>_<prénom> ».
    if nom:
        filename = _nom_affiche(nom)
    else:
        genre = type_document or categorie
        base = _nettoyer_filename(f"{genre}_{entite.nom}_{entite.prenom}")
        _, ext = os.path.splitext(file.filename or "")
        ext = re.sub(r"[^a-zA-Z0-9]", "", ext)[:10]
        filename = f"{base}{('.' + ext) if ext else ''}"

    kw = {cle: identifiant}
    doc = models.Documents(
        **kw,
        categorie=categorie,
        type_document=type_document,
        filename=filename,
        nom_fichier_original=file.filename,
        filepath=filename,  # valeur logique : le contenu est stocké en base
        contenu=contenu,
        taille=len(contenu),
        mime_type=mime_type,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


# ── API générique (§46) ──────────────────────────────────────────────────────


@router.get("/", response_model=List[schemas.DocumentRead])
def lister_documents(
    entite_type: Optional[str] = None,
    entite_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Liste globale (§46) ou filtrée par entité via `?entite_type=&entite_id=`."""
    query = db.query(models.Documents)
    if entite_type:
        if entite_type not in _ENTITES:
            raise HTTPException(status_code=400, detail="entite_type invalide")
        if not entite_id:
            raise HTTPException(status_code=400, detail="entite_id manquant")
        cle = _ENTITES[entite_type][0]
        query = query.filter(getattr(models.Documents, cle) == entite_id)
    docs = query.order_by(models.Documents.uploaded_at.desc(), models.Documents.id.desc()).all()

    # Libellés d'entité en une passe (liste globale uniquement).
    eleves, enseignants, tuteurs = {}, {}, {}
    if not entite_type:
        mat_e = {d.matricule_eleve for d in docs if d.matricule_eleve}
        mat_s = {d.matricule_enseignant for d in docs if d.matricule_enseignant}
        cod_t = {d.code_tuteur for d in docs if d.code_tuteur}
        if mat_e:
            eleves = {e.matricule: e for e in db.query(models.Eleves).filter(models.Eleves.matricule.in_(mat_e)).all()}
        if mat_s:
            enseignants = {e.matricule: e for e in db.query(models.Enseignants).filter(models.Enseignants.matricule.in_(mat_s)).all()}
        if cod_t:
            tuteurs = {t.code_tuteur: t for t in db.query(models.Tuteurs).filter(models.Tuteurs.code_tuteur.in_(cod_t)).all()}

    return [
        _to_read(
            doc,
            entite_label=_charger_entite_label(db, doc, eleves, enseignants, tuteurs),
        )
        for doc in docs
    ]


@router.post("/", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    entite_type: str = Form(...),
    entite_id: str = Form(...),
    fichier: UploadFile = File(...),
    nom: Optional[str] = Form(None),
    categorie: str = Form("autre"),
    db: Session = Depends(get_db),
):
    doc = _creer_document(
        db,
        file=fichier,
        nom=nom,
        categorie=categorie,
        entite_type=entite_type,
        entite_id=entite_id,
    )
    return _to_read(doc, entite_label=_charger_entite_label(db, doc))


@router.patch("/{document_id}", response_model=schemas.DocumentRead)
def modifier_document(
    document_id: int,
    payload: schemas.DocumentUpdate,
    db: Session = Depends(get_db),
):
    doc = db.query(models.Documents).filter(models.Documents.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if payload.nom is not None:
        doc.filename = _nom_affiche(payload.nom)
    if payload.categorie is not None:
        if payload.categorie not in CATEGORIES_VALIDES:
            raise HTTPException(status_code=400, detail="Catégorie invalide")
        doc.categorie = payload.categorie
    db.commit()
    db.refresh(doc)
    return _to_read(doc, entite_label=_charger_entite_label(db, doc))


@router.get("/{document_id}/preview")
def preview_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Documents).filter(models.Documents.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return _servir_document(doc, disposition="inline")


@router.get("/{document_id}/fichier")
def telecharger_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Documents).filter(models.Documents.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return _servir_document(doc, disposition="attachment")


def _servir_document(doc: models.Documents, *, disposition: str):
    # Jamais de rendu inline pour autre chose que des images/PDF : un HTML ou
    # SVG stocké pourrait être exécuté dans l'origine de l'application.
    mime = doc.mime_type or _deviner_media_type(doc.filename)
    if disposition == "inline" and not magicbytes.servir_inline(mime):
        disposition = "attachment"
    headers: dict[str, str] = {"X-Content-Type-Options": "nosniff"}
    if doc.contenu is not None:
        return Response(
            content=doc.contenu,
            media_type=mime,
            headers={
                **headers,
                "Content-Disposition": _content_disposition(
                    doc.nom_fichier_original or doc.filename, disposition
                ),
            },
        )
    # Fallback : anciens documents stockés sur disque avant la migration BLOB.
    if not os.path.exists(doc.filepath):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return FileResponse(
        doc.filepath,
        filename=doc.nom_fichier_original or doc.filename,
        media_type=mime,
        headers=headers,
    )


# ── Uploads rétro-compat (par entité, champ type_document) ──────────────────
_UPLOAD = [Depends(get_current_user)]


@router.post("/upload", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED, dependencies=_UPLOAD)
def upload_document_eleve_legacy(
    matricule_eleve: str = Form(...),
    type_document: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return _to_read(_creer_document(
        db, matricule_eleve=matricule_eleve, type_document=type_document, file=file
    ))


@router.post("/enseignant/upload", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED, dependencies=_UPLOAD)
def upload_document_enseignant_legacy(
    matricule_enseignant: str = Form(...),
    type_document: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return _to_read(_creer_document(
        db, matricule_enseignant=matricule_enseignant, type_document=type_document, file=file
    ))


@router.post("/tuteur/upload", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED, dependencies=_UPLOAD)
def upload_document_tuteur_legacy(
    code_tuteur: str = Form(...),
    type_document: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return _to_read(_creer_document(
        db, code_tuteur=code_tuteur, type_document=type_document, file=file
    ))


# ── Récupération par entité (rétro-compat) ───────────────────────────────────
@router.get("/enseignant/{matricule}", response_model=List[schemas.DocumentRead])
def lister_documents_enseignant(matricule: str, db: Session = Depends(get_db)):
    return [
        _to_read(doc, entite_label=_charger_entite_label(db, doc))
        for doc in db.query(models.Documents)
        .filter(models.Documents.matricule_enseignant == matricule)
        .order_by(models.Documents.uploaded_at.desc())
        .all()
    ]


@router.get("/tuteur/{code}", response_model=List[schemas.DocumentRead])
def lister_documents_tuteur(code: str, db: Session = Depends(get_db)):
    return [
        _to_read(doc, entite_label=_charger_entite_label(db, doc))
        for doc in db.query(models.Documents)
        .filter(models.Documents.code_tuteur == code)
        .order_by(models.Documents.uploaded_at.desc())
        .all()
    ]


@router.get("/file/{document_id}")
def telecharger_document_legacy(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Documents).filter(models.Documents.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    return _servir_document(doc, disposition="attachment")


# ── Routes par matricule (strictement après /enseignant, /tuteur, /file) ──────
@router.get("/{matricule}", response_model=List[schemas.DocumentRead])
def lister_documents_eleve(matricule: str, db: Session = Depends(get_db)):
    return [
        _to_read(doc, entite_label=_charger_entite_label(db, doc))
        for doc in db.query(models.Documents)
        .filter(models.Documents.matricule_eleve == matricule)
        .order_by(models.Documents.uploaded_at.desc())
        .all()
    ]


# ── Suppression ──────────────────────────────────────────────────────────────
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Documents).filter(models.Documents.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    if doc.filepath and os.path.exists(doc.filepath) and os.path.isfile(doc.filepath):
        try:
            os.remove(doc.filepath)
        except OSError:
            pass
    db.delete(doc)
    db.commit()
    return None