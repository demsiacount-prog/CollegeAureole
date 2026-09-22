from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from timeutils import now_utc
from database import get_db
import models
import schemas
from security import get_current_user
from bareme import appreciation_for_moyenne, bareme_niveau, est_jardin, utilise_coefficient
from services import pdf as pdf_service
from helpers import get_annee_ou_active
from schemas.bulletins import BulletinGenerationClasseResponse

router = APIRouter(prefix="/api/bulletins", tags=["Bulletins"], dependencies=[Depends(get_current_user)])


def _classe_bulletin_trimestre(db: Session, eleve: models.Eleves, trimestre: models.Trimestres | None):
    """Classe de référence d'un bulletin : celle de l'inscription de l'élève
    pour l'année scolaire du trimestre.

    On ne lit JAMAIS Eleves.classe_id comme source unique : cette colonne reflète
    la classe ACTUELLE de l'élève, pas celle qu'il avait l'année du bulletin
    (régressions lors de la relecture d'anciens bulletins après un changement de
    classe). L'inscription de l'année est la source fiable ; la classe courante
    ne sert de repli que lorsque aucune inscription n'existe (données anciennes).
    """
    id_classe = eleve.classe_id
    if trimestre is not None:
        inscription = (
            db.query(models.Inscriptions)
            .filter(
                models.Inscriptions.matricule_eleve == eleve.matricule,
                models.Inscriptions.id_annee_scolaire == trimestre.annee_scolaire_id,
            )
            .first()
        )
        if inscription is not None and inscription.id_classe is not None:
            id_classe = inscription.id_classe
    if id_classe is None:
        return None, None
    classe = db.query(models.Classes).filter(models.Classes.id == id_classe).first()
    return id_classe, classe


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

    # Classe de l'élève pour l'année du trimestre (inscription), jamais la classe
    # actuelle : un élève qui a changé de classe depuis conserve son ancien
    # bulletin avec les coefficients et le barème de l'époque.
    id_classe, classe = _classe_bulletin_trimestre(db, eleve, trimestre)
    if id_classe is None or classe is None:
        raise HTTPException(
            status_code=400,
            detail="Classe introuvable",
        )

    if est_jardin(classe.niveau):
        raise HTTPException(
            status_code=400,
            detail="Le jardin d'enfants n'utilise pas de notes : appréciation manuelle de l'enseignant.",
        )

    # Cours attendus pour cette classe (avec leur coefficient)
    affectations_classe = (
        db.query(models.AffectationCoursClasse)
        .filter(models.AffectationCoursClasse.id_classe == id_classe)
        .all()
    )
    coefficients_par_cours = {a.id_cours: a.coefficient for a in affectations_classe}

    # Moyenne matière de la période = 60% note de composition + 40% note de
    # classe (facultative : si absente, la note de composition fait foi).
    # Le repli s'applique ligne par ligne via coalesce avant la moyenne.
    moyennes_par_cours = (
        db.query(
            models.Notes.id_cours,
            func.avg(models.Notes.note).label("moyenne_comp"),
            func.avg(func.coalesce(models.Notes.note_classe, models.Notes.note)).label("moyenne_classe"),
        )
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
    cours_notes = {id_cours for id_cours, _, _ in moyennes_par_cours}
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

    bareme = bareme_niveau(classe.niveau) if classe else 20

    details = []
    total_pondere = 0.0
    total_coefficients = 0.0
    total_simple = 0.0
    nb_matieres = 0

    # Conditions de pondération par le coefficient (même règle partagée que le
    # PDF et le frontend, voir bareme.utilise_coefficient) :
    # - EF1 (1ère-5ème, barème /10) : moyenne SIMPLE, aucun coefficient.
    # - 6ème (classe spéciale) : les TRIMESTRES sont coefficientés (moyenne
    #   pondérée, toujours sur /10), les COMPOSITIONS restent en moyenne simple.
    # - EF2/lycée (barème /20) : moyenne pondérée par le coefficient.
    utilise_coeff = utilise_coefficient(classe.niveau if classe else None, trimestre.type)

    for id_cours, moyenne_comp, moyenne_classe_eff in moyennes_par_cours:
        coefficient = coefficients_par_cours.get(id_cours)
        if coefficient is None:
            # Cours noté mais non affecté à la classe actuelle (ex: changement de classe en cours d'année) : ignoré
            continue
        if not utilise_coeff:
            coefficient = 1.0
        moyenne = round(0.6 * float(moyenne_comp) + 0.4 * float(moyenne_classe_eff), 2)
        details.append({
            "id_cours": id_cours,
            "moyenne": moyenne,
            "coefficient": coefficient,
        })
        total_pondere += moyenne * coefficient
        total_coefficients += coefficient
        total_simple += moyenne
        nb_matieres += 1

    if utilise_coeff:
        # Aucune matière coefficientée (ex. tous les coefficients à 0) : la
        # moyenne n'a pas de sens → None plutôt qu'un 0.0 fallacieux inscrit au
        # bulletin officiel. La colonne est désormais nullable : `None` est
        # enregistré tel quel, sans valeur arbitraire.
        moyenne_generale = round(total_pondere / total_coefficients, 2) if total_coefficients else None
    else:
        moyenne_generale = round(total_simple / nb_matieres, 2) if nb_matieres else None

    return {
        "matricule_eleve": matricule_eleve,
        "id_trimestre": id_trimestre,
        "id_classe": id_classe,
        "moyenne_generale": moyenne_generale,
        "appreciation": (
            appreciation_for_moyenne(moyenne_generale, bareme)
            if moyenne_generale is not None
            else None
        ),
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
    """Calcule le rang des bulletins PUBLIÉS de la classe/trimestre.

    Les brouillons n'ont PAS de rang : le classement affiché est celui de la
    version officielle diffusée aux familles. Un brouillon régénéré après une
    publication n'écrase pas les rangs publiés (ni dans l'affichage PDF, ni
    dans le bulletin annuel).
    """
    db.query(models.Bulletins).filter(
        models.Bulletins.id_classe == id_classe,
        models.Bulletins.id_trimestre == id_trimestre,
        models.Bulletins.statut != "PUBLIE",
    ).update({models.Bulletins.rang: None})
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


@router.post("/generer", response_model=schemas.BulletinResponse, status_code=status.HTTP_201_CREATED)
def generer_bulletin(payload: schemas.BulletinGenerateRequest, db: Session = Depends(get_db)):
    # FIX SÉCURITÉ : bloquer la génération de bulletin sur une année clôturée
    trimestre = db.query(models.Trimestres).options(
        joinedload(models.Trimestres.annee_scolaire)
    ).filter(models.Trimestres.id == payload.id_trimestre).first()
    if trimestre and trimestre.annee_scolaire and trimestre.annee_scolaire.cloturee:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Année scolaire clôturée : la génération de bulletin est bloquée.",
        )
    calcul = _calculer_bulletin(db, payload.matricule_eleve, payload.id_trimestre)
    bulletin = _upsert_bulletin(db, calcul)
    _calculer_rangs_classe(db, calcul["id_classe"], calcul["id_trimestre"])
    db.commit()
    db.refresh(bulletin)
    return bulletin


@router.post("/generer-classe", response_model=BulletinGenerationClasseResponse, status_code=status.HTTP_201_CREATED)
def generer_bulletins_classe(payload: schemas.BulletinGenerateClasseRequest, db: Session = Depends(get_db)):
    classe = db.query(models.Classes).filter(models.Classes.id == payload.id_classe).first()
    if not classe:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    trimestre = db.query(models.Trimestres).options(
        joinedload(models.Trimestres.annee_scolaire)
    ).filter(models.Trimestres.id == payload.id_trimestre).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable")
    # FIX SÉCURITÉ : bloquer la génération sur une année clôturée
    if trimestre.annee_scolaire and trimestre.annee_scolaire.cloturee:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Année scolaire clôturée : la génération de bulletins est bloquée.",
        )
    if est_jardin(classe.niveau):
        raise HTTPException(
            status_code=400,
            detail="Le jardin d'enfants n'utilise pas de bulletins chiffrés : appréciation manuelle de l'enseignant.",
        )

    # Effectif de la classe POUR l'année du trimestre = union de deux sources,
    # pour ne JAMAIS perdre d'étudiant :
    # - les inscriptions de cette (classe, année) : source fiable et historique ;
    # - les élèves actuellement affectés à la classe (Eleves.classe_id), en
    #   complément pour ceux sans inscription de l'année (inscriptions
    #   incomplètes ou non re-saisies chaque année).
    # La classe via Eleves.classe_id seul reste interdite pour reconstruire
    # l'année (fausse pour les années antérieures après un changement de classe).
    inscrits_annee = {
        row[0]
        for row in db.query(models.Inscriptions.matricule_eleve)
        .filter(
            models.Inscriptions.id_classe == payload.id_classe,
            models.Inscriptions.id_annee_scolaire == trimestre.annee_scolaire_id,
        )
        .all()
    }
    effectifs_classe = {
        e.matricule
        for e in db.query(models.Eleves).filter(models.Eleves.classe_id == payload.id_classe).all()
    }
    matricules = sorted(inscrits_annee | effectifs_classe)

    bulletins_generes, erreurs = [], []
    for matricule in matricules:
        try:
            calcul = _calculer_bulletin(db, matricule, payload.id_trimestre)
            bulletins_generes.append(_upsert_bulletin(db, calcul))
        except HTTPException as exc:
            erreurs.append({"matricule_eleve": matricule, "motif": str(exc.detail)})

    _calculer_rangs_classe(db, payload.id_classe, payload.id_trimestre)
    db.commit()
    for bulletin in bulletins_generes:
        db.refresh(bulletin)

    if erreurs and not bulletins_generes:
        motifs = "; ".join(e["motif"] for e in erreurs)
        raise HTTPException(status_code=400, detail=f"Aucun bulletin généré ({len(erreurs)} élève(s)) : {motifs}")

    return BulletinGenerationClasseResponse(
        bulletins=bulletins_generes,
        erreurs=erreurs,
        nb_succes=len(bulletins_generes),
        nb_erreurs=len(erreurs),
    )


