import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from database import get_db
import models
import schemas
from security import get_current_user, require_role
from bareme import niveau_ordre

logger = logging.getLogger("college_aureole")

router = APIRouter(prefix="/api/cloture", tags=["Clôture d'année"], dependencies=[Depends(get_current_user)])


def _classe_suivante(db: Session, classe_origine) -> models.Classes | None:
    """Classe du niveau suivant (même division si elle existe), sinon None."""
    if classe_origine is None:
        return None
    ordre = niveau_ordre(classe_origine.niveau)
    if ordre is None:
        return None
    candidates = [c for c in db.query(models.Classes).all() if niveau_ordre(c.niveau) == ordre + 1]
    if not candidates:
        return None
    meme_division = [c for c in candidates if c.nom == classe_origine.nom]
    return (meme_division or candidates)[0]


def _action_prevue(insc: models.Inscriptions, classe_dest=None) -> str:
    sp = insc.statut_passage
    if sp == "ADMIS":
        if insc.diplome:
            return "Diplômé – sortie du système"
        if classe_dest is not None:
            return f"Admis – passage en {classe_dest.niveau} {classe_dest.nom}"
        return "Admis – passage en classe suivante"
    if sp == "RECALE":
        return "Recalé – redoublement (même classe)"
    if sp == "EXCLU":
        return "Exclu – retrait du système"
    return "En attente – non encore décidé"


