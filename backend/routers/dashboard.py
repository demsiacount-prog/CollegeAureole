from datetime import date, datetime, timedelta
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


@router.get("/stats", response_model=schemas.DashboardStatsResponse, dependencies=[Depends(require_role("admin", "directeur"))])
def get_dashboard_stats(db: Session = Depends(get_db)):

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
        {"classe": f"{niveau} {nom}", "moy": round(float(moy), 1) if moy is not None else 0}
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
        if isinstance(d, str):
            d = datetime.fromisoformat(d).date()
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
        .order_by(models.Notes.created_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    dernieres_absences = (
        db.query(models.Absences, models.Eleves)
        .join(models.Eleves, models.Eleves.matricule == models.Absences.matricule_eleve)
        .order_by(models.Absences.created_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_eleves = (
        db.query(models.Eleves)
        .order_by(models.Eleves.created_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_enseignants = (
        db.query(models.Enseignants)
        .order_by(models.Enseignants.created_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_tuteurs = (
        db.query(models.Tuteurs)
        .order_by(models.Tuteurs.created_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    dernieres_inscriptions = (
        db.query(models.Inscriptions, models.Eleves)
        .join(models.Eleves, models.Eleves.matricule == models.Inscriptions.matricule_eleve)
        .order_by(models.Inscriptions.created_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    derniers_paiements = (
        db.query(models.Paiements, models.Inscriptions, models.Eleves)
        .outerjoin(models.Inscriptions, models.Inscriptions.id == models.Paiements.id_inscription)
        .outerjoin(models.Eleves, models.Eleves.matricule == models.Inscriptions.matricule_eleve)
        .order_by(models.Paiements.created_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )
    dernieres_depenses = (
        db.query(models.Depenses)
        .order_by(models.Depenses.created_at.desc())
        .limit(LIMIT_PAR_TYPE)
        .all()
    )

    activites = []
    for note, eleve, classe in dernieres_notes:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip()
        nom_classe = classe.nom if classe else "sa classe"
        bm = bareme_niveau(classe.niveau) if classe else 20
        activites.append({
            "type": "note",
            "texte": f"Note de {note.note}/{bm} ajoutée pour {nom_eleve} ({nom_classe}).",
            "date": str(note.created_at),
        })
    for absence, eleve in dernieres_absences:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip()
        statut = "justifiée" if absence.justifiee else "non justifiée"
        activites.append({
            "type": "absence",
            "texte": f"Absence {statut} enregistrée pour {nom_eleve}.",
            "date": str(absence.created_at),
        })
    for eleve in derniers_eleves:
        activites.append({
            "type": "eleve",
            "texte": f"Nouvel élève {eleve.prenom} {eleve.nom} enregistré.",
            "date": str(eleve.created_at),
        })
    for enseignant in derniers_enseignants:
        activites.append({
            "type": "enseignant",
            "texte": f"Enseignant {enseignant.prenom} {enseignant.nom} ajouté.",
            "date": str(enseignant.created_at),
        })
    for tuteur in derniers_tuteurs:
        activites.append({
            "type": "tuteur",
            "texte": f"Tuteur {tuteur.prenom} {tuteur.nom} ajouté.",
            "date": str(tuteur.created_at),
        })
    for inscription, eleve in dernieres_inscriptions:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip()
        reference = inscription.code_inscription or f"n°{inscription.id}"
        activites.append({
            "type": "inscription",
            "texte": f"Inscription {reference} enregistrée pour {nom_eleve}.",
            "date": str(inscription.created_at),
        })
    for paiement, _inscription, eleve in derniers_paiements:
        nom_eleve = f"{eleve.nom} {eleve.prenom}".strip() if eleve else "un élève"
        activites.append({
            "type": "paiement",
            "texte": f"Paiement de {paiement.montant:,.0f} FCFA reçu pour {nom_eleve}.",
            "date": str(paiement.created_at),
        })
    for depense in dernieres_depenses:
        activites.append({
            "type": "depense",
            "texte": f"Dépense « {depense.libelle} » de {depense.montant:,.0f} FCFA enregistrée.",
            "date": str(depense.created_at),
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