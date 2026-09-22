from timeutils import now_utc
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from database import get_db
import models
import schemas
from security import get_current_user
from bareme import bareme_niveau, est_jardin
from helpers import get_annee_ou_active
from schemas.notes import NoteSaisieAutoriseeResponse, NoteSaisieTrimestre

router = APIRouter(prefix="/api/notes", tags=["Notes"], dependencies=[Depends(get_current_user)])

# NoteResponse imbrique eleve + cours + classe + enseignant + trimestre : sans
# eager loading, chaque note sérialisée coûte jusqu'à 5 requêtes SQL supplémentaires.
_EAGER = (
    joinedload(models.Notes.eleve),
    joinedload(models.Notes.cours),
    joinedload(models.Notes.classe),
    joinedload(models.Notes.enseignant),
    joinedload(models.Notes.trimestre).joinedload(models.Trimestres.annee_scolaire),
)


def _verifier_trimestre_ecriture(note, db: Session) -> None:
    """Verrouillage d'écriture : toute note est rattachée à UN trimestre.

    - absent → 422 : impossible de savoir si la période est saisissable ;
    - introuvable → 404 ;
    - trimestre verrouillé → 423 : saisie bloquée pour cette période ;
    - trimestre rattaché à une année clôturée → 423 : bloqué.
    """
    if note.id_trimestre is None:
        raise HTTPException(
            status_code=422,
            detail="id_trimestre requis : une note doit être rattachée à une période.",
        )
    trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == note.id_trimestre).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable")
    if trimestre.verrouille:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Trimestre verrouillé",
        )
    annee = (
        db.query(models.AnneesScolaires)
        .filter(models.AnneesScolaires.id == trimestre.annee_scolaire_id)
        .first()
    )
    if annee is not None and annee.cloturee:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=(
                "Année scolaire clôturée : toute saisie de note est bloquée. "
                "Rouvrez l'année pour pouvoir enregistrer."
            ),
        )


def _verifier_references(note, db: Session):
    _verifier_trimestre_ecriture(note, db)
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


def _valider_bareme(classe, note: Optional[float], note_classe: Optional[float]):
    if est_jardin(classe.niveau):
        raise HTTPException(
            status_code=400,
            detail="Les sections du jardin d'enfants sont évaluées par appréciation manuelle, pas par notes.",
        )
    bareme = bareme_niveau(classe.niveau)
    if note is not None and note > bareme:
        raise HTTPException(status_code=422, detail="Note dépasse le barème")
    if note_classe is not None and note_classe > bareme:
        raise HTTPException(status_code=422, detail="Note de classe dépasse le barème")


def _peut_saisir_note(note, db: Session) -> bool:
    """Vrai si la note est rééditable (trimestre non verrouillé, année non clôturée)."""
    if note.id_trimestre is None:
        return True
    trimestre = note.trimestre
    if trimestre is None:
        trimestre = db.query(models.Trimestres).options(
            joinedload(models.Trimestres.annee_scolaire)
        ).filter(models.Trimestres.id == note.id_trimestre).first()
    if trimestre is None:
        return True
    if trimestre.verrouille:
        return False
    if trimestre.annee_scolaire is not None and trimestre.annee_scolaire.cloturee:
        return False
    return True


def _creer_note(note: schemas.NoteCreate, db: Session, commit: bool = True):
    """Création idempotente (upsert).

    Si une note existe déjà pour le même (élève, cours, trimestre), elle est
    mise à jour au lieu de lever un conflit. Règle la course entre
    l'auto-enregistrement au perte de focus et la sauvegarde manuelle
    (double soumission → double création → 409).
    """
    _verifier_references(note, db)
    classe = _trouver_classe(db, note.id_classe)
    _valider_bareme(classe, note.note, note.note_classe)

    query = db.query(models.Notes).filter(
        models.Notes.matricule_eleve == note.matricule_eleve,
        models.Notes.id_cours == note.id_cours,
    )
    query = query.filter(models.Notes.id_trimestre == note.id_trimestre)
    existante = query.first()

    if existante is not None:
        for key, value in note.model_dump().items():
            if key == "id":
                continue
            setattr(existante, key, value)
        existante.updated_at = now_utc()
        if commit:
            db.commit()
            db.refresh(existante)
        else:
            db.flush()  # rend l'objet exploitable (id, etc.) sans valider la transaction
        existante.peut_saisir = _peut_saisir_note(existante, db)
        return existante, False

    data = note.model_dump()
    data.pop("id", None)  # NoteBulkItem transporte un `id` optionnel à ignorer à la création
    data["date"] = now_utc().date()
    nouvelle_note = models.Notes(**data)
    db.add(nouvelle_note)
    if commit:
        db.commit()
        db.refresh(nouvelle_note)
    else:
        db.flush()  # rend l'objet exploitable (id, etc.) sans valider la transaction
    nouvelle_note.peut_saisir = _peut_saisir_note(nouvelle_note, db)
    return nouvelle_note, True


def _modifier_note(note_id: int, note: schemas.NoteCreate, db: Session, commit: bool = True):
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
    if commit:
        db.commit()
        db.refresh(db_note)
    else:
        db.flush()
    db_note.peut_saisir = _peut_saisir_note(db_note, db)
    return db_note


