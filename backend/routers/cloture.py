import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from database import get_db
import models
import schemas
from security import get_current_user, require_admin
from bareme import niveau_ordre, est_jardin, jardin_suivant
from timeutils import now_utc

logger = logging.getLogger("college_aureole")

router = APIRouter(prefix="/api/cloture", tags=["Clôture d'année"], dependencies=[Depends(get_current_user)])


def _passage_jardin_automatique(insc: models.Inscriptions) -> bool:
    """Règle maternelle : chaque année, les élèves du jardin d'enfants passent
    automatiquement à la section supérieure (petite → moyenne → grande → 1ère
    année), sans décision de conseil. Seule une exclusion explicite l'emporte."""
    return insc.classe is not None and est_jardin(insc.classe.niveau) and insc.statut_passage != "EXCLU"


def _construire_index_classes(db: Session) -> dict:
    """Charge TOUTES les classes une seule fois et retourne un index par id.

    Évite le pattern N+1 queries de l'ancienne implémentation qui appelait
    db.query(Classes).all() pour chaque élève dans la boucle de clôture.
    À appeler UNE FOIS avant la boucle, puis passer le dict aux helpers.
    """
    return {c.id: c for c in db.query(models.Classes).all()}


def _classe_suivante_depuis_index(classe_origine, index_classes: dict) -> models.Classes | None:
    """Classe du niveau suivant (même division si elle existe), sinon None.

    Utilise un index pre-chargé au lieu de requêter la base à chaque appel.

    Règle jardin : l'enfant passe à la section de jardin suivante
    (Petite → Moyenne → Grande → 1ère Année).
    """
    if classe_origine is None:
        return None
    toutes = list(index_classes.values())

    if est_jardin(classe_origine.niveau):
        niveau_suivant = jardin_suivant(classe_origine.niveau)
        if niveau_suivant is None:
            return None
        candidates = [c for c in toutes if c.niveau == niveau_suivant]
        return candidates[0] if candidates else None

    ordre = niveau_ordre(classe_origine.niveau)
    if ordre is None:
        return None
    candidates = [c for c in toutes if niveau_ordre(c.niveau) == ordre + 1]
    if not candidates:
        return None
    meme_division = [c for c in candidates if c.nom == classe_origine.nom]
    return (meme_division or candidates)[0]


def _action_prevue(insc: models.Inscriptions, classe_dest=None, auto_jardin=False) -> str:
    if auto_jardin:
        if classe_dest is not None:
            return f"Admis – passage en {classe_dest.niveau} {classe_dest.nom}"
        return "Admis – passage (classe suivante non créée)"
    sp = insc.statut_passage
    if sp == "ADMIS":
        if insc.diplome:
            return "Diplômé – sortie du système"
        if classe_dest is not None:
            return f"Admis – passage en {classe_dest.niveau} {classe_dest.nom}"
        return "Admis – passage en classe suivante (non créée — à créer avant la clôture)"
    if sp == "RECALE":
        return "Recalé – redoublement (même classe)"
    if sp == "EXCLU":
        return "Exclu – retrait du système"
    return "En attente – non encore décidé"


