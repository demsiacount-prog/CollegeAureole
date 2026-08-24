from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models
import schemas
from security import get_current_user, require_role
from bareme import bareme_niveau

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(get_current_user)])

MOIS_ABBR = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]


def _derniers_mois(n: int = 6):
    """Retourne les n derniers mois sous forme [(annee, mois, label), ...]"""
    aujourdhui = date.today()
    mois = []
    annee, m = aujourdhui.year, aujourdhui.month
    for _ in range(n):
        mois.append((annee, m, MOIS_ABBR[m - 1]))
        m -= 1
        if m == 0:
            m = 12
            annee -= 1
    return list(reversed(mois))


def est_modifie(created_at, updated_at) -> bool:
    """Vrai si la ligne a réellement été modifiée après sa création.

    created_at/updated_at ont des defaults séparés (écart d'~1 µs à
    l'insertion), on ignore donc les écarts inférieurs à 1 seconde.
    """
    try:
        delta = updated_at - created_at
        return delta.total_seconds() > 1.0
    except (TypeError, AttributeError):
        return False



def _stats_direction(db: Session, include_finance: bool = True) -> dict:

    # ── 1. COMPTEURS SIMPLES (COUNT côté SQL, pas de chargement de lignes) ──
    nb_eleves = db.query(func.count(models.Eleves.matricule)).scalar() or 0
    nb_enseignants = db.query(func.count(models.Enseignants.matricule)).scalar() or 0
    nb_classes = db.query(func.count(models.Classes.id)).scalar() or 0

    # ── 2. MOYENNE PAR CLASSE (GROUP BY + AVG en SQL) ──────────────────────
    moyennes_brutes = (
        db.query(models.Classes.niveau, models.Classes.nom, func.avg(models.Notes.note))
        .outerjoin(models.Notes, models.Notes.id_classe == models.Classes.id)
        .group_by(models.Classes.id, models.Classes.niveau, models.Classes.nom)
        .order_by(models.Classes.niveau, models.Classes.nom)
        .all()
    )
    moyennes_par_classe = [
        {"classe": f"{niveau} {nom}", "moy": round(float(moy), 1) if moy is not None else 0, "bareme": bareme_niveau(niveau)}
        for niveau, nom, moy in moyennes_brutes
    ]

    # ── 3. RÉPARTITION PAR NIVEAU (GROUP BY + COUNT en SQL) ────────────────
    repartition_brute = (
        db.query(models.Classes.niveau, func.count(models.Eleves.matricule))
        .join(models.Eleves, models.Eleves.classe_id == models.Classes.id)
        .group_by(models.Classes.niveau)
        .all()
    )
    repartition_niveaux = [
        {"name": niveau if str(niveau).startswith("Niveau") else f"Niveau {niveau}", "value": count}
        for niveau, count in repartition_brute
    ]

    # ── 4. ABSENCES SUR LES 6 DERNIERS MOIS ────────────────────────────────
    mois_range = _derniers_mois(6)
    annee_min, mois_min, _ = mois_range[0]
    date_min = date(annee_min, mois_min, 1)

    # On ne récupère que la colonne date_absence sur la fenêtre utile
    # (au lieu de toutes les colonnes / toute la table comme avant)
    dates_absences = (
        db.query(models.Absences.date_absence)
        .filter(models.Absences.date_absence >= date_min)
        .all()
    )

    compteur_par_mois = {(a, m): 0 for a, m, _ in mois_range}
    for (d,) in dates_absences:
        key = (d.year, d.month)
        if key in compteur_par_mois:
            compteur_par_mois[key] += 1

    absences_par_mois = [
        {"mois": label, "absences": compteur_par_mois[(a, m)]}
        for a, m, label in mois_range
    ]

    # ── 5. TAUX D'ABSENCE DU MOIS EN COURS ─────────────────────────────────
    aujourdhui = date.today()
    absences_mois_actuel = compteur_par_mois.get((aujourdhui.year, aujourdhui.month), 0)
    taux_absence = (
        round((absences_mois_actuel / nb_eleves) * 100, 1) if nb_eleves > 0 else 0
    )

    # ── 6. ACTIVITÉ RÉCENTE (créations de toutes natures, triées en SQL) ────
    # Chaque table de création apporte ses événements les plus récents ; on
    # fusionne le tout, on trie par date décroissante puis on limite.
    LIMIT_PAR_TYPE = 5
    TOTAL_ACTIVITES = 30

    dernieres_notes = (
        db.query(models.Notes, models.Eleves, models.Classes)
        .join(models.Eleves, models.Eleves.matricule == models.Notes.matricule_eleve)
        .outerjoin(models.Classes, models.Classes.id == models.Notes.id_classe)
        .order_by(models.Notes.updated_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    dernieres_absences = (
        db.query(models.Absences, models.Eleves)
        .join(models.Eleves, models.Eleves.matricule == models.Absences.matricule_eleve)
        .order_by(models.Absences.updated_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_eleves = (
        db.query(models.Eleves)
        .order_by(models.Eleves.updated_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_enseignants = (
        db.query(models.Enseignants)
        .order_by(models.Enseignants.updated_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_tuteurs = (
        db.query(models.Tuteurs)
        .order_by(models.Tuteurs.updated_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    dernieres_inscriptions = (
        db.query(models.Inscriptions, models.Eleves)
        .join(models.Eleves, models.Eleves.matricule == models.Inscriptions.matricule_eleve)
        .order_by(models.Inscriptions.updated_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_paiements = (
        db.query(models.Paiements, models.Inscriptions, models.Eleves)
        .outerjoin(models.Inscriptions, models.Inscriptions.id == models.Paiements.id_inscription)
        .outerjoin(models.Eleves, models.Eleves.matricule == models.Inscriptions.matricule_eleve)
        .order_by(models.Paiements.updated_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    dernieres_depenses = (
        db.query(models.Depenses)
        .order_by(models.Depenses.updated_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_documents = (
        db.query(models.Documents, models.Eleves)
        .outerjoin(models.Eleves, models.Eleves.matricule == models.Documents.matricule_eleve)
        .order_by(models.Documents.uploaded_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )

    activites = []
    for note, eleve, classe in dernieres_notes:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip()
        nom_classe = classe.nom if classe else "sa classe"
        bm = bareme_niveau(classe.niveau) if classe else 20
        if est_modifie(note.created_at, note.updated_at):
            texte = f"Note de {note.note}/{bm} modifiée pour {nom_eleve} ({nom_classe})."
        else:
            texte = f"Note de {note.note}/{bm} ajoutée pour {nom_eleve} ({nom_classe})."
        activites.append({
            "type": "note",
            "texte": texte,
            "date": str(note.updated_at),
        })
    for absence, eleve in dernieres_absences:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip()
        statut = "justifiée" if absence.justifiee else "non justifiée"
        if est_modifie(absence.created_at, absence.updated_at):
            texte = f"Absence {statut} modifiée pour {nom_eleve}."
        else:
            texte = f"Absence {statut} enregistrée pour {nom_eleve}."
        activites.append({
            "type": "absence",
            "texte": texte,
            "date": str(absence.updated_at),
        })
    for eleve in derniers_eleves:
        if est_modifie(eleve.created_at, eleve.updated_at):
            texte = f"Élève {eleve.prenom} {eleve.nom} mis à jour."
        else:
            texte = f"Nouvel élève {eleve.prenom} {eleve.nom} enregistré."
        activites.append({
            "type": "eleve",
            "texte": texte,
            "date": str(eleve.updated_at),
        })
    for enseignant in derniers_enseignants:
        if est_modifie(enseignant.created_at, enseignant.updated_at):
            texte = f"Enseignant {enseignant.prenom} {enseignant.nom} mis à jour."
        else:
            texte = f"Enseignant {enseignant.prenom} {enseignant.nom} ajouté."
        activites.append({
            "type": "enseignant",
            "texte": texte,
            "date": str(enseignant.updated_at),
        })
    for tuteur in derniers_tuteurs:
        if est_modifie(tuteur.created_at, tuteur.updated_at):
            texte = f"Tuteur {tuteur.prenom} {tuteur.nom} mis à jour."
        else:
            texte = f"Tuteur {tuteur.prenom} {tuteur.nom} ajouté."
        activites.append({
            "type": "tuteur",
            "texte": texte,
            "date": str(tuteur.updated_at),
        })
    for inscription, eleve in dernieres_inscriptions:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip()
        reference = inscription.code_inscription or f"n°{inscription.id}"
        if est_modifie(inscription.created_at, inscription.updated_at):
            texte = f"Inscription {reference} mise à jour pour {nom_eleve}."
        else:
            texte = f"Inscription {reference} enregistrée pour {nom_eleve}."
        activites.append({
            "type": "inscription",
            "texte": texte,
            "date": str(inscription.updated_at),
        })
    for paiement, _inscription, eleve in derniers_paiements:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip() if eleve else "un élève"
        if est_modifie(paiement.created_at, paiement.updated_at):
            texte = f"Paiement de {paiement.montant:,.0f} FCFA modifié pour {nom_eleve}."
        else:
            texte = f"Paiement de {paiement.montant:,.0f} FCFA reçu pour {nom_eleve}."
        activites.append({
            "type": "paiement",
            "texte": texte,
            "date": str(paiement.updated_at),
        })
    for depense in dernieres_depenses:
        if est_modifie(depense.created_at, depense.updated_at):
            texte = f"Dépense « {depense.libelle} » de {depense.montant:,.0f} FCFA modifiée."
        else:
            texte = f"Dépense « {depense.libelle} » de {depense.montant:,.0f} FCFA enregistrée."
        activites.append({
            "type": "depense",
            "texte": texte,
            "date": str(depense.updated_at),
        })
    for document, eleve in derniers_documents:
        nom_eleve = f"{eleve.prenom} {eleve.nom}".strip() if eleve else "un élève"
        activites.append({
            "type": "document",
            "texte": f"Document « {document.filename} » ajouté pour l'élève {nom_eleve}.",
            "date": str(document.uploaded_at),
        })

    # Un événement de chaque type d'abord (pour que toutes les créations soient
    # visibles, y compris celles au timestamp ancien), puis on complète avec les
    # événements les plus récents restants jusqu'à la limite.
    par_type: dict = {}
    for a in activites:
        par_type.setdefault(a["type"], []).append(a)

    dernieres_activites = [items[0] for items in par_type.values()]
    autres = [a for items in par_type.values() for a in items[1:]]
    autres.sort(key=lambda a: a["date"], reverse=True)
    for a in autres:
        if len(dernieres_activites) >= TOTAL_ACTIVITES:
            break
        dernieres_activites.append(a)
    dernieres_activites.sort(key=lambda a: a["date"], reverse=True)
    if not include_finance:
        dernieres_activites = [a for a in dernieres_activites if a["type"] not in ("paiement", "depense")]

    # ── 7. ABSENCES SUR LES 7 DERNIERS JOURS (carte "Absences (7 derniers jours)") ──
    date_7j = aujourdhui - timedelta(days=6)  # fenêtre glissante de 7 jours, bornes incluses
    absences_7_jours = (
        db.query(func.count(models.Absences.id))
        .filter(models.Absences.date_absence >= date_7j)
        .filter(models.Absences.date_absence <= aujourdhui)
        .scalar() or 0
    )

    # ── 8. TOTAL DES PAIEMENTS DU MOIS EN COURS (carte "Paiements du mois") ──
    debut_mois = date(aujourdhui.year, aujourdhui.month, 1)
    paiements_mois = (
        db.query(func.coalesce(func.sum(models.Paiements.montant), 0.0))
        .filter(models.Paiements.date >= debut_mois)
        .filter(models.Paiements.date <= aujourdhui)
        .scalar() or 0.0
    )

    return {
        "nb_eleves": nb_eleves,
        "nb_enseignants": nb_enseignants,
        "nb_classes": nb_classes,
        "taux_absence": taux_absence,
        "absences_7_jours": absences_7_jours,
        "paiements_mois": round(float(paiements_mois), 2),
        "moyennes_par_classe": moyennes_par_classe,
        "repartition_niveaux": repartition_niveaux,
        "absences_par_mois": absences_par_mois,
        "dernieres_activites": dernieres_activites,
    }


def _stats_finances(db: Session) -> dict:
    """Tableau de bord du comptable : flux financiers uniquement."""
    aujourdhui = date.today()
    debut_mois = date(aujourdhui.year, aujourdhui.month, 1)

    # ── 1. FLUX DU MOIS EN COURS ─────────────────────────────────────────────
    paiements_mois = (
        db.query(func.coalesce(func.sum(models.Paiements.montant), 0.0))
        .filter(models.Paiements.date >= debut_mois, models.Paiements.date <= aujourdhui)
        .scalar() or 0.0
    )
    depenses_mois = (
        db.query(func.coalesce(func.sum(models.Depenses.montant), 0.0))
        .filter(models.Depenses.date >= debut_mois, models.Depenses.date <= aujourdhui)
        .scalar() or 0.0
    )
    solde_mois = paiements_mois - depenses_mois

    # ── 2. ÉCHÉANCES EN RETARD (relances) ────────────────────────────────────
    echeances_retard = (
        db.query(models.Echeances)
        .filter(
            models.Echeances.statut.in_(["EN_ATTENTE", "PARTIEL"]),
            models.Echeances.date_echeance < aujourdhui,
        )
        .all()
    )
    montant_en_retard = sum(max(e.montant_du - e.montant_paye, 0.0) for e in echeances_retard)

    # ── 3. ÉVOLUTION MENSUELLE (6 derniers mois) ─────────────────────────────
    mois_range = _derniers_mois(6)
    annee_min, mois_min, _ = mois_range[0]
    date_min = date(annee_min, mois_min, 1)
    paiements_par_mois = {
        (int(p.annee), int(p.mois)): float(p.total)
        for p in db.query(
            func.extract("year", models.Paiements.date).label("annee"),
            func.extract("month", models.Paiements.date).label("mois"),
            func.coalesce(func.sum(models.Paiements.montant), 0.0).label("total"),
        )
        .filter(models.Paiements.date >= date_min)
        .group_by(func.extract("year", models.Paiements.date), func.extract("month", models.Paiements.date))
        .all()
    }
    depenses_par_mois = {
        (int(d.annee), int(d.mois)): float(d.total)
        for d in db.query(
            func.extract("year", models.Depenses.date).label("annee"),
            func.extract("month", models.Depenses.date).label("mois"),
            func.coalesce(func.sum(models.Depenses.montant), 0.0).label("total"),
        )
        .filter(models.Depenses.date >= date_min)
        .group_by(func.extract("year", models.Depenses.date), func.extract("month", models.Depenses.date))
        .all()
    }
    evolution_mensuelle = [
        {
            "mois": label,
            "paiements": round(float(paiements_par_mois.get((a, m), 0.0)), 2),
            "depenses": round(float(depenses_par_mois.get((a, m), 0.0)), 2),
        }
        for a, m, label in mois_range
    ]

    # ── 4. ACTIVITÉ FINANCIÈRE RÉCENTE (paiements + dépenses) ────────────────
    activites: list[dict] = []
    derniers_paiements = (
        db.query(models.Paiements, models.Inscriptions, models.Eleves)
        .outerjoin(models.Inscriptions, models.Inscriptions.id == models.Paiements.id_inscription)
        .outerjoin(models.Eleves, models.Eleves.matricule == models.Inscriptions.matricule_eleve)
        .order_by(models.Paiements.updated_at.desc())
        .limit(8)
        .all()
    )
    for paiement, _inscription, eleve in derniers_paiements:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip() if eleve else "un élève"
        if est_modifie(paiement.created_at, paiement.updated_at):
            texte = f"Paiement de {paiement.montant:,.0f} FCFA modifié pour {nom_eleve}."
        else:
            texte = f"Paiement de {paiement.montant:,.0f} FCFA reçu pour {nom_eleve}."
        activites.append({
            "type": "paiement",
            "texte": texte,
            "date": str(paiement.updated_at),
        })
    dernieres_depenses = (
        db.query(models.Depenses)
        .order_by(models.Depenses.updated_at.desc())
        .limit(8)
        .all()
    )
    for depense in dernieres_depenses:
        if est_modifie(depense.created_at, depense.updated_at):
            texte = f"Dépense « {depense.libelle} » de {depense.montant:,.0f} FCFA modifiée."
        else:
            texte = f"Dépense « {depense.libelle} » de {depense.montant:,.0f} FCFA enregistrée."
        activites.append({
            "type": "depense",
            "texte": texte,
            "date": str(depense.updated_at),
        })
    activites.sort(key=lambda a: a["date"], reverse=True)
    activites = activites[:12]

    return {
        "paiements_mois": round(float(paiements_mois), 2),
        "depenses_mois": round(float(depenses_mois), 2),
        "solde_mois": round(float(solde_mois), 2),
        "echeances_en_retard": len(echeances_retard),
        "montant_en_retard": round(float(montant_en_retard), 2),
        "evolution_mensuelle": evolution_mensuelle,
        "dernieres_activites": activites,
    }


@router.get("/stats", response_model=schemas.DashboardStatsResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def get_dashboard_stats(
    utilisateur: models.Utilisateurs = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tableau de bord pédagogique (admin/directeur). Le directeur ne voit pas
    les flux financiers (paiements, dépenses)."""
    return _stats_direction(db, include_finance=utilisateur.role.value == "admin")


@router.get("/finances", response_model=schemas.DashboardFinanceResponse, dependencies=[Depends(require_role("admin", "comptable"))])
def get_dashboard_finances(db: Session = Depends(get_db)):
    """Tableau de bord du comptable : flux financiers uniquement."""
    return _stats_finances(db)