@router.get("/preview", response_model=schemas.CloturePreviewResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def preview_cloture(db: Session = Depends(get_db)):
    annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()
    if not annee:
        raise HTTPException(status_code=404, detail="Aucune année scolaire active")

    inscriptions = (
        db.query(models.Inscriptions)
        .options(
            joinedload(models.Inscriptions.eleve),
            joinedload(models.Inscriptions.classe),
        )
        .filter(models.Inscriptions.id_annee_scolaire == annee.id)
        .all()
    )

    compteurs = schemas.CompteursPreview()
    eleves_preview: list[schemas.ElevePreview] = []

    for insc in inscriptions:
        eleve = insc.eleve
        classe = insc.classe
        sp = insc.statut_passage

        if sp == "ADMIS":
            if insc.diplome:
                compteurs.ADMIS_DIPLOME += 1
            else:
                compteurs.ADMIS_PASSAGE += 1
        elif sp == "RECALE":
            compteurs.RECALE_REDOUBLEMENT += 1
        elif sp == "EXCLU":
            compteurs.EXCLU += 1
        else:
            compteurs.EN_ATTENTE += 1

        eleves_preview.append(schemas.ElevePreview(
            matricule=eleve.matricule if eleve else insc.matricule_eleve,
            nom=eleve.nom if eleve else "",
            prenom=eleve.prenom if eleve else "",
            classe_id=classe.id if classe else None,
            classe_nom=classe.nom if classe else None,
            niveau=classe.niveau if classe else None,
            statut_passage=sp,
            diplome=insc.diplome,
            action_prevue=_action_prevue(insc, _classe_suivante(db, classe)),
            inscription_id=insc.id,
        ))

    return schemas.CloturePreviewResponse(
        annee_active=schemas.AnneeInfo(id=annee.id, libelle=annee.libelle),
        total_eleves=len(inscriptions),
        blocants=compteurs.EN_ATTENTE,
        peut_executer=compteurs.EN_ATTENTE == 0 and len(inscriptions) > 0,
        compteurs=compteurs,
        eleves=eleves_preview,
    )


@router.post("/executer", response_model=schemas.ClotureExecuterResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(require_role("admin", "directeur"))])
def executer_cloture(payload: schemas.ClotureExecuterPayload, db: Session = Depends(get_db)):
    try:
        annee_active = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()
        if not annee_active:
            raise HTTPException(status_code=404, detail="Aucune année scolaire active")

        inscriptions = (
            db.query(models.Inscriptions)
            .options(
                joinedload(models.Inscriptions.eleve),
                joinedload(models.Inscriptions.classe),
            )
            .filter(models.Inscriptions.id_annee_scolaire == annee_active.id)
            .all()
        )

        if not inscriptions:
            raise HTTPException(status_code=400, detail="Aucune inscription")

        en_attente = [i for i in inscriptions if i.statut_passage == "EN_ATTENTE"]
        if en_attente:
            raise HTTPException(status_code=409, detail="Élèves en attente")

        doublon = db.query(models.AnneesScolaires).filter(
            models.AnneesScolaires.libelle == payload.nouvelle_annee.libelle
        ).first()
        if doublon:
            raise HTTPException(status_code=400, detail="Année scolaire déjà existante")

        nouvelle_annee = models.AnneesScolaires(
            libelle=payload.nouvelle_annee.libelle,
            date_debut=payload.nouvelle_annee.date_debut,
            date_fin=payload.nouvelle_annee.date_fin,
            active=True,
            cloturee=False,
        )
        db.add(nouvelle_annee)
        db.flush()  # indispensable : nouvelle_annee.id est utilisé juste après (sinon None -> violation NOT NULL sur inscriptions.id_annee_scolaire)

        from routers.inscriptions import _generer_echeances, _reporter_impayes, _synchroniser_classe_eleve

        rapport = schemas.RapportCloture()

        for insc in inscriptions:
            sp = insc.statut_passage
            eleve = insc.eleve

            if sp == "ADMIS":
                if insc.diplome:
                    rapport.admis_diplome += 1
                    continue

                statut_insc = "Inscrit"
                classe_dest = _classe_suivante(db, insc.classe)
                id_classe_dest = classe_dest.id if classe_dest is not None else insc.id_classe
                rapport.admis_passage += 1

            elif sp == "RECALE":
                statut_insc = "Redoublant"
                id_classe_dest = insc.id_classe
                rapport.recale_redoublement += 1

            elif sp == "EXCLU":
                if eleve:
                    eleve.statut = "exclu"
                    eleve.classe_id = None
                rapport.exclus += 1
                continue

            else:
                continue

            nouvelle_inscription = models.Inscriptions(
                matricule_eleve=insc.matricule_eleve,
                id_classe=id_classe_dest,
                id_annee_scolaire=nouvelle_annee.id,
                statut=statut_insc,
                date_inscription=nouvelle_annee.date_debut,
            )
            db.add(nouvelle_inscription)
            try:
                # Savepoint : si le flush échoue (ex. doublon), on annule uniquement
                # cette insertion sans invalider toute la transaction en cours
                # (sur PostgreSQL, un flush en échec laisse sinon la transaction
                # "aborted" et fait échouer tous les tours de boucle suivants).
                with db.begin_nested():
                    db.flush()
            except IntegrityError:
                logger.warning("Inscription déjà existante pour %s en année %s", insc.matricule_eleve, nouvelle_annee.libelle)
                continue

            _generer_echeances(db, nouvelle_inscription)
            db.flush()
            _reporter_impayes(db, insc.matricule_eleve, annee_active.id, nouvelle_inscription)
            _synchroniser_classe_eleve(db, insc.matricule_eleve, statut_insc, id_classe_dest)

            rapport.total_traites += 1

        annee_active.active = False
        annee_active.cloturee = True
        db.query(models.Trimestres).filter(
            models.Trimestres.annee_scolaire_id == annee_active.id
        ).update({models.Trimestres.verrouille: True})

        from periodes import generer_periodes_par_defaut
        generer_periodes_par_defaut(db, nouvelle_annee.id, nouvelle_annee.date_debut, nouvelle_annee.date_fin)

        db.flush()
        db.commit()

        return schemas.ClotureExecuterResponse(
            succes=True,
            ancienne_annee=schemas.AnneeInfo(id=annee_active.id, libelle=annee_active.libelle),
            nouvelle_annee=schemas.AnneeInfo(id=nouvelle_annee.id, libelle=nouvelle_annee.libelle),
            rapport=rapport,
        )

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        logger.exception("Erreur lors de l'exécution de la clôture d'année.")
        raise HTTPException(status_code=500, detail="Erreur interne")