def _verifier_trimestre_pas_cloture(payload: schemas.BulletinPublierRequest, db: Session):
    """Publier/dépublier modifie des bulletins officiels : refus sur année clôturée."""
    trimestre = db.query(models.Trimestres).options(
        joinedload(models.Trimestres.annee_scolaire)
    ).filter(models.Trimestres.id == payload.id_trimestre).first()
    if not trimestre:
        raise HTTPException(status_code=404, detail="Trimestre introuvable")
    if trimestre.annee_scolaire and trimestre.annee_scolaire.cloturee:
        raise HTTPException(
            status_code=409,
            detail="Année scolaire clôturée : le statut des bulletins ne peut plus être modifié.",
        )


@router.post("/publier", response_model=List[schemas.BulletinResponse])
def publier_bulletins_classe(payload: schemas.BulletinPublierRequest, db: Session = Depends(get_db)):
    """Verrouille les bulletins d'une classe/trimestre : ils deviennent visibles
    et ne peuvent plus être régénérés sans dépublication explicite."""
    _verifier_trimestre_pas_cloture(payload, db)
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


@router.post("/depublier", response_model=List[schemas.BulletinResponse])
def depublier_bulletins_classe(payload: schemas.BulletinPublierRequest, db: Session = Depends(get_db)):
    _verifier_trimestre_pas_cloture(payload, db)
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