@router.post("/", response_model=schemas.NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    nouvelle_note, _ = _creer_note(note, db)
    return nouvelle_note


@router.get("/", response_model=List[schemas.NoteResponse])
def get_all_notes(
    matricule_eleve: Optional[str] = None,
    id_classe: Optional[int] = None,
    id_cours: Optional[int] = None,
    id_trimestre: Optional[int] = None,
    annee_id: Optional[int] = Query(None, description="Filtrer par année scolaire (défaut : active)"),
    id_annee_scolaire: Optional[int] = Query(None, description="Alias de `annee_id` (consultation d'une année passée)"),
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(models.Notes).options(*_EAGER)

    if annee_id is None:
        annee_id = id_annee_scolaire
    if annee_id is not None:
        # Filtrer les notes dont le trimestre appartient à cette année
        query = query.join(
            models.Trimestres,
            models.Notes.id_trimestre == models.Trimestres.id
        ).filter(
            models.Trimestres.annee_scolaire_id == annee_id
        )

    if matricule_eleve:
        query = query.filter(models.Notes.matricule_eleve == matricule_eleve)
    if id_classe:
        query = query.filter(models.Notes.id_classe == id_classe)
    if id_cours:
        query = query.filter(models.Notes.id_cours == id_cours)
    if id_trimestre:
        query = query.filter(models.Notes.id_trimestre == id_trimestre)

    notes = query.order_by(models.Notes.id).offset(skip).limit(limit).all()
    for note in notes:
        note.peut_saisir = _peut_saisir_note(note, db)
    return notes


@router.get("/saisie-autorisee", response_model=NoteSaisieAutoriseeResponse)
def get_saisie_autorisee(
    annee_id: Optional[int] = Query(None, description="Année à consulter (défaut : active)"),
    db: Session = Depends(get_db),
):
    """État de saisie par trimestre de l'année (verrou/saisie autorisée).

    Le verrouillage est global par trimestre (verrouillé / année clôturée) :
    le front peut désactiver les champs de notes ET masquer les messages de
    conflit sur cette seule réponse, sans lire note par note.
    """
    annee = get_annee_ou_active(db, annee_id)
    trimestres = (
        db.query(models.Trimestres)
        .filter(models.Trimestres.annee_scolaire_id == annee.id)
        .order_by(models.Trimestres.date_debut.asc())
        .all()
    )
    liste = []
    for tr in trimestres:
        peut = (not tr.verrouille) and (not annee.cloturee)
        liste.append(NoteSaisieTrimestre(
            id=tr.id,
            nom=tr.nom,
            type=tr.type,
            verrouille=bool(tr.verrouille),
            annee_cloturee=bool(annee.cloturee),
            peut_saisir=peut,
        ))
    return NoteSaisieAutoriseeResponse(
        annee_id=annee.id,
        annee_libelle=annee.libelle,
        annee_cloturee=bool(annee.cloturee),
        trimestres=liste,
        peut_saisir=(not annee.cloturee) and any(t.peut_saisir for t in liste),
    )


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
    db_note.peut_saisir = _peut_saisir_note(db_note, db)
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
    id_trimestre = changes.get("id_trimestre", db_note.id_trimestre)
    if id_trimestre is None:
        raise HTTPException(
            status_code=422,
            detail="id_trimestre requis : une note doit être rattachée à une période.",
        )
    merged_note = changes.get("note", db_note.note)
    merged_note_classe = changes.get("note_classe", db_note.note_classe)
    if merged_note is None and merged_note_classe is None:
        raise HTTPException(
            status_code=422,
            detail="Au moins une note (note ou note_classe) est requise",
        )
    merged = schemas.NoteCreate(
        matricule_eleve=changes.get("matricule_eleve", db_note.matricule_eleve),
        id_cours=changes.get("id_cours", db_note.id_cours),
        id_classe=changes.get("id_classe", db_note.id_classe),
        matricule_enseignant=changes.get("matricule_enseignant", db_note.matricule_enseignant),
        id_trimestre=id_trimestre,
        note=merged_note,
        note_classe=merged_note_classe,
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
    db_note.peut_saisir = _peut_saisir_note(db_note, db)
    return db_note


@router.post("/bulk", response_model=schemas.NoteBulkResponse)
def bulk_notes(payload: schemas.NoteBulkRequest, db: Session = Depends(get_db)):
    """Sauvegarde groupée (Type D — Enregistrer tout) : création ou mise à jour en un lot.

    FIX BUG CRITIQUE (incohérence) : chaque note committait individuellement,
    donc si un élément du lot échouait (doublon, référence invalide...), les
    précédents restaient enregistrés alors que l'appel global renvoyait une
    erreur — l'enseignant croit que rien n'a été sauvegardé et resaisit,
    créant des doublons. Le lot est maintenant tout-ou-rien : un seul commit
    à la fin, rollback complet en cas d'échec sur n'importe quel élément.
    """
    enregistrees: list = []
    creees = 0
    modifiees = 0
    try:
        for item in payload.notes:
            if item.id is not None:
                enregistrees.append(_modifier_note(item.id, item, db, commit=False))
                modifiees += 1
            else:
                note_obj, creee = _creer_note(item, db, commit=False)
                enregistrees.append(note_obj)
                if creee:
                    creees += 1
                else:
                    modifiees += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    for note in enregistrees:
        db.refresh(note)
        note.peut_saisir = _peut_saisir_note(note, db)
    return schemas.NoteBulkResponse(notes=enregistrees, creees=creees, modifiees=modifiees)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    db_note = db.query(models.Notes).filter(models.Notes.id == note_id).first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note introuvable")
    if db_note.id_trimestre:
        trimestre = db.query(models.Trimestres).options(
            joinedload(models.Trimestres.annee_scolaire)
        ).filter(models.Trimestres.id == db_note.id_trimestre).first()
        if trimestre and trimestre.verrouille:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Trimestre verrouillé")
        if trimestre and trimestre.annee_scolaire and trimestre.annee_scolaire.cloturee:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Année scolaire clôturée : suppression de note bloquée.",
            )
    db.delete(db_note)
    db.commit()
    return None
