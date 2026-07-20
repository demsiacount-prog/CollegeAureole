from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/notes", tags=["Notes"], dependencies=[Depends(get_current_user)])

# NoteResponse imbrique eleve + cours + classe + enseignant + trimestre : sans
# eager loading, chaque note sérialisée coûte jusqu'à 5 requêtes SQL supplémentaires.
_EAGER = (
    joinedload(models.Notes.eleve),
    joinedload(models.Notes.cours),
    joinedload(models.Notes.classe),
    joinedload(models.Notes.enseignant),
    joinedload(models.Notes.trimestre),
)


def _verifier_references(note, db: Session):
    if not db.query(models.Eleves).filter(models.Eleves.matricule == note.matricule_eleve).first():
        raise HTTPException(status_code=404, detail="Élève introuvable.")
    if not db.query(models.Cours).filter(models.Cours.id == note.id_cours).first():
        raise HTTPException(status_code=404, detail="Cours introuvable.")
    if not db.query(models.Classes).filter(models.Classes.id == note.id_classe).first():
        raise HTTPException(status_code=404, detail="Classe introuvable.")
    if not db.query(models.Enseignants).filter(models.Enseignants.matricule == note.matricule_enseignant).first():
        raise HTTPException(status_code=404, detail="Enseignant introuvable.")
    if note.id_trimestre is not None:
        trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == note.id_trimestre).first()
        if not trimestre:
            raise HTTPException(status_code=404, detail="Trimestre introuvable.")
        if trimestre.verrouille:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="La période de saisie de ce trimestre est verrouillée.",
            )


@router.post("/", response_model=schemas.NoteResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    _verifier_references(note, db)
    data = note.model_dump()
    data["date"] = date.today().isoformat()
    nouvelle_note = models.Notes(**data)
    db.add(nouvelle_note)
    db.commit()
    db.refresh(nouvelle_note)
    return nouvelle_note


@router.get("/", response_model=List[schemas.NoteResponse])
def get_all_notes(
    matricule_eleve: Optional[str] = None,
    id_classe: Optional[int] = None,
    id_cours: Optional[int] = None,
    id_trimestre: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(models.Notes).options(*_EAGER)
    if matricule_eleve:
        query = query.filter(models.Notes.matricule_eleve == matricule_eleve)
    if id_classe:
        query = query.filter(models.Notes.id_classe == id_classe)
    if id_cours:
        query = query.filter(models.Notes.id_cours == id_cours)
    if id_trimestre:
        query = query.filter(models.Notes.id_trimestre == id_trimestre)
    return query.order_by(models.Notes.id).offset(skip).limit(limit).all()


@router.get("/{note_id}", response_model=schemas.NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(models.Notes).options(*_EAGER).filter(models.Notes.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note introuvable")
    return db_note


@router.put("/{note_id}", response_model=schemas.NoteResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_note(note_id: int, note_update: schemas.NoteCreate, db: Session = Depends(get_db)):
    db_note = db.query(models.Notes).filter(models.Notes.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note introuvable")

    _verifier_references(note_update, db)

    for key, value in note_update.model_dump().items():
        setattr(db_note, key, value)
    db_note.updated_at = datetime.now().isoformat()
    db.commit()
    db.refresh(db_note)
    return db_note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(models.Notes).filter(models.Notes.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note introuvable")
    if db_note.id_trimestre:
        trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == db_note.id_trimestre).first()
        if trimestre and trimestre.verrouille:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Trimestre verrouillé.")
    db.delete(db_note)
    db.commit()
    return None
