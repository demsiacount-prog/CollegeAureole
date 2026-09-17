"""Agrégations de l'application pour les documents officiels de rentrée.

- rapport_rentree      : Tableaux 1-3 du rapport succinct de rentrée (doc5).
- fiche_renseignements : Fiche de renseignements 2nd cycle (doc6).
- fiche_notes_compositions : Fiche de notes de composition 1er cycle (doc7).

Les comptages passent exclusivement par les inscriptions de l'année scolaire
sélectionnée (elles encadrent le couple classe × élève). Un élève est
« redoublant » si son inscription de l'année précédente a été déclarée
RECALE ; « exclu / transféré » si son inscription courante porte le statut
EXCLU ; tout le reste forme les « titulaires / admis ».
"""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

import models
import schemas
from bareme import bareme_niveau, est_jardin, niveau_ordre
from services.moyennes import calculer_moyennes_matiere_par_periode
from services.registre_notes import _periodes_classe

LABELS_ETUDE = {
    1: "1ère A", 2: "2ème A", 3: "3ème A", 4: "4ème A",
    5: "5ème A", 6: "6ème A", 7: "7ème A", 8: "8ème A", 9: "9ème A",
}

GENRES = ("M", "F")


# ─── Helpers de comptage ──────────────────────────────────────────────────────

def _annee_precedente(db: Session, annee: models.AnneesScolaires) -> Optional[models.AnneesScolaires]:
    return (
        db.query(models.AnneesScolaires)
        .filter(models.AnneesScolaires.date_debut < annee.date_debut)
        .order_by(models.AnneesScolaires.date_debut.desc())
        .first()
    )


def _inscriptions_annee(db: Session, annee: models.AnneesScolaires) -> list:
    """Inscriptions de l'année, avec classe et élève chargés."""
    return (
        db.query(models.Inscriptions)
        .options(
            joinedload(models.Inscriptions.classe),
            joinedload(models.Inscriptions.eleve),
        )
        .filter(models.Inscriptions.id_annee_scolaire == annee.id)
        .all()
    )


def _statuts_precedents(db: Session, annee: models.AnneesScolaires) -> dict:
    """matricule → statut_passage pour la dernière année antérieure."""
    precedente = _annee_precedente(db, annee)
    if precedente is None:
        return {}
    return {
        i.matricule_eleve: i.statut_passage
        for i in (
            db.query(models.Inscriptions)
            .filter(models.Inscriptions.id_annee_scolaire == precedente.id)
            .all()
        )
    }


def _statut_mentale(insc, precedents: dict) -> str:
    """Catégorie d'une inscription dans les effectifs de rentrée.

    Le compteur de redoublements (nb_redoublements) prime : il est incrémenté
    dès qu'un élève redouble (passage d'année / clôture), donc une valeur ≥ 1
    signifie que l'élève redouble l'année en cours. Sinon, la catégorie est
    déduite de l'historique (recalé l'année précédente) puis de l'exclusion.
    """
    if (getattr(insc, "nb_redoublements", 0) or 0) >= 1:
        return "RECALE"
    if precedents.get(insc.matricule_eleve) == "RECALE":
        return "RECALE"
    if insc.statut_passage == "EXCLU":
        return "EXCLU"
    return "TITULAIRE"


def _sexe(eleve) -> str:
    return "M" if (eleve and eleve.sexe == "M") else "F"


def _groupes_par_niveau(db: Session, annee: models.AnneesScolaires) -> dict:
    """niveau (ordre) → nombre de classes distinctes ayant des inscrits."""
    lignes = (
        db.query(models.Classes.niveau, models.Classes.id)
        .join(models.Inscriptions, models.Inscriptions.id_classe == models.Classes.id)
        .filter(models.Inscriptions.id_annee_scolaire == annee.id)
        .distinct(models.Classes.id)
        .all()
    )
    resultat: dict[int, int] = {}
    for niv, _classe_id in lignes:
        ordre = niveau_ordre(niv)
        if ordre is not None:
            resultat[ordre] = resultat.get(ordre, 0) + 1
    return resultat


