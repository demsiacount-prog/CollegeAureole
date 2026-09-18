from timeutils import now_utc
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
import models
import schemas
from security import get_current_user
from bareme import bareme_niveau, est_jardin

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
        raise HTTPException(status_code=404, detail="Élève introuvable")
    cours = db.query(models.Cours).filter(models.Cours.id == note.id_cours).first()
    if not cours:
        raise HTTPException(status_code=404, detail="Cours introuvable")
    if not db.query(models.Classes).filter(models.Classes.id == note.id_classe).first():
        raise HTTPException(status_code=404, detail="Classe introuvable")
    if not db.query(models.Enseignants).filter(models.Enseignants.matricule == note.matricule_enseignant).first():
        raise HTTPException(status_code=404, detail="Enseignant introuvable")
    if not db.query(models.AffectationCoursClasse).filter(
        models.AffectationCoursClasse.id_cours == note.id_cours,
        models.AffectationCoursClasse.id_classe == note.id_classe,
    ).first():
        raise HTTPException(status_code=400, detail="Cours non affecté")
    if cours.matricule_enseignant and cours.matricule_enseignant != note.matricule_enseignant:
        raise HTTPException(status_code=400, detail="Enseignant non assigné")
    if note.id_trimestre is not None:
        trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == note.id_trimestre).first()
        if not trimestre:
            raise HTTPException(status_code=404, detail="Trimestre introuvable")
        if trimestre.verrouille:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Trimestre verrouillé",
            )


def _verifier_doublon(note, db: Session, exclure_id: Optional[int] = None):
    query = db.query(models.Notes).filter(
        models.Notes.matricule_eleve == note.matricule_eleve,
        models.Notes.id_cours == note.id_cours,
    )
    if note.id_trimestre is not None:
        query = query.filter(models.Notes.id_trimestre == note.id_trimestre)
    else:
        query = query.filter(models.Notes.id_trimestre.is_(None))
    if exclure_id is not None:
        query = query.filter(models.Notes.id != exclure_id)
    if query.first():
        raise HTTPException(status_code=409, detail="Note déjà existante")


def _trouver_classe(db: Session, id_classe: int):
    classe = db.query(models.Classes).filter(models.Classes.id == id_classe).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    return classe


def _valider_bareme(classe, note: float, note_classe: Optional[float]):
    if est_jardin(classe.niveau):
        raise HTTPException(
            status_code=400,
            detail="Les sections du jardin d'enfants sont évaluées par appréciation manuelle, pas par notes.",
        )
    bareme = bareme_niveau(classe.niveau)
    if note > bareme:
        raise HTTPException(status_code=422, detail="Note dépasse le barème")
    if note_classe is not None and note_classe > bareme:
        raise HTTPException(status_code=422, detail="Note de classe dépasse le barème")


def _creer_note(note: schemas.NoteCreate, db: Session):
    _verifier_references(note, db)
    classe = _trouver_classe(db, note.id_classe)
    _valider_bareme(classe, note.note, note.note_classe)
    _verifier_doublon(note, db)
    data = note.model_dump()
    data.pop("id", None)  # NoteBulkItem transporte un `id` optionnel à ignorer à la création
    data["date"] = now_utc().date()
    nouvelle_note = models.Notes(**data)
    db.add(nouvelle_note)
    db.commit()
    db.refresh(nouvelle_note)
    return nouvelle_note


def _modifier_note(note_id: int, note: schemas.NoteCreate, db: Session):
    db_note = db.query(models.Notes).filter(models.Notes.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note introuvable")

    _verifier_references(note, db)
    classe = _trouver_classe(db, note.id_classe)
    _valider_bareme(classe, note.note, note.note_classe)
    _verifier_doublon(note, db, exclure_id=note_id)

    for key, value in note.model_dump().items():
        setattr(db_note, key, value)
    db_note.updated_at = now_utc()
    db.commit()
    db.refresh(db_note)
    return db_note


@router.post("/", response_model=schemas.NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    if note.id_trimestre is not None:
        tr = db.query(models.Trimestres).filter(models.Trimestres.id == note.id_trimestre).first()
        if tr is not None and tr.annee_scolaire is not None and tr.annee_scolaire.cloturee:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=(
                    "Année scolaire clôturée : toute saisie de note est bloquée. "
                    "Rouvrez l'année pour pouvoir enregistrer."
                ),
            )
    return _creer_note(note, db)


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


@router.get("/registre", response_model=schemas.RegistreNotesResponse)
def get_registre_notes(
    classe_id: int = Query(..., description="Identifiant de la classe"),
    cours_id: int = Query(..., description="Identifiant de la matière"),
    annee_id: int = Query(..., description="Identifiant de l'année scolaire"),
    db: Session = Depends(get_db),
):
    """Registre de notes d'une matière : chaque élève × toutes les périodes de l'année."""
    from services.registre_notes import registre_notes

    try:
        return registre_notes(db, classe_id, cours_id, annee_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{note_id}", response_model=schemas.NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(models.Notes).options(*_EAGER).filter(models.Notes.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note introuvable")
    return db_note


@router.put("/{note_id}", response_model=schemas.NoteResponse)
def update_note(note_id: int, note_update: schemas.NoteCreate, db: Session = Depends(get_db)):
    return _modifier_note(note_id, note_update, db)


@router.patch("/{note_id}", response_model=schemas.NoteResponse)
def patch_note(note_id: int, note_update: schemas.NotePatch, db: Session = Depends(get_db)):
    """Mise à jour partielle (Type D — sauvegarde auto à chaque blur)."""
    db_note = db.query(models.Notes).filter(models.Notes.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note introuvable")

    changes = note_update.model_dump(exclude_unset=True)
    merged = schemas.NoteCreate(
        matricule_eleve=changes.get("matricule_eleve", db_note.matricule_eleve),
        id_cours=changes.get("id_cours", db_note.id_cours),
        id_classe=changes.get("id_classe", db_note.id_classe),
        matricule_enseignant=changes.get("matricule_enseignant", db_note.matricule_enseignant),
        id_trimestre=changes.get("id_trimestre", db_note.id_trimestre),
        note=changes.get("note", db_note.note),
        note_classe=changes.get("note_classe", db_note.note_classe),
    )
    _verifier_references(merged, db)
    classe = _trouver_classe(db, merged.id_classe)
    _valider_bareme(classe, merged.note, merged.note_classe)
    _verifier_doublon(merged, db, exclure_id=note_id)

    for key, value in changes.items():
        setattr(db_note, key, value)
    db_note.updated_at = now_utc()
    db.commit()
    db.refresh(db_note)
    return db_note


@router.post("/bulk", response_model=schemas.NoteBulkResponse)
def bulk_notes(payload: schemas.NoteBulkRequest, db: Session = Depends(get_db)):
    """Sauvegarde groupée (Type D — Enregistrer tout) : création ou mise à jour en un lot."""
    enregistrees: list = []
    creees = 0
    modifiees = 0
    for item in payload.notes:
        if item.id is not None:
            enregistrees.append(_modifier_note(item.id, item, db))
            modifiees += 1
        else:
            enregistrees.append(_creer_note(item, db))
            creees += 1
    return schemas.NoteBulkResponse(notes=enregistrees, creees=creees, modifiees=modifiees)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(models.Notes).filter(models.Notes.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note introuvable")
    if db_note.id_trimestre:
        trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == db_note.id_trimestre).first()
        if trimestre and trimestre.verrouille:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Trimestre verrouillé")
    db.delete(db_note)
    db.commit()
    return None
