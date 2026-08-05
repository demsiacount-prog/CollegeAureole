from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
from database import get_db
import models
import schemas
from security import get_current_user, require_role
from bareme import appreciation_for_moyenne, bareme_niveau

router = APIRouter(prefix="/api/bulletins", tags=["Bulletins"], dependencies=[Depends(get_current_user)])


def _calculer_bulletin(db: Session, matricule_eleve: str, id_trimestre: int) -> dict:
    """Calcule la moyenne générale pondérée par le COEFFICIENT de chaque matière
    dans la classe de l'élève (et non plus par le volume horaire du cours)."""
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule_eleve).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable.")

    trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == id_trimestre).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable.")

    if not eleve.classe_id:
        raise HTTPException(
            status_code=400,
            detail="Cet élève n'est rattaché à aucune classe, impossible de générer un bulletin.",
        )

    # Cours attendus pour cette classe (avec leur coefficient)
    affectations_classe = (
        db.query(models.AffectationCoursClasse)
        .filter(models.AffectationCoursClasse.id_classe == eleve.classe_id)
        .all()
    )
    coefficients_par_cours = {a.id_cours: a.coefficient for a in affectations_classe}

    moyennes_par_cours = (
        db.query(models.Notes.id_cours, func.avg(models.Notes.note).label("moyenne"))
        .filter(
            models.Notes.matricule_eleve == matricule_eleve,
            models.Notes.id_trimestre == id_trimestre,
        )
        .group_by(models.Notes.id_cours)
        .all()
    )

    if not moyennes_par_cours:
        raise HTTPException(
            status_code=400,
            detail="Aucune note trouvée pour cet élève sur ce trimestre, impossible de générer le bulletin.",
        )

    # Blocage si un cours de la classe n'a aucune note saisie pour cet élève
    cours_notes = {id_cours for id_cours, _ in moyennes_par_cours}
    cours_manquants = [
        id_cours for id_cours in coefficients_par_cours if id_cours not in cours_notes
    ]
    if cours_manquants:
        # db.get() (API SQLAlchemy 2.0) au lieu de Query.get(), dépréciée, et une
        # seule requête pour tous les cours manquants au lieu d'une par cours.
        cours_manquants_map = {
            c.id: c for c in db.query(models.Cours).filter(models.Cours.id.in_(cours_manquants)).all()
        }
        noms = [
            cours_manquants_map[cid].nom if cid in cours_manquants_map else str(cid)
            for cid in cours_manquants
        ]
        raise HTTPException(
            status_code=400,
            detail=f"Notes manquantes pour : {', '.join(noms)}. Génération du bulletin impossible.",
        )

    details = []
    total_pondere = 0.0
    total_coefficients = 0.0

    for id_cours, moyenne in moyennes_par_cours:
        coefficient = coefficients_par_cours.get(id_cours)
        if coefficient is None:
            # Cours noté mais non affecté à la classe actuelle (ex: changement de classe en cours d'année) : ignoré
            continue
        details.append({
            "id_cours": id_cours,
            "moyenne": round(float(moyenne), 2),
            "coefficient": coefficient,
        })
        total_pondere += float(moyenne) * coefficient
        total_coefficients += coefficient

    moyenne_generale = round(total_pondere / total_coefficients, 2) if total_coefficients else 0.0

    classe = db.query(models.Classes).filter(models.Classes.id == eleve.classe_id).first()
    bareme = bareme_niveau(classe.niveau) if classe else 20

    return {
        "matricule_eleve": matricule_eleve,
        "id_trimestre": id_trimestre,
        "id_classe": eleve.classe_id,
        "moyenne_generale": moyenne_generale,
        "appreciation": appreciation_for_moyenne(moyenne_generale, bareme),
        "details": details,
    }


def _upsert_bulletin(db: Session, calcul: dict) -> models.Bulletins:
    bulletin = (
        db.query(models.Bulletins)
        .filter(
            models.Bulletins.matricule_eleve == calcul["matricule_eleve"],
            models.Bulletins.id_trimestre == calcul["id_trimestre"],
        )
        .first()
    )

    if bulletin and bulletin.statut == "PUBLIE":
        raise HTTPException(
            status_code=409,
            detail="Ce bulletin a déjà été publié. Dépubliez-le avant de le régénérer.",
        )

    if bulletin:
        bulletin.moyenne_generale = calcul["moyenne_generale"]
        bulletin.appreciation = calcul["appreciation"]
        bulletin.id_classe = calcul["id_classe"]
        db.query(models.BulletinDetails).filter(
            models.BulletinDetails.id_bulletin == bulletin.id
        ).delete()
    else:
        bulletin = models.Bulletins(
            matricule_eleve=calcul["matricule_eleve"],
            id_trimestre=calcul["id_trimestre"],
            id_classe=calcul["id_classe"],
            moyenne_generale=calcul["moyenne_generale"],
            appreciation=calcul["appreciation"],
            statut="BROUILLON",
        )
        db.add(bulletin)

    db.flush()

    for detail in calcul["details"]:
        db.add(
            models.BulletinDetails(
                id_bulletin=bulletin.id,
                id_cours=detail["id_cours"],
                moyenne=detail["moyenne"],
                coefficient=detail["coefficient"],
            )
        )

    db.flush()
    return bulletin


def _calculer_rangs_classe(db: Session, id_classe: int, id_trimestre: int) -> None:
    bulletins = (
        db.query(models.Bulletins)
        .filter(
            models.Bulletins.id_classe == id_classe,
            models.Bulletins.id_trimestre == id_trimestre,
            models.Bulletins.statut == "PUBLIE",
        )
        .order_by(models.Bulletins.moyenne_generale.desc())
        .all()
    )
    for index, bulletin in enumerate(bulletins, start=1):
        bulletin.rang = index