@router.get("/preview", response_model=schemas.CloturePreviewResponse)
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

    # FIX PERFORMANCE : charger toutes les classes une seule fois, pas dans la boucle
    index_classes = _construire_index_classes(db)

    compteurs = schemas.CompteursPreview()
    eleves_preview: list[schemas.ElevePreview] = []
    nb_classes_manquantes = 0

    for insc in inscriptions:
        eleve = insc.eleve
        classe = insc.classe
        sp = insc.statut_passage
        auto_jardin = _passage_jardin_automatique(insc)

        if sp == "EXCLU":
            compteurs.EXCLU += 1
        elif auto_jardin:
            compteurs.ADMIS_PASSAGE += 1
        elif sp == "ADMIS":
            if insc.diplome:
                compteurs.ADMIS_DIPLOME += 1
            else:
                compteurs.ADMIS_PASSAGE += 1
        elif sp == "RECALE":
            compteurs.RECALE_REDOUBLEMENT += 1
        else:
            compteurs.EN_ATTENTE += 1

        classe_dest = _classe_suivante_depuis_index(classe, index_classes)
        # FIX (élèves orphelins) : un élève admis sans classe de destination ne
        # sera pas réinscrit à la clôture — on le signale avant l'exécution.
        a_besoin_classe = (auto_jardin or sp == "ADMIS") and not insc.diplome
        classe_manquante = bool(a_besoin_classe and classe_dest is None)
        if classe_manquante:
            nb_classes_manquantes += 1

        eleves_preview.append(schemas.ElevePreview(
            matricule=eleve.matricule if eleve else insc.matricule_eleve,
            nom=eleve.nom if eleve else "",
            prenom=eleve.prenom if eleve else "",
            classe_id=classe.id if classe else None,
            classe_nom=classe.nom if classe else None,
            niveau=classe.niveau if classe else None,
            statut_passage="ADMIS" if auto_jardin else sp,
            diplome=insc.diplome,
            action_prevue=_action_prevue(insc, classe_dest, auto_jardin),
            inscription_id=insc.id,
            classe_manquante=classe_manquante,
        ))

    return schemas.CloturePreviewResponse(
        annee_active=schemas.AnneeInfo(id=annee.id, libelle=annee.libelle),
        total_eleves=len(inscriptions),
        blocants=compteurs.EN_ATTENTE,
        peut_executer=False if annee.cloturee else (compteurs.EN_ATTENTE == 0 and len(inscriptions) > 0),
        cloturee=annee.cloturee,
        compteurs=compteurs,
        eleves=eleves_preview,
        nb_classes_manquantes=nb_classes_manquantes,
    )