def _cours_par_cycle(db: Session, annee: models.AnneesScolaires) -> tuple:
    """Distinct (premier, second) : nombre de classes et de salles par cycle."""
    inscriptions = _inscriptions_annee(db, annee)
    classes_visibles = {i.id_classe for i in inscriptions if i.id_classe}
    premier_classes: set = set()
    second_classes: set = set()
    for inscription in inscriptions:
        classe = inscription.classe
        if classe is None or classe.id not in classes_visibles:
            continue
        ordre = niveau_ordre(classe.niveau)
        if ordre is None:
            continue
        if ordre <= 6:
            premier_classes.add(classe.id)
        else:
            second_classes.add(classe.id)
    salles = {
        c.id: c.id_salle
        for c in (
            db.query(models.Classes)
            .filter(models.Classes.id.in_(classes_visibles or [0]))
            .all()
        )
        if c.id_salle
    }
    salles_1er = {salles[c] for c in premier_classes if c in salles}
    salles_2nd = {salles[c] for c in second_classes if c in salles}
    return (
        len(premier_classes),
        len(second_classes),
        len(salles_1er),
        len(salles_2nd),
    )


def _classer_enseignant(enseignant) -> str:
    """Branche un enseignant dans une colonne FE / FC / CE / CC / EM / Autres."""
    categorie = ((enseignant.categorie or "") + " " + (enseignant.fonction or "")).lower()
    if "fonctionnaire" in categorie:
        return "fe" if ("état" in categorie or "etat" in categorie) else "fc"
    if "ce" in categorie:
        return "ce"
    if "cc" in categorie:
        return "cc"
    if "maître" in categorie or "maitre" in categorie or "em" in categorie:
        return "em"
    return "autres"


_CYCLE_LABEL = {0: "Premier cycle", 1: "Second Cycle"}


def _cycle_enseignant(enseignant) -> Optional[int]:
    """0 = premier cycle, 1 = second cycle ; None si indéterminé."""
    for champ in (getattr(enseignant, "classe_tenue", None), getattr(enseignant, "dernier_poste", None)):
        if not champ:
            continue
        match = niveau_ordre(champ)
        if match is not None:
            return 0 if match <= 6 else 1
    return None


def _compteurs_enseignants(db: Session) -> list:
    resultats: list = [{"cycle": 0, "fe": 0, "fc": 0, "ce": 0, "cc": 0, "autres": 0, "em": 0},
                       {"cycle": 1, "fe": 0, "fc": 0, "ce": 0, "cc": 0, "autres": 0, "em": 0}]
    for enseignant in db.query(models.Enseignants).all():
        cycle = _cycle_enseignant(enseignant)
        if cycle is None:
            continue
        branche = _classer_enseignant(enseignant)
        resultats[cycle][branche] += 1
    return resultats


def _resultat_cycle(cycle: int, compteur: dict) -> schemas.RapportRentreeCycle:
    labels = {"fe": "fe", "fc": "fc", "ce": "ce", "cc": "cc", "autres": "autres", "em": "em"}
    valeurs = {cle: compteur[cle] for cle in labels}
    return schemas.RapportRentreeCycle(cycle=_CYCLE_LABEL[cycle], **valeurs,
                                       total=sum(valeurs.values()))


# ─── Rapport succinct de rentrée (doc5) ───────────────────────────────────────

def _cycles_coches(inscriptions: list) -> list:
    """Case(s) cochée(s) des cycles d'enseignement (doc5, Tableau 1)."""
    ordres = {niveau_ordre(i.classe.niveau) for i in inscriptions if i.classe}
    a_premier = any(o is not None and o <= 6 for o in ordres)
    a_second = any(o is not None and o >= 7 for o in ordres)
    if a_premier and a_second:
        return ["3. Cycles complets"]
    if a_second:
        return ["2. 2è cycle"]
    if a_premier:
        return ["1. 1er cycle"]
    return []