@router.post("/generer", response_model=schemas.BulletinResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def generer_bulletin(payload: schemas.BulletinGenerateRequest, db: Session = Depends(get_db)):
    calcul = _calculer_bulletin(db, payload.matricule_eleve, payload.id_trimestre)
    bulletin = _upsert_bulletin(db, calcul)
    _calculer_rangs_classe(db, calcul["id_classe"], calcul["id_trimestre"])
    db.commit()
    db.refresh(bulletin)
    return bulletin


@router.post("/generer-classe", response_model=List[schemas.BulletinResponse], status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role("admin", "directeur"))])
def generer_bulletins_classe(payload: schemas.BulletinGenerateClasseRequest, db: Session = Depends(get_db)):
    classe = db.query(models.Classes).filter(models.Classes.id == payload.id_classe).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable.")
    if not db.query(models.Trimestres).filter(models.Trimestres.id == payload.id_trimestre).first():
        raise HTTPException(status_code=404, detail="Trimestre introuvable.")

    eleves = db.query(models.Eleves).filter(models.Eleves.classe_id == payload.id_classe).all()

    bulletins_generes, erreurs = [], []
    for eleve in eleves:
        try:
            calcul = _calculer_bulletin(db, eleve.matricule, payload.id_trimestre)
            bulletins_generes.append(_upsert_bulletin(db, calcul))
        except HTTPException as exc:
            erreurs.append({"matricule_eleve": eleve.matricule, "detail": exc.detail})

    _calculer_rangs_classe(db, payload.id_classe, payload.id_trimestre)
    db.commit()
    for bulletin in bulletins_generes:
        db.refresh(bulletin)

    if erreurs and not bulletins_generes:
        raise HTTPException(status_code=400, detail=f"Aucun bulletin n'a pu être généré. Détails : {erreurs}")

    return bulletins_generes


@router.post("/publier", response_model=List[schemas.BulletinResponse], dependencies=[Depends(require_role("admin", "directeur"))])
def publier_bulletins_classe(payload: schemas.BulletinPublierRequest, db: Session = Depends(get_db)):
    """Verrouille les bulletins d'une classe/trimestre : ils deviennent visibles
    et ne peuvent plus être régénérés sans dépublication explicite."""
    bulletins = (
        db.query(models.Bulletins)
        .filter(models.Bulletins.id_classe == payload.id_classe, models.Bulletins.id_trimestre == payload.id_trimestre)
        .all()
    )
    if not bulletins:
        raise HTTPException(status_code=404, detail="Aucun bulletin à publier pour cette classe/trimestre.")
    for b in bulletins:
        b.statut = "PUBLIE"
        b.published_at = datetime.utcnow()
    db.flush()
    _calculer_rangs_classe(db, payload.id_classe, payload.id_trimestre)
    db.commit()
    for b in bulletins:
        db.refresh(b)
    return bulletins


@router.post("/depublier", response_model=List[schemas.BulletinResponse], dependencies=[Depends(require_role("admin", "directeur"))])
def depublier_bulletins_classe(payload: schemas.BulletinPublierRequest, db: Session = Depends(get_db)):
    bulletins = (
        db.query(models.Bulletins)
        .filter(models.Bulletins.id_classe == payload.id_classe, models.Bulletins.id_trimestre == payload.id_trimestre)
        .all()
    )
    for b in bulletins:
        b.statut = "BROUILLON"
        b.published_at = None
        b.rang = None
    db.commit()
    for b in bulletins:
        db.refresh(b)
    return bulletins


@router.get("/", response_model=List[schemas.BulletinResponse])
def get_all_bulletins(
    matricule_eleve: Optional[str] = None,
    id_classe: Optional[int] = None,
    id_trimestre: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    # BulletinResponse imbrique details -> cours_nom (via detail.cours) : sans
    # eager loading, chaque détail de bulletin déclenche une requête supplémentaire.
    query = db.query(models.Bulletins).options(
        joinedload(models.Bulletins.eleve),
        joinedload(models.Bulletins.details).joinedload(models.BulletinDetails.cours)
    )
    if matricule_eleve:
        query = query.filter(models.Bulletins.matricule_eleve == matricule_eleve)
    if id_classe:
        query = query.filter(models.Bulletins.id_classe == id_classe)
    if id_trimestre:
        query = query.filter(models.Bulletins.id_trimestre == id_trimestre)
    return query.order_by(models.Bulletins.rang.asc().nullslast()).offset(skip).limit(limit).all()


@router.get("/{bulletin_id}", response_model=schemas.BulletinDetailFullResponse)
def get_bulletin(bulletin_id: int, db: Session = Depends(get_db)):
    bulletin = (
        db.query(models.Bulletins)
        .options(
            joinedload(models.Bulletins.details).joinedload(models.BulletinDetails.cours),
            joinedload(models.Bulletins.eleve),
            joinedload(models.Bulletins.trimestre),
            joinedload(models.Bulletins.classe),
        )
        .filter(models.Bulletins.id == bulletin_id)
        .first()
    )
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin introuvable")
    return bulletin


@router.delete("/{bulletin_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role("admin"))])
def delete_bulletin(bulletin_id: int, db: Session = Depends(get_db)):
    bulletin = db.query(models.Bulletins).filter(models.Bulletins.id == bulletin_id).first()
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin introuvable")
    db.delete(bulletin)
    db.commit()
    return None
