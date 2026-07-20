from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from database import get_db
import models
import schemas
from security import get_current_user, require_role

router = APIRouter(prefix="/api/eleves", tags=["Élèves"], dependencies=[Depends(get_current_user)])


def _verifier_capacite_classe(db: Session, id_classe: int, matricule_a_exclure: Optional[str] = None):
    classe = db.query(models.Classes).filter(models.Classes.id == id_classe).first()
    if not classe:
        raise HTTPException(status_code=404, detail="La classe spécifiée n'existe pas.")
    if classe.capacite_max is None:
        return  # pas de limite définie
    effectif = db.query(models.Eleves).filter(
        models.Eleves.classe_id == id_classe,
        models.Eleves.statut == "actif",
        models.Eleves.matricule != (matricule_a_exclure or ""),
    ).count()
    if effectif >= classe.capacite_max:
        raise HTTPException(
            status_code=400,
            detail=f"Capacité maximale atteinte pour la classe {classe.niveau} {classe.nom} "
                   f"({effectif}/{classe.capacite_max}).",
        )


class EleveUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    lieu_de_naissance: Optional[str] = None
    adresse: Optional[str] = None
    classe_id: Optional[int] = None
    statut: Optional[str] = None
    photo: Optional[str] = None


@router.post("/", response_model=schemas.EleveResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def create_eleve(eleve: schemas.EleveCreate, db: Session = Depends(get_db)):
    if not db.query(models.Tuteurs).filter(models.Tuteurs.id == eleve.tuteur_id).first():
        raise HTTPException(status_code=404, detail="Le tuteur spécifié n'existe pas.")
    if eleve.classe_id:
        _verifier_capacite_classe(db, eleve.classe_id)

    nouveau_eleve = models.Eleves(**eleve.model_dump())
    db.add(nouveau_eleve)
    db.commit()
    db.refresh(nouveau_eleve)
    return nouveau_eleve


@router.get("/", response_model=List[schemas.EleveResponse])
def get_all_eleves(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
):
    # joinedload évite le N+1 : sans lui, sérialiser N élèves déclenche
    # N requêtes supplémentaires (tuteur + classe) car EleveResponse imbrique ces relations.
    return (
        db.query(models.Eleves)
        .options(joinedload(models.Eleves.tuteur), joinedload(models.Eleves.classe_relation))
        .order_by(models.Eleves.matricule)
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.put("/{matricule}", response_model=schemas.EleveResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def update_eleve(matricule: str, payload: EleveUpdate, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")

    donnees = payload.model_dump(exclude_unset=True)
    if "classe_id" in donnees and donnees["classe_id"] and donnees["classe_id"] != eleve.classe_id:
        _verifier_capacite_classe(db, donnees["classe_id"], matricule_a_exclure=matricule)

    for key, value in donnees.items():
        setattr(eleve, key, value)

    db.commit()
    db.refresh(eleve)
    return eleve


@router.get("/{matricule}", response_model=schemas.EleveResponse)
def get_eleve(matricule: str, db: Session = Depends(get_db)):
    eleve = (
        db.query(models.Eleves)
        .options(joinedload(models.Eleves.tuteur), joinedload(models.Eleves.classe_relation))
        .filter(models.Eleves.matricule == matricule)
        .first()
    )
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    return eleve


@router.patch("/{matricule}/desactiver", response_model=schemas.EleveResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def desactiver_eleve(matricule: str, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    eleve.statut = "inactif"
    db.commit()
    db.refresh(eleve)
    return eleve


@router.patch("/{matricule}/activer", response_model=schemas.EleveResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def activer_eleve(matricule: str, db: Session = Depends(get_db)):
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")
    if eleve.classe_id:
        _verifier_capacite_classe(db, eleve.classe_id, matricule_a_exclure=matricule)
    eleve.statut = "actif"
    db.commit()
    db.refresh(eleve)
    return eleve


# ─── Dossier complet (fiche élève) ─────────────────────────────────────────────
# Reconstruit à partir des schémas existants (DossierEleveResponse,
# InscriptionDetailResponse, MoyenneTrimestre, NoteParMatiere), qui étaient déjà
# définis et importés mais que rien n'exposait : il manquait ce endpoint.

def _moyenne_annuelle(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> Optional[float]:
    bulletins = (
        db.query(models.Bulletins)
        .join(models.Trimestres, models.Bulletins.id_trimestre == models.Trimestres.id)
        .filter(
            models.Bulletins.matricule_eleve == matricule_eleve,
            models.Trimestres.annee_scolaire_id == id_annee_scolaire,
        )
        .all()
    )
    if not bulletins:
        return None
    return round(sum(b.moyenne_generale for b in bulletins) / len(bulletins), 2)


def _moyennes_par_trimestre(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> List["schemas.MoyenneTrimestre"]:
    trimestres = (
        db.query(models.Trimestres)
        .filter(models.Trimestres.annee_scolaire_id == id_annee_scolaire)
        .order_by(models.Trimestres.date_debut.asc())
        .all()
    )
    resultats = []
    for numero, trimestre in enumerate(trimestres, start=1):
        bulletin = (
            db.query(models.Bulletins)
            .filter(
                models.Bulletins.matricule_eleve == matricule_eleve,
                models.Bulletins.id_trimestre == trimestre.id,
            )
            .first()
        )
        resultats.append(schemas.MoyenneTrimestre(
            numero=numero,
            periode=trimestre.nom,
            moyenne=bulletin.moyenne_generale if bulletin else None,
        ))
    return resultats


def _notes_par_matiere(db: Session, matricule_eleve: str, id_annee_scolaire: int) -> List["schemas.NoteParMatiere"]:
    resultats = (
        db.query(models.Cours.nom, func.count(models.Notes.id), func.avg(models.Notes.note))
        .join(models.Notes, models.Notes.id_cours == models.Cours.id)
        .join(models.Trimestres, models.Notes.id_trimestre == models.Trimestres.id)
        .filter(
            models.Notes.matricule_eleve == matricule_eleve,
            models.Trimestres.annee_scolaire_id == id_annee_scolaire,
        )
        .group_by(models.Cours.nom)
        .all()
    )
    return [
        schemas.NoteParMatiere(matiere=nom, nb_notes=nb, moyenne=round(float(moy), 2) if moy is not None else None)
        for nom, nb, moy in resultats
    ]


def _construire_inscription_enrichie(db: Session, inscription: models.Inscriptions) -> "schemas.InscriptionDetailResponse":
    annee = inscription.annee_scolaire
    nb_absences = 0
    if annee:
        nb_absences = (
            db.query(func.count(models.Absences.id))
            .filter(
                models.Absences.matricule_eleve == inscription.matricule_eleve,
                models.Absences.date_absence >= annee.date_debut,
                models.Absences.date_absence <= annee.date_fin,
            )
            .scalar()
            or 0
        )

    montant_paye = sum((e.montant_paye or 0.0) for e in inscription.echeances)
    reste_a_payer = sum(e.reste_a_payer for e in inscription.echeances)

    base = schemas.InscriptionResponse.model_validate(inscription).model_dump()
    return schemas.InscriptionDetailResponse(
        **base,
        classe=inscription.classe,
        annee_scolaire=annee,
        eleve=inscription.eleve,
        nb_absences=nb_absences,
        moyenne_annuelle=_moyenne_annuelle(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else None,
        moyennes_par_trimestre=_moyennes_par_trimestre(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else [],
        paiements=inscription.paiements,
        montant_paye=montant_paye,
        reste_a_payer=reste_a_payer,
        notes_par_matiere=_notes_par_matiere(db, inscription.matricule_eleve, inscription.id_annee_scolaire) if annee else [],
    )


@router.get("/{matricule}/dossier", response_model=schemas.DossierEleveResponse)
def get_dossier_eleve(matricule: str, db: Session = Depends(get_db)):
    """Fiche complète d'un élève : profil, historique d'inscriptions (avec
    finances et moyennes), notes, absences et bulletins."""
    eleve = (
        db.query(models.Eleves)
        .options(joinedload(models.Eleves.tuteur), joinedload(models.Eleves.classe_relation))
        .filter(models.Eleves.matricule == matricule)
        .first()
    )
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève non trouvé")

    inscriptions = (
        db.query(models.Inscriptions)
        .options(
            joinedload(models.Inscriptions.classe),
            joinedload(models.Inscriptions.annee_scolaire),
            joinedload(models.Inscriptions.paiements),
            joinedload(models.Inscriptions.echeances),
        )
        .filter(models.Inscriptions.matricule_eleve == matricule)
        .join(models.AnneesScolaires)
        .order_by(models.AnneesScolaires.date_debut.desc())
        .all()
    )
    inscriptions_enrichies = [_construire_inscription_enrichie(db, insc) for insc in inscriptions]

    notes = (
        db.query(models.Notes)
        .options(
            joinedload(models.Notes.cours),
            joinedload(models.Notes.classe),
            joinedload(models.Notes.enseignant),
            joinedload(models.Notes.trimestre),
        )
        .filter(models.Notes.matricule_eleve == matricule)
        .order_by(models.Notes.date.desc())
        .all()
    )
    absences = (
        db.query(models.Absences)
        .options(joinedload(models.Absences.cours))
        .filter(models.Absences.matricule_eleve == matricule)
        .order_by(models.Absences.date_absence.desc())
        .all()
    )
    bulletins = (
        db.query(models.Bulletins)
        .options(joinedload(models.Bulletins.details))
        .filter(models.Bulletins.matricule_eleve == matricule)
        .order_by(models.Bulletins.generated_at.desc())
        .all()
    )
    annee_active = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()  # noqa: E712

    # On valide d'abord l'élève seul (respecte le validation_alias classe_relation -> classe),
    # puis on complète avec les listes déjà construites via model_copy plutôt que par des kwargs
    # (passer classe=... directement au constructeur serait ignoré : le champ n'accepte que
    # son alias de validation en entrée, pas son nom de champ, tant que populate_by_name n'est
    # pas activé sur le schéma).
    dossier = schemas.DossierEleveResponse.model_validate(eleve)
    return dossier.model_copy(update={
        "inscriptions": inscriptions_enrichies,
        "notes": [schemas.NoteResponse.model_validate(n) for n in notes],
        "absences": [schemas.AbsenceResponse.model_validate(a) for a in absences],
        "bulletins": [schemas.BulletinResponse.model_validate(b) for b in bulletins],
        "annee_scolaire": schemas.AnneeScolaireResponse.model_validate(annee_active) if annee_active else None,
    })