def rapport_rentree(db: Session, annee: models.AnneesScolaires, etab: models.Etablissement | None) -> schemas.RapportRentreeResponse:
    inscriptions = _inscriptions_annee(db, annee)
    precedents = _statuts_precedents(db, annee)
    groupes = _groupes_par_niveau(db, annee)

    classes_out: List[schemas.RapportRentreeClasse] = []
    totals = {"g": 0, "f": 0, "r_g": 0, "r_f": 0}
    for ordre in range(1, 10):
        inscrits = [i for i in inscriptions if i.classe and niveau_ordre(i.classe.niveau) == ordre]
        g = sum(1 for i in inscrits if _sexe(i.eleve) == "M")
        f = len(inscrits) - g
        redoublants = [i for i in inscrits if _statut_mentale(i, precedents) == "RECALE"]
        r_g = sum(1 for i in redoublants if _sexe(i.eleve) == "M")
        r_f = len(redoublants) - r_g
        totals["g"] += g
        totals["f"] += f
        totals["r_g"] += r_g
        totals["r_f"] += r_f
        classes_out.append(
            schemas.RapportRentreeClasse(
                annee_etude=LABELS_ETUDE[ordre],
                groupes=groupes.get(ordre, 0),
                garcons=g,
                filles=f,
                total=len(inscrits),
                redoublants_g=r_g,
                redoublants_f=r_f,
                redoublants_total=len(redoublants),
            )
        )

    compteurs = _compteurs_enseignants(db)
    _n_cours_1er, _n_cours_2nd, n_salles_1er, n_salles_2nd = _cours_par_cycle(db, annee)

    return schemas.RapportRentreeResponse(
        annee_label=annee.libelle,
        ecole=(etab.nom or "Collège Auréole") if etab else "Collège Auréole",
        village_quartier=etab.village_quartier if etab else None,
        commune=etab.commune if etab else None,
        cap=etab.cap if etab else None,
        cercle=etab.cercle if etab else None,
        ae=etab.academie if etab else None,
        cycles=_cycles_coches(inscriptions),
        statuts=([etab.statut_administratif] if etab and etab.statut_administratif else []),
        types_modes=[v for v in (etab.type_ecole, etab.mode) if v] if etab else [],
        classes=classes_out,
        total_garcons=totals["g"],
        total_filles=totals["f"],
        total_general=totals["g"] + totals["f"],
        total_redoublants_g=totals["r_g"],
        total_redoublants_f=totals["r_f"],
        total_redoublants=totals["r_g"] + totals["r_f"],
        premiers_cycle=_resultat_cycle(0, compteurs[0]),
        second_cycle=_resultat_cycle(1, compteurs[1]),
        nb_salles_1er=n_salles_1er,
        nb_salles_2nd=n_salles_2nd,
    )


# ─── Fiche de renseignements de rentrée, 2nd cycle (doc6) ─────────────────────

def _classes_par_niveau(inscriptions: list) -> dict:
    resultat: dict = {}
    for insc in inscriptions:
        if not insc.classe:
            continue
        ordre = niveau_ordre(insc.classe.niveau)
        if ordre is None:
            continue
        resultat.setdefault(ordre, set()).add(insc.id_classe)
    return {o: list(v) for o, v in resultat.items()}


def _ligne_renseignements(inscriptions: list, precedents: dict, libelle: str, cle: str, niveaux: tuple) -> schemas.FicheRenseignementsLigne:
    cell_par_ordre: dict = {}
    for ordre in niveaux:
        cell_par_ordre[ordre] = schemas.FicheRenseignementsCellule()
    total = schemas.FicheRenseignementsCellule()

    for insc in inscriptions:
        if not insc.classe:
            continue
        ordre = niveau_ordre(insc.classe.niveau)
        if ordre not in niveaux:
            continue
        if _statut_mentale(insc, precedents) != cle:
            continue
        sex = _sexe(insc.eleve)
        cellule = cell_par_ordre[ordre]
        if sex == "M":
            cellule.garcons += 1
        else:
            cellule.filles += 1
        cellule.total += 1
        if sex == "M":
            total.garcons += 1
        else:
            total.filles += 1
        total.total += 1

    classes_ids = _classes_par_niveau(inscriptions)
    for ordre in niveaux:
        cellule = cell_par_ordre[ordre]
        cellule.rc = len(classes_ids.get(ordre, []))
        total.rc += cellule.rc

    return schemas.FicheRenseignementsLigne(libelle=libelle, sept=cell_par_ordre[niveaux[0]],
                                            huit=cell_par_ordre[niveaux[1]], neuf=cell_par_ordre[niveaux[2]],
                                            total=total)


def _effectifs_renseignements(inscriptions: list, precedents: dict) -> list:
    return [
        _ligne_renseignements(inscriptions, precedents, "Titulaire / Adm.", "TITULAIRE", (7, 8, 9)),
        _ligne_renseignements(inscriptions, precedents, "Redoublants", "RECALE", (7, 8, 9)),
        _ligne_renseignements(inscriptions, precedents, "Exclus / Transf.", "EXCLU", (7, 8, 9)),
    ]


