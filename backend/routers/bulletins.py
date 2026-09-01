from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from timeutils import now_utc
from database import get_db
import models
import schemas
from security import get_current_user, require_role
from bareme import appreciation_for_moyenne, bareme_niveau
from services import pdf as pdf_service

router = APIRouter(prefix="/api/bulletins", tags=["Bulletins"], dependencies=[Depends(get_current_user)])


def _calculer_bulletin(db: Session, matricule_eleve: str, id_trimestre: int) -> dict:
    """Calcule la moyenne générale de la période.

    Règle métier :
    - EF1 (1ère–6ème Année, barème /10) : notes sur 10, moyennes SIMPLES,
      aucun coefficient ;
    - EF2/lycée (barème /20) : moyennes pondérées par le coefficient de
      chaque matière dans la classe de l'élève.

    Les détails stockent toujours la MOYENNE BRUTE de la matière (jamais
    note × coefficient) ; le produit s'affiche côté interface.
    """
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule_eleve).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")

    trimestre = db.query(models.Trimestres).filter(models.Trimestres.id == id_trimestre).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable")

    if not eleve.classe_id:
        raise HTTPException(
            status_code=400,
            detail="Classe introuvable",
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
            detail="Aucune note",
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
            detail=f"Notes manquantes pour : {', '.join(noms)}",
        )

    classe = db.query(models.Classes).filter(models.Classes.id == eleve.classe_id).first()
    bareme = bareme_niveau(classe.niveau) if classe else 20

    details = []
    total_pondere = 0.0
    total_coefficients = 0.0
    total_simple = 0.0
    nb_matieres = 0

    # EF1 (barème /10) : aucune pondération, moyenne simple des matières.
    est_ef1 = bareme == 10

    for id_cours, moyenne in moyennes_par_cours:
        coefficient = coefficients_par_cours.get(id_cours)
        if coefficient is None:
            # Cours noté mais non affecté à la classe actuelle (ex: changement de classe en cours d'année) : ignoré
            continue
        if est_ef1:
            coefficient = 1.0
        details.append({
            "id_cours": id_cours,
            "moyenne": round(float(moyenne), 2),
            "coefficient": coefficient,
        })
        total_pondere += round(float(moyenne), 2) * coefficient
        total_coefficients += coefficient
        total_simple += float(moyenne)
        nb_matieres += 1

    if est_ef1:
        moyenne_generale = round(total_simple / nb_matieres, 2) if nb_matieres else 0.0
    else:
        moyenne_generale = round(total_pondere / total_coefficients, 2) if total_coefficients else 0.0

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
            detail="Bulletin déjà publié",
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
    """Calcule le rang de tous les bulletins de la classe/trimestre, y compris
    les brouillons, afin de permettre un contrôle du classement avant publication."""
    bulletins = (
        db.query(models.Bulletins)
        .filter(
            models.Bulletins.id_classe == id_classe,
            models.Bulletins.id_trimestre == id_trimestre,
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
        raise HTTPException(status_code=404, detail="Classe introuvable")
    if not db.query(models.Trimestres).filter(models.Trimestres.id == payload.id_trimestre).first():
        raise HTTPException(status_code=404, detail="Trimestre introuvable")

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
        raise HTTPException(status_code=400, detail="Aucun bulletin généré")

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
        raise HTTPException(status_code=404, detail="Aucun bulletin à publier")
    for b in bulletins:
        b.statut = "PUBLIE"
        b.published_at = now_utc()
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


def _bulletin_avec_relations(db: Session, bulletin_id: int) -> models.Bulletins:
    """Charge un bulletin avec ses relations (détails+cours, élève, trimestre,
    classe) pour la génération du PDF — évite les requêtes N+1."""
    bulletin = (
        db.query(models.Bulletins)
        .options(
            joinedload(models.Bulletins.details).joinedload(models.BulletinDetails.cours),
            joinedload(models.Bulletins.eleve),
            joinedload(models.Bulletins.trimestre).joinedload(models.Trimestres.annee_scolaire),
            joinedload(models.Bulletins.classe),
        )
        .filter(models.Bulletins.id == bulletin_id)
        .first()
    )
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin introuvable")
    return bulletin


def _contexte_etablissement(db: Session):
    etab = db.query(models.Etablissement).first()
    return etab


@router.get("/pdf/{bulletin_id}")
def bulletins_pdf_un(bulletin_id: int, db: Session = Depends(get_db)):
    """PDF d'un seul bulletin (remplace l'impression navigateur)."""
    bulletin = _bulletin_avec_relations(db, bulletin_id)
    etab = _contexte_etablissement(db)
    annee_label = bulletin.trimestre.annee_scolaire.libelle if bulletin.trimestre.annee_scolaire else None

    effectif = (
        db.query(func.count(models.Bulletins.id))
        .filter(
            models.Bulletins.id_classe == bulletin.id_classe,
            models.Bulletins.id_trimestre == bulletin.id_trimestre,
        )
        .scalar()
    )

    fichier = pdf_service.nom_fichier_bulletin(bulletin)
    contenu = pdf_service.bulletin_pdf(bulletin, etab, effectif, annee_label)
    return Response(
        content=contenu,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fichier}"'},
    )


@router.get("/classe/{id_classe}/trimestre/{id_trimestre}/pdf")
def bulletins_pdf_classe(id_classe: int, id_trimestre: int, db: Session = Depends(get_db)):
    """PDF regroupant tous les bulletins de la classe/période (un par page)."""
    bulletins = (
        db.query(models.Bulletins)
        .options(
            joinedload(models.Bulletins.details).joinedload(models.BulletinDetails.cours),
            joinedload(models.Bulletins.eleve),
            joinedload(models.Bulletins.trimestre).joinedload(models.Trimestres.annee_scolaire),
            joinedload(models.Bulletins.classe),
        )
        .filter(
            models.Bulletins.id_classe == id_classe,
            models.Bulletins.id_trimestre == id_trimestre,
        )
        .order_by(models.Bulletins.rang.asc().nullslast(), models.Bulletins.id.asc())
        .all()
    )
    if not bulletins:
        raise HTTPException(status_code=404, detail="Aucun bulletin trouvé pour cette classe / période")

    etab = _contexte_etablissement(db)
    annee_label = bulletins[0].trimestre.annee_scolaire.libelle if bulletins[0].trimestre.annee_scolaire else None

    fichier = pdf_service.nom_fichier_classe(bulletins)
    contenu = pdf_service.bulletins_classe_pdf(bulletins, etab, annee_label)
    return Response(
        content=contenu,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fichier}"'},
    )


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