@router.post("/executer", response_model=schemas.ClotureExecuterResponse, status_code=status.HTTP_200_OK)
def executer_cloture(
    payload: schemas.ClotureExecuterPayload,
    db: Session = Depends(get_db),
    _admin: models.Utilisateurs = Depends(require_admin),
):
    try:
        annee_active = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.active == True).first()
        if not annee_active:
            raise HTTPException(status_code=404, detail="Aucune année scolaire active")
        if annee_active.cloturee:
            raise HTTPException(
                status_code=409,
                detail="L'année scolaire active est déjà clôturée : aucune nouvelle clôture possible.",
            )

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

        en_attente = [i for i in inscriptions if i.statut_passage == "EN_ATTENTE" and not _passage_jardin_automatique(i)]
        if en_attente:
            raise HTTPException(status_code=409, detail="Élèves en attente")

        doublon = db.query(models.AnneesScolaires).filter(
            models.AnneesScolaires.libelle == payload.nouvelle_annee.libelle
        ).first()
        if doublon:
            raise HTTPException(status_code=400, detail="Année scolaire déjà existante")

        from services import sauvegardes

        # FIX (archive uniquement à la clôture) : la sauvegarde automatique au
        # démarrage a été supprimée (main.py) — la clôture d'année est donc le
        # SEUL moment où une archive complète est exigée automatiquement. Elle
        # capture l'état AVANT le passage à la nouvelle année ; un échec
        # annule la clôture (on ne change jamais d'année sans archive).
        try:
            sauvegardes.sauvegarde_cloture(db)
        except Exception:
            db.rollback()
            logger.exception("Clôture annulée : échec de création de l'archive.")
            raise HTTPException(status_code=500, detail="Impossible de créer l'archive de clôture")

        nouvelle_annee = models.AnneesScolaires(
            libelle=payload.nouvelle_annee.libelle,
            date_debut=payload.nouvelle_annee.date_debut,
            date_fin=payload.nouvelle_annee.date_fin,
            active=True,
            cloturee=False,
        )
        db.add(nouvelle_annee)
        db.flush()  # indispensable : nouvelle_annee.id utilisé juste après

        from routers.inscriptions import _generer_echeances, _reporter_impayes, _synchroniser_classe_eleve

        rapport = schemas.RapportCloture()

        # FIX PERFORMANCE : charger toutes les classes une seule fois pour éviter N+1
        index_classes = _construire_index_classes(db)

        def _eleve_cloture(insc: models.Inscriptions) -> schemas.EleveCloture:
            eleve = insc.eleve
            classe = insc.classe
            return schemas.EleveCloture(
                matricule=eleve.matricule if eleve else insc.matricule_eleve,
                nom=eleve.nom if eleve else "",
                prenom=eleve.prenom if eleve else "",
                classe_nom=classe.nom if classe else None,
                niveau=classe.niveau if classe else None,
            )

        def _alerter(insc: models.Inscriptions, motif: str) -> None:
            """Persiste un rappel actif de rattrapage (élève non réinscrit)."""
            eleve = insc.eleve
            db.add(models.ClotureAlertes(
                id_annee_scolaire=nouvelle_annee.id,
                matricule=insc.matricule_eleve,
                nom=eleve.nom if eleve else "",
                prenom=eleve.prenom if eleve else "",
                motif=motif,
            ))

        for insc in inscriptions:
            sp = insc.statut_passage
            eleve = insc.eleve
            auto_jardin = _passage_jardin_automatique(insc)

            if sp == "EXCLU" and not auto_jardin:
                if eleve:
                    eleve.statut = "exclu"
                    eleve.classe_id = None
                rapport.exclus += 1
                rapport.eleves_exclus.append(_eleve_cloture(insc))
                continue

            if auto_jardin:
                statut_insc = "Inscrit"
                classe_dest = _classe_suivante_depuis_index(insc.classe, index_classes)

            elif sp == "ADMIS":
                if insc.diplome:
                    rapport.admis_diplome += 1
                    rapport.eleves_diplomes.append(_eleve_cloture(insc))
                    continue
                statut_insc = "Inscrit"
                classe_dest = _classe_suivante_depuis_index(insc.classe, index_classes)

            elif sp == "RECALE":
                statut_insc = "Redoublant"
                classe_dest = insc.classe  # redoublement : même classe

            else:
                continue

            # FIX BUG CRITIQUE (perte silencieuse) : si la classe du niveau
            # suivant n'existe pas encore, on NE réinscrit PLUS l'élève dans
            # son ancienne classe en silence (mauvais tarif, élève qui semble
            # ne pas avoir progressé). On remonte une erreur explicite à
            # traiter manuellement par l'admin après la clôture.
            if classe_dest is None:
                motif = (
                    "Classe suivante introuvable : aucune classe créée pour le niveau suivant. "
                    "Créez la classe puis inscrivez cet élève manuellement."
                )
                rapport.erreurs.append(schemas.EleveErreurCloture(
                    matricule=insc.matricule_eleve,
                    nom=eleve.nom if eleve else "",
                    prenom=eleve.prenom if eleve else "",
                    motif=motif,
                ))
                _alerter(insc, motif)
                continue

            id_classe_dest = classe_dest.id

            # FIX BUG CRITIQUE : nb_redoublements ne doit PAS être remis à 0
            # pour les élèves admis. Un élève qui a redoublé par le passé et
            # est finalement admis conserve son historique de redoublements.
            # AVANT (bug) : nb_redoublements=... else 0
            # APRÈS (fix) : ... else (insc.nb_redoublements or 0)
            nouvelle_inscription = models.Inscriptions(
                matricule_eleve=insc.matricule_eleve,
                id_classe=id_classe_dest,
                id_annee_scolaire=nouvelle_annee.id,
                statut=statut_insc,
                statut_passage="EN_ATTENTE",  # FIX : initialisation explicite pour la nouvelle année
                nb_redoublements=(insc.nb_redoublements or 0) + 1 if statut_insc == "Redoublant" else (insc.nb_redoublements or 0),
                date_inscription=nouvelle_annee.date_debut,
            )
            db.add(nouvelle_inscription)
            try:
                # Savepoint : si le flush échoue (ex. doublon), on annule uniquement
                # cette insertion sans invalider toute la transaction en cours.
                with db.begin_nested():
                    db.flush()
            except IntegrityError:
                logger.warning("Inscription déjà existante pour %s en année %s", insc.matricule_eleve, nouvelle_annee.libelle)
                # FIX BUG CRITIQUE (perte silencieuse) : l'élève n'a PAS été
                # traité, ce doit être visible dans le rapport, pas seulement
                # dans les logs serveur.
                motif = (
                    "Une inscription existe déjà pour cet élève sur la nouvelle année (doublon) : "
                    "vérifiez son dossier manuellement."
                )
                rapport.erreurs.append(schemas.EleveErreurCloture(
                    matricule=insc.matricule_eleve,
                    nom=eleve.nom if eleve else "",
                    prenom=eleve.prenom if eleve else "",
                    motif=motif,
                ))
                _alerter(insc, motif)
                continue

            _generer_echeances(db, nouvelle_inscription)
            db.flush()
            _reporter_impayes(db, insc.matricule_eleve, annee_active.id, nouvelle_inscription)
            _synchroniser_classe_eleve(db, insc.matricule_eleve, statut_insc, id_classe_dest)

            rapport.total_traites += 1
            # FIX : les compteurs ne sont incrémentés qu'APRÈS le succès réel
            # de la création (avant, un élève comptait comme "admis" même si
            # aucune inscription n'avait été créée pour lui).
            if statut_insc == "Redoublant":
                rapport.recale_redoublement += 1
                rapport.eleves_redoublants.append(_eleve_cloture(insc))
            else:
                rapport.admis_passage += 1
                rapport.eleves_admis_passage.append(_eleve_cloture(insc))

        annee_active.active = False
        annee_active.cloturee = True
        db.query(models.Trimestres).filter(
            models.Trimestres.annee_scolaire_id == annee_active.id
        ).update({models.Trimestres.verrouille: True})

        from periodes import generer_periodes_par_defaut
        generer_periodes_par_defaut(db, nouvelle_annee.id, nouvelle_annee.date_debut, nouvelle_annee.date_fin)

        # FIX (rappel actif) : les erreurs de rattrapage sont persistées
        # (cloture_alertes) et comptées explicitement dans le rapport.
        rapport.nb_erreurs = len(rapport.erreurs)

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