def fiche_renseignements(db: Session, annee: models.AnneesScolaires, etab: models.Etablissement | None) -> schemas.FicheRenseignementsResponse:
    inscriptions = _inscriptions_annee(db, annee)
    precedents = _statuts_precedents(db, annee)
    effectifs = _effectifs_renseignements(inscriptions, precedents)

    personnel: List[schemas.FicheRenseignementsPersonnel] = []
    for ens in db.query(models.Enseignants).order_by(models.Enseignants.nom, models.Enseignants.prenom).all():
        personnel.append(
            schemas.FicheRenseignementsPersonnel(
                prenom=ens.prenom,
                nom=ens.nom,
                genre=ens.genre,
                nina=ens.nina,
                date_naissance=ens.date_naissance,
                categorie=ens.categorie,
                classe=ens.classe_tenue,
                echelon=ens.echelon,
                fonction=ens.fonction,
                sf_nombre_enfants=ens.sf_nombre_enfants,
                date_contrat=ens.date_contrat,
                classe_tenue=ens.classe_tenue,
                dernier_poste=ens.dernier_poste,
                date_arrivee_cap=ens.date_arrivee_cap,
                observations=ens.observations,
                diplome=ens.diplome,
            )
        )

    return schemas.FicheRenseignementsResponse(
        annee_label=annee.libelle,
        academie=etab.academie if etab else None,
        cap=etab.cap if etab else None,
        ecole=(etab.nom or "Collège Auréole") if etab else "Collège Auréole",
        telephone=etab.telephone if etab else None,
        dirigee_par=None,
        effectifs=effectifs,
        personnel=personnel,
    )


# ─── Fiche de renseignements de rentrée, 1er cycle —───────────────────────────
# Tableau de bord recto/verso distinct de celui du 2nd cycle : effectifs par
# année 1ère→6ème (sous-colonnes N.C / G / F / T) sur 3 lignes (Inscrits,
# Redoublants, Exclus), infrastructures/mobiliers, puis personnel administratif
# (section II) et personnel enseignant (section III).

_ORDRE_PREMIER_CYCLE = (1, 2, 3, 4, 5, 6)


def _ligne_renseignements_pc(inscriptions, precedents, libelle, presenter, niveaux) -> schemas.FicheRensPCLigne:
    """Construit une ligne d'effectifs du 1er cycle : une colonne chiffrée par
    année (1ère→6ème) plus la colonne TOTAL, toutes en N.C / G / F / T."""
    cell_par_ordre: dict = {}
    for ordre in niveaux:
        cell_par_ordre[ordre] = schemas.FicheRenseignementsCellule()
    total = schemas.FicheRenseignementsCellule()

    for insc in inscriptions:
        if not insc.classe:
            continue
        ordre = niveau_ordre(insc.classe.niveau)
        if ordre not in niveaux:
            continue
        if not presenter(_statut_mentale(insc, precedents)):
            continue
        sex = _sexe(insc.eleve)
        cellule = cell_par_ordre[ordre]
        if sex == "M":
            cellule.garcons += 1
        else:
            cellule.filles += 1
        cellule.total += 1
        if sex == "M":
            total.garcons += 1
        else:
            total.filles += 1
        total.total += 1

    classes_ids = _classes_par_niveau(inscriptions)
    for ordre in niveaux:
        cellule = cell_par_ordre[ordre]
        cellule.rc = len(classes_ids.get(ordre, []))
        total.rc += cellule.rc

    return schemas.FicheRensPCLigne(
        libelle=libelle,
        annee_1=cell_par_ordre[niveaux[0]], annee_2=cell_par_ordre[niveaux[1]],
        annee_3=cell_par_ordre[niveaux[2]], annee_4=cell_par_ordre[niveaux[3]],
        annee_5=cell_par_ordre[niveaux[4]], annee_6=cell_par_ordre[niveaux[5]],
        total=total,
    )