@router.get("/", response_model=List[schemas.BulletinResponse])
def get_all_bulletins(
    matricule_eleve: Optional[str] = None,
    id_classe: Optional[int] = None,
    id_trimestre: Optional[int] = None,
    annee_id: Optional[int] = Query(None, description="Filtrer par année scolaire (défaut : active)"),
    id_annee_scolaire: Optional[int] = Query(None, description="Alias de `annee_id` (consultation d'une année passée)"),
    skip: int = 0,
    limit: int = Query(default=200, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(models.Bulletins).options(
        joinedload(models.Bulletins.eleve),
        joinedload(models.Bulletins.details).joinedload(models.BulletinDetails.cours)
    )

    if annee_id is None:
        annee_id = id_annee_scolaire
    if annee_id is not None:
        query = query.join(
            models.Trimestres,
            models.Bulletins.id_trimestre == models.Trimestres.id
        ).filter(
            models.Trimestres.annee_scolaire_id == annee_id
        )

    if matricule_eleve:
        query = query.filter(models.Bulletins.matricule_eleve == matricule_eleve)
    if id_classe:
        query = query.filter(models.Bulletins.id_classe == id_classe)
    if id_trimestre:
        query = query.filter(models.Bulletins.id_trimestre == id_trimestre)

    return query.order_by(models.Bulletins.rang.asc().nullslast()).offset(skip).limit(limit).all()


@router.get("/annuel/{matricule_eleve}", response_model=schemas.BulletinAnnuelResponse)
def get_bulletin_annuel(matricule_eleve: str, annee_id: int, db: Session = Depends(get_db)):
    from services.bulletins_annuels import bulletin_annuel

    try:
        return bulletin_annuel(db, matricule_eleve, annee_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


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


@router.delete("/{bulletin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bulletin(bulletin_id: int, db: Session = Depends(get_db)):
    bulletin = db.query(models.Bulletins).filter(models.Bulletins.id == bulletin_id).first()
    if not bulletin:
        raise HTTPException(status_code=404, detail="Bulletin introuvable")
    # FIX BUG CRITIQUE : la régénération d'un bulletin publié est bloquée
    # (_upsert_bulletin) mais sa suppression pure ne l'était pas — on pouvait
    # effacer un bulletin officiel déjà diffusé aux familles. On exige une
    # dépublication explicite au préalable (POST /api/bulletins/depublier).
    if bulletin.statut == "PUBLIE":
        raise HTTPException(
            status_code=409,
            detail="Ce bulletin est publié : dépubliez-le d'abord avant de le supprimer.",
        )
    db.delete(bulletin)
    db.commit()
    return None