# ── Rappel actif : élèves à réinscrire après une clôture ─────────────────────

@router.get("/alertes", response_model=schemas.ClotureAlertesReponse)
def lister_alertes_cloture(
    db: Session = Depends(get_db),
    _admin: models.Utilisateurs = Depends(require_admin),
):
    """Alertes de rattrapage en attente : élèves non réinscrits lors d'une
    clôture (classe suivante absente, doublon). Elles ne disparaissent que
    lorsqu'un traitement manuel les a résolues explicitement."""
    alertes = (
        db.query(models.ClotureAlertes)
        .options(joinedload(models.ClotureAlertes.annee_scolaire))
        .filter(models.ClotureAlertes.resolue.is_(False))
        .order_by(models.ClotureAlertes.cree_le.desc(), models.ClotureAlertes.id.desc())
        .all()
    )
    lectures = []
    for a in alertes:
        base = schemas.ClotureAlerteRead.model_validate(a)
        lectures.append(base)
    return schemas.ClotureAlertesReponse(nb_en_attente=len(lectures), alertes=lectures)


@router.post("/alertes/{alerte_id}/resoudre", response_model=schemas.ClotureAlerteRead)
def resoudre_alerte_cloture(
    alerte_id: int,
    db: Session = Depends(get_db),
    _admin: models.Utilisateurs = Depends(require_admin),
):
    """Marque une alerte comme traitée : l'élève a été réinscrit manuellement
    (ou sa situation réglée) par l'admin."""
    alerte = db.query(models.ClotureAlertes).filter(models.ClotureAlertes.id == alerte_id).first()
    if not alerte:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    alerte.resolue = True
    alerte.resolue_le = now_utc()
    db.commit()
    db.refresh(alerte)
    return schemas.ClotureAlerteRead.model_validate(alerte)