def _effectifs_renseignements_pc(inscriptions, precedents) -> list:
    """Trois lignes officielles : Inscrits/Effectifs, Redoublants, Exclus."""
    def present(cat: str) -> bool:
        return cat != "EXCLU"
    return [
        _ligne_renseignements_pc(inscriptions, precedents, "Inscrits / Effectifs", present, _ORDRE_PREMIER_CYCLE),
        _ligne_renseignements_pc(inscriptions, precedents, "Redoublants (Red)", lambda c: c == "RECALE", _ORDRE_PREMIER_CYCLE),
        _ligne_renseignements_pc(inscriptions, precedents, "Exclus (Excl)", lambda c: c == "EXCLU", _ORDRE_PREMIER_CYCLE),
    ]


def _encode_personnel_pc(ens) -> schemas.FicheRensPCPersonnel:
    return schemas.FicheRensPCPersonnel(
        prenom=ens.prenom,
        nom=ens.nom,
        numero_mle=ens.nina or ens.matricule,
        date_naissance=ens.date_naissance,
        grade=ens.categorie,
        sf=ens.sf_nombre_enfants,
        nbre_enfants=ens.sf_nombre_enfants,
        fonction=ens.fonction,
        date_recrutement=ens.date_contrat,
        date_titularisation=None,
        date_dernier_avancement=None,
        dernier_poste=ens.dernier_poste,
        date_arrivee_cap=ens.date_arrivee_cap,
        classe_tenue=ens.classe_tenue,
        observations=ens.observations,
        diplome=ens.diplome,
    )


def _est_administratif(ens) -> bool:
    """Un agent est administratif uniquement si sa fonction (ou classe tenue)
    comporte un rôle d'administration explicite. Les enseignants — même sans
    « classe tenue » renseignée — relèvent du personnel enseignant."""
    fonction = ((ens.fonction or "") + " " + (ens.classe_tenue or "")).lower()
    return any(m in fonction for m in ("directeur", "secretaire", "secrétaire", "gardien",
                                       "comptable", "intendant", "agent"))


def fiche_renseignements_premier_cycle(
    db: Session, annee: models.AnneesScolaires, etab: models.Etablissement | None,
) -> schemas.FicheRenseignementsPremierCycleResponse:
    inscriptions = _inscriptions_annee(db, annee)
    precedents = _statuts_precedents(db, annee)
    effectifs = _effectifs_renseignements_pc(inscriptions, precedents)

    personnels_admin: List[schemas.FicheRensPCPersonnel] = []
    personnels_enseignants: List[schemas.FicheRensPCPersonnel] = []
    for ens in db.query(models.Enseignants).order_by(models.Enseignants.nom, models.Enseignants.prenom).all():
        if _est_administratif(ens):
            personnels_admin.append(_encode_personnel_pc(ens))
        else:
            personnels_enseignants.append(_encode_personnel_pc(ens))

    infra = (
        db.query(models.EtablissementInfrastructures)
        .filter(models.EtablissementInfrastructures.id_annee_scolaire == annee.id)
        .first()
    )
    return schemas.FicheRenseignementsPremierCycleResponse(
        annee_label=annee.libelle,
        cap=etab.cap if etab else None,
        commune=etab.commune if etab else None,
        ecole=(etab.nom or "Collège Auréole") if etab else "Collège Auréole",
        village_quartier=etab.village_quartier if etab else None,
        dirige_par=None,
        telephone=etab.telephone if etab else None,
        effectifs=effectifs,
        personnel_admin=personnels_admin,
        personnel_enseignant=personnels_enseignants,
        infrastructures=(None if infra is None else schemas.FicheRensPCInfrastructures(
            salles_dur=infra.salles_dur,
            salles_semi_dur=infra.salles_semi_dur,
            salles_banco=infra.salles_banco,
            salles_autres=infra.salles_autres,
            direction_dur=infra.direction_dur,
            direction_banco=infra.direction_banco,
            direction_autres=infra.direction_autres,
            logement_direction=infra.logement_direction,
            tables_bancs=infra.tables_bancs,
            chaises=infra.chaises,
            armoires=infra.armoires,
            tableaux=infra.tableaux,
            mobilier_divers=infra.mobilier_divers,
        )),
    )


# ─── Fiche de notes mensuelle / de composition, élève (doc7 + doc3) ───────────

def _moyenne_periode_eleve(db: Session, matricule: str, periode) -> Optional[float]:
    par_cours = calculer_moyennes_matiere_par_periode(db, matricule, [periode])[periode.id]
    valeurs = [v for v in par_cours.values() if v is not None]
    return round(sum(valeurs) / len(valeurs), 2) if valeurs else None


def fiche_notes_compositions(
    db: Session,
    matricule: str,
    annee: models.AnneesScolaires,
    eleve: models.Eleves,
    insc,
    trimestre_id: Optional[int] = None,
) -> schemas.FicheNotesCompoResponse:
    classe = insc.classe
    niveau = classe.niveau if classe else None
    est_j = est_jardin(niveau)
    bareme = bareme_niveau(niveau)
    periodes = _periodes_classe(db, insc.id_classe, annee.id) if classe else []

    if trimestre_id is not None:
        periode = next((t for t in periodes if t.id == trimestre_id), None)
    else:
        periode = periodes[-1] if periodes else None

    if est_j or not classe or periode is None:
        raise ValueError("Cette fiche ne s'applique qu'aux classes du 1er cycle avec compositions.")

    # Matières réelles de la classe, dans l'ordre de leur affectation.
    affectations = (
        db.query(models.AffectationCoursClasse)
        .options(joinedload(models.AffectationCoursClasse.cours))
        .filter(models.AffectationCoursClasse.id_classe == insc.id_classe)
        .order_by(models.AffectationCoursClasse.id_classe, models.AffectationCoursClasse.id_cours)
        .all()
    )

    par_cours = calculer_moyennes_matiere_par_periode(db, matricule, [periode])[periode.id]
    matieres: List[schemas.FicheNotesCompoMatiere] = []
    poids = True  # coefficient réel de l'affectation
    for aff in affectations:
        cours = aff.cours
        nom = cours.nom if cours else "—"
        matieres.append(
            schemas.FicheNotesCompoMatiere(
                matiere=nom,
                note=par_cours.get(nom),
                coef=float(aff.coefficient),
                observation=None,
            )
        )

    # Rang et effectif de la période pour l'ensemble de la classe.
    notes_classe: list = []
    effectif = 0
    inscriptions_classe = (
        db.query(models.Inscriptions)
        .options(joinedload(models.Inscriptions.eleve))
        .filter(
            models.Inscriptions.id_classe == insc.id_classe,
            models.Inscriptions.id_annee_scolaire == annee.id,
        )
        .all()
    )
    for i in inscriptions_classe:
        if not i.eleve:
            continue
        effectif += 1
        moy = _moyenne_periode_eleve(db, i.matricule_eleve, periode)
        if moy is not None:
            notes_classe.append((i.matricule_eleve, moy))

    ma_moy = _moyenne_periode_eleve(db, matricule, periode)
    rang = None
    if ma_moy is not None:
        rang = sum(1 for _, m in notes_classe if m > ma_moy) + 1

    # Moyennes annuelles de la période → rang annuel.
    annuels_classe: list = []
    for i in inscriptions_classe:
        if not i.eleve:
            continue
        vals = []
        for t in periodes:
            moy = _moyenne_periode_eleve(db, i.matricule_eleve, t)
            if moy is not None:
                vals.append(moy)
        m_ann = round(sum(vals) / len(vals), 2) if vals else None
        annuels_classe.append((i.matricule_eleve, m_ann))

    m_ann_eleve = next((m for mat, m in annuels_classe if mat == matricule), None)
    rang_annuel = None
    if m_ann_eleve is not None:
        rang_annuel = sum(1 for _, m in annuels_classe if m is not None and m > m_ann_eleve) + 1

    total_notes = None
    notes = [m.note for m in matieres if m.note is not None]
    if notes:
        total_notes = round(sum(notes), 2)

    return schemas.FicheNotesCompoResponse(
        matricule=eleve.matricule,
        nom=eleve.nom,
        prenom=eleve.prenom,
        niveau=niveau,
        classe=f"{classe.niveau} {classe.nom}" if classe else None,
        bareme=bareme,
        est_jardin=est_j,
        annee_label=annee.libelle,
        mois=periode.nom,
        matieres=matieres,
        total_notes=total_notes,
        moyenne=ma_moy,
        rang=rang,
        effectif=effectif,
        moyenne_annuelle=m_ann_eleve,
        rang_annuel=rang_annuel,
        effectif_annuel=effectif,
    )