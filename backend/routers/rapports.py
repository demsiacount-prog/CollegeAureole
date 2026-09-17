import re
import unicodedata
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session, joinedload

from database import get_db
import models
import schemas
from security import get_current_user
from bareme import (
    bareme_niveau,
    est_jardin,
    niveau_ordre,
    seuil_passage,
)
from services.moyennes import (
    calculer_moyenne_annuelle,
    calculer_moyennes_matiere_par_periode,
    calculer_moyennes_par_trimestre,
    calculer_notes_par_matiere,
)
from services.registre_notes import _periodes_classe
from services import effectifs as effectifs_service
from services import rapports_pdf as pdf_service

# ─── Fiche de suivi au second cycle (formulaire officiel DEF) ────────────────
# Matières du formulaire, dans l'ordre officiel ; la catégorie sert au calcul
# de l'orientation finale (Littéraire vs Scientifique). La correspondance avec
# les cours réels de l'application se fait par nom normalisé ; sans
# correspondance, la cellule affiche « — ».
MATIERES_FIXES = [
    ("Rédaction", "litt"),
    ("Dictée et Questions", "litt"),
    ("Histoire-Géographie", "litt"),
    ("Langue", "litt"),
    ("Mathématiques", "scient"),
    ("Physique-Chimie", "scient"),
    ("Sciences Naturelles", "scient"),
]
_CATEGORIE_MATIERE = dict(MATIERES_FIXES)

# Grille fixe du formulaire officiel (31 colonnes) : 7 périodes « classe × nème
# passage », chacune avec un nombre de sous-colonnes trimestrielles imposé.
# La 9ème 3ème Fois ne présente que 2 trimestres (site officiel).
PERIODES_FICHE = [
    (7, 1, "7ème 1ère Fois", 3),
    (7, 2, "7ème 2ème Fois", 3),
    (8, 1, "8ème 1ère Fois", 3),
    (8, 2, "8ème 2ème Fois", 3),
    (9, 1, "9ème 1ère Fois", 2),
    (9, 2, "9ème 2ème Fois", 2),
    (9, 3, "9ème 3ème Fois", 2),
]
SOUS_COMPTES_FICHE = [nb for _, _, _, nb in PERIODES_FICHE]
_NB_CELLULES_FICHE = sum(SOUS_COMPTES_FICHE)  # 18 cellules de notes
_ORDRE_SECOND_CYCLE = (7, 8, 9)
_LABELS_PASSAGE = {1: "1ère Fois", 2: "2ème Fois", 3: "3ème Fois"}

_REMARQUES_FICHE = [
    "En aucun cas, la fiche ne sera remise ni à l'élève ni à ses parents ;",
    "En cas de changement d'établissement, cette fiche sera transmise au Directeur de CAP qui reçoit l'élève ;",
    "Cette fiche ne doit comporte aucune surcharge ni rature sous peine de nullité ;",
    "La non production de cette fiche entraine la non orientation de l'élève ;",
    "Lorsque l'élève est admis au DEF, envoyer la fiche à l'Académie de l'enseignement immédiatement après les résultats.",
]


def _normaliser(texte: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", (texte or "").lower()) if not unicodedata.combining(c)
    ).strip()


def _correspond_cours(nom_fixe: str, nom_cours: str) -> bool:
    a, b = _normaliser(nom_fixe), _normaliser(nom_cours)
    if not a or not b:
        return False
    return a in b or b in a


def _tendance_ligne(valeurs_passage: list) -> Optional[str]:
    """Flèche de tendance d'une matière entre le dernier et l'avant-dernier passage."""
    non_nuls = [v for v in valeurs_passage if v is not None]
    if len(non_nuls) < 2:
        return None
    precedent, courant = non_nuls[-2], non_nuls[-1]
    if courant > precedent + 0.05:
        return "↗"
    if courant < precedent - 0.05:
        return "↘"
    return "→"


def _orientation_finale(lignes) -> Optional[str]:
    """Comparaison du niveau littéraire (4 matières) vs scientifique (3) sur tout le 2e cycle."""
    litt = [v for ligne in lignes if _CATEGORIE_MATIERE.get(ligne.matiere) == "litt" for v in ligne.valeurs if v is not None]
    scient = [v for ligne in lignes if _CATEGORIE_MATIERE.get(ligne.matiere) == "scient" for v in ligne.valeurs if v is not None]
    if not litt or not scient:
        return None
    return "Littéraire" if (sum(litt) / len(litt)) >= (sum(scient) / len(scient)) else "Scientifique"


def _grille_suivi(db, matricule: str, inscriptions) -> tuple:
    """Grille officielle de la fiche : 7 matières × grille fixe de 23 colonnes.

    Le formulaire présente toujours les 7 périodes (7è/8è 1ère & 2ème Fois,
    9è 1ère/2ème/3ème Fois) avec 3 trimestres pour les 4 premières périodes
    et 2 pour les trois dernières (18 colonnes de notes), puis 4 colonnes de
    tendance (hachurée + « 1er/2e/3e Fois »).
    On cale les moyennes réelles de chaque passage sur ce cadre fixe ; les
    cellules correspondant à des passages non effectués restent vides. Le
    champ « nème Fois » de la zone Tendance reçoit un × à hauteur du nombre
    de passages de la dernière classe suivie (redoublement).
    """
    par_niveau = {7: [], 8: [], 9: []}
    for ins in inscriptions:
        classe = ins.classe
        if classe is None:
            continue
        ordre = niveau_ordre(classe.niveau)
        if ordre in par_niveau:
            par_niveau[ordre].append(ins)

    # (ordre, passage) → inscription, numérotation chronologique par niveau.
    indice_par_passage: dict[tuple, models.Inscriptions] = {}
    for ordre in _ORDRE_SECOND_CYCLE:
        for i, ins in enumerate(par_niveau[ordre]):
            indice_par_passage[(ordre, i + 1)] = ins

    cellules: dict[str, list] = {nom: [None] * _NB_CELLULES_FICHE for nom, _ in MATIERES_FIXES}
    moyennes_passage_matiere: dict[str, list] = {nom: [] for nom, _ in MATIERES_FIXES}
    colonnes: list[schemas.FicheSuiviPassage] = []

    offset = 0
    for ordre, passage, libelle, nb_sous in PERIODES_FICHE:
        ins_reel = indice_par_passage.get((ordre, passage))

        valeurs_par_matiere: dict[str, list] = {}
        if ins_reel is not None:
            periodes = _periodes_classe(db, ins_reel.id_classe, ins_reel.id_annee_scolaire)
            nbc = max(1, len(periodes))
            par_periode = calculer_moyennes_matiere_par_periode(db, matricule, periodes)
            cours_par_fixe = {
                nom_fixe: next(
                    (cn for map_p in par_periode.values() for cn in map_p if _correspond_cours(nom_fixe, cn)),
                    None,
                )
                for nom_fixe, _ in MATIERES_FIXES
            }
            for nom_fixe, _ in MATIERES_FIXES:
                cours = cours_par_fixe[nom_fixe]
                vals = (
                    [par_periode[t.id].get(cours) for t in periodes]
                    if cours is not None and periodes
                    else [None] * nbc
                )
                vals = vals[:nb_sous]
                vals += [None] * (nb_sous - len(vals))
                valeurs_par_matiere[nom_fixe] = vals
                cellules[nom_fixe][offset : offset + nb_sous] = vals
                non_nuls = [v for v in vals if v is not None]
                moyennes_passage_matiere[nom_fixe].append(
                    round(sum(non_nuls) / len(non_nuls), 2) if non_nuls else None
                )
            moyennes_passage = []
            for j in range(nb_sous):
                notes_j = [valeurs_par_matiere[nf][j] for nf, _ in MATIERES_FIXES]
                non_nuls = [v for v in notes_j if v is not None]
                moyennes_passage.append(round(sum(non_nuls) / len(non_nuls), 2) if non_nuls else None)
            colonnes.append(
                schemas.FicheSuiviPassage(
                    niveau=f"{ordre}ème Année",
                    passage=passage,
                    label=libelle,
                    annee_label=ins_reel.annee_scolaire.libelle if ins_reel.annee_scolaire else None,
                    statut_passage=ins_reel.statut_passage,
                    moyenne_annuelle=calculer_moyenne_annuelle(db, matricule, ins_reel.id_annee_scolaire),
                    effectue=True,
                    moyennes=moyennes_passage,
                )
            )
        else:
            for nom_fixe, _ in MATIERES_FIXES:
                moyennes_passage_matiere[nom_fixe].append(None)
            colonnes.append(
                schemas.FicheSuiviPassage(
                    niveau=f"{ordre}ème Année",
                    passage=passage,
                    label=libelle,
                    annee_label=None,
                    statut_passage=None,
                    moyenne_annuelle=None,
                    effectue=False,
                    moyennes=[None] * nb_sous,
                )
            )
        offset += nb_sous

    lignes = [
        schemas.FicheSuiviLigne(
            matiere=nom_fixe,
            valeurs=cellules[nom_fixe],
            tendance=_tendance_ligne(moyennes_passage_matiere[nom_fixe]),
        )
        for nom_fixe, _ in MATIERES_FIXES
    ]

    # × de la zone « nème Fois » : dernier passage suivi de la dernière classe.
    derniers = [c for c in colonnes if c.effectue]
    fois_x = derniers[-1].passage if derniers else 1

    return colonnes, lignes, _orientation_finale(lignes), fois_x

router = APIRouter(
    prefix="/api/rapports",
    tags=["Rapports et documents"],
    dependencies=[Depends(get_current_user)],
)


def _annee(db: Session, annee_id: Optional[int] = None) -> models.AnneesScolaires:
    if annee_id is not None:
        annee = (
            db.query(models.AnneesScolaires)
            .filter(models.AnneesScolaires.id == annee_id)
            .first()
        )
        if not annee:
            raise HTTPException(status_code=404, detail="Année scolaire introuvable")
        return annee
    annee = (
        db.query(models.AnneesScolaires)
        .filter(models.AnneesScolaires.active == True)
        .first()
    )
    if not annee:
        raise HTTPException(status_code=404, detail="Aucune année scolaire active")
    return annee


def _get_eleve(db: Session, matricule: str) -> models.Eleves:
    eleve = db.query(models.Eleves).filter(models.Eleves.matricule == matricule).first()
    if not eleve:
        raise HTTPException(status_code=404, detail="Élève introuvable")
    return eleve


def _inscription(db: Session, matricule: str, id_annee: int) -> Optional[models.Inscriptions]:
    return (
        db.query(models.Inscriptions)
        .options(joinedload(models.Inscriptions.classe))
        .filter(
            models.Inscriptions.matricule_eleve == matricule,
            models.Inscriptions.id_annee_scolaire == id_annee,
        )
        .first()
    )


def _rang_classe(
    db: Session, id_classe: int, id_annee: int, matricule: str, est_jardin_classe: bool
) -> tuple[Optional[int], int]:
    if est_jardin_classe:
        return None, 0
    inscriptions = (
        db.query(models.Inscriptions)
        .options(joinedload(models.Inscriptions.eleve))
        .filter(
            models.Inscriptions.id_classe == id_classe,
            models.Inscriptions.id_annee_scolaire == id_annee,
        )
        .all()
    )
    effectif = 0
    moyennes: list[tuple[str, Optional[float]]] = []
    for insc in inscriptions:
        if not insc.eleve:
            continue
        effectif += 1
        moyennes.append(
            (insc.matricule_eleve, calculer_moyenne_annuelle(db, insc.matricule_eleve, id_annee))
        )
    m_eleve = calculer_moyenne_annuelle(db, matricule, id_annee)
    if m_eleve is None:
        return None, effectif
    rang = sum(1 for _, m in moyennes if m is not None and m > m_eleve) + 1
    return rang, effectif


def _etablissement(db: Session):
    return db.query(models.Etablissement).first()


def _nom_fichier(base: str, matricule: str, nom: str, prenom: str) -> str:
    def _ascii(texte: str) -> str:
        nfkd = unicodedata.normalize("NFKD", texte)
        return "".join(c for c in nfkd if not unicodedata.combining(c))

    identite = re.sub(r"[^A-Za-z0-9]+", "_", f"{_ascii(prenom)} {_ascii(nom)} {matricule}").strip("_")
    return f"{base}_{identite}.pdf"


# ─── Acte de naissance ─────────────────────────────────────────────────────────


@router.get("/eleves/{matricule}/fiche-suivi", response_model=schemas.FicheSuiviResponse)
def fiche_suivi(
    matricule: str,
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    eleve = _get_eleve(db, matricule)
    annee = _annee(db, annee_id)
    insc = _inscription(db, matricule, annee.id)

    classe = insc.classe if insc else None
    niveau = classe.niveau if classe else None

    # La fiche de suivi se délivre aux élèves du second cycle du fondamental
    # (7ème, 8ème et 9ème année). Les autres cycles n'y ont pas droit.
    if niveau is None or niveau_ordre(niveau) not in _ORDRE_SECOND_CYCLE:
        raise HTTPException(
            status_code=403,
            detail="La fiche de suivi ne s'applique qu'aux élèves du second cycle du fondamental (7ème, 8ème et 9ème année).",
        )

    est_j = est_jardin(niveau)
    bareme = bareme_niveau(niveau)

    rang = None
    effectif = None
    transfert = False
    if classe and not est_j:
        rang, effectif = _rang_classe(db, insc.id_classe, annee.id, matricule, est_j)
        transfert = niveau_ordre(niveau) == 9

    moyenne_annuelle = None if est_j else calculer_moyenne_annuelle(db, matricule, annee.id)
    moyennes_trimestres = [] if est_j else calculer_moyennes_par_trimestre(db, matricule, annee.id)
    notes_par_matiere = [] if est_j else calculer_notes_par_matiere(db, matricule, annee.id)

    absences = (
        db.query(models.Absences)
        .filter(
            models.Absences.matricule_eleve == matricule,
            models.Absences.date_absence >= annee.date_debut,
            models.Absences.date_absence <= annee.date_fin,
        )
        .all()
    )
    nb_absences = len(absences)
    nb_justifiees = sum(1 for a in absences if a.justifiee)
    nb_injustifiees = nb_absences - nb_justifiees

    inscriptions = (
        db.query(models.Inscriptions)
        .options(
            joinedload(models.Inscriptions.classe),
            joinedload(models.Inscriptions.annee_scolaire),
        )
        .join(models.AnneesScolaires, models.Inscriptions.id_annee_scolaire == models.AnneesScolaires.id)
        .filter(models.Inscriptions.matricule_eleve == matricule)
        .order_by(models.AnneesScolaires.date_debut.asc())
        .all()
    )
    parcours = [
        schemas.ParcoursAnnee(
            annee_label=ins.annee_scolaire.libelle,
            classe=f"{ins.classe.niveau} {ins.classe.nom}" if ins.classe else None,
            niveau=ins.classe.niveau if ins.classe else None,
            statut_passage=ins.statut_passage,
            moyenne_annuelle=calculer_moyenne_annuelle(db, matricule, ins.id_annee_scolaire),
        )
        for ins in inscriptions
    ]

    colonnes, lignes, orientation, fois_x = _grille_suivi(db, matricule, inscriptions)

    return schemas.FicheSuiviResponse(
        matricule=eleve.matricule,
        nom=eleve.nom,
        prenom=eleve.prenom,
        date_de_naissance=eleve.date_de_naissance,
        lieu_de_naissance=eleve.lieu_de_naissance,
        sexe=eleve.sexe,
        adresse=eleve.adresse,
        pere=(f"{eleve.prenom_pere} {eleve.nom_pere}".strip() if eleve.prenom_pere or eleve.nom_pere else None),
        mere=(f"{eleve.prenom_mere} {eleve.nom_mere}".strip() if eleve.prenom_mere or eleve.nom_mere else None),
        niveau=niveau,
        classe=f"{classe.niveau} {classe.nom}" if classe else None,
        bareme=bareme,
        est_jardin=est_j,
        transfert=transfert,
        annee_label=annee.libelle,
        moyenne_annuelle=moyenne_annuelle,
        rang=rang,
        effectif=effectif,
        moyennes_trimestres=moyennes_trimestres,
        notes_par_matiere=notes_par_matiere,
        colonnes=colonnes,
        lignes=lignes,
        orientation=orientation,
        remarques=_REMARQUES_FICHE,
        fois_x=fois_x,
        nb_absences=nb_absences,
        nb_absences_justifiees=nb_justifiees,
        nb_absences_injustifiees=nb_injustifiees,
        parcours=parcours,
    )


# ─── Rapport des moyennes annuelles ────────────────────────────────────────────


def _classes_annee(db: Session, classe_id: Optional[int], id_annee: int, exclure_jardin: bool = False):
    requete = db.query(models.Classes)
    if classe_id is not None:
        requete = requete.filter(models.Classes.id == classe_id)
    classes = requete.order_by(models.Classes.id.asc()).all()
    if exclure_jardin:
        classes = [c for c in classes if not est_jardin(c.niveau)]
    return classes


def _exiger_classe_notable(db: Session, classe_id: Optional[int]) -> None:
    """Rejette une demande ciblée sur une classe du jardin d'enfants :
    ces classes n'ont pas de notes chiffrées, donc ni moyennes ni passage."""
    if classe_id is None:
        return
    classe = db.query(models.Classes).filter(models.Classes.id == classe_id).first()
    if classe is None:
        raise HTTPException(status_code=404, detail="Classe introuvable")
    if est_jardin(classe.niveau):
        raise HTTPException(
            status_code=400,
            detail="Le jardin d'enfants n'utilise pas de notes chiffrées : ce rapport ne s'applique qu'aux classes du fondamental.",
        )


@router.get("/moyennes-annuelles", response_model=schemas.RapportMoyennesResponse)
def moyennes_annuelles(
    classe_id: Optional[int] = None,
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    annee = _annee(db, annee_id)
    _exiger_classe_notable(db, classe_id)
    classes_out: List[schemas.ClasseMoyennes] = []
    for classe in _classes_annee(db, classe_id, annee.id, exclure_jardin=True):
        inscriptions = (
            db.query(models.Inscriptions)
            .options(joinedload(models.Inscriptions.eleve))
            .filter(
                models.Inscriptions.id_classe == classe.id,
                models.Inscriptions.id_annee_scolaire == annee.id,
            )
            .all()
        )
        if not inscriptions and classe_id is None:
            continue
        eleves_out: List[schemas.EleveMoyenne] = []
        moyennes: list[float] = []
        est_j = est_jardin(classe.niveau)
        for insc in inscriptions:
            el = insc.eleve
            if not el:
                continue
            m = None if est_j else calculer_moyenne_annuelle(db, el.matricule, annee.id)
            if m is not None:
                moyennes.append(m)
            eleves_out.append(
                schemas.EleveMoyenne(
                    inscription_id=insc.id,
                    matricule=el.matricule,
                    nom=el.nom,
                    prenom=el.prenom,
                    moyenne_annuelle=m,
                    rang=None,
                    statut_passage=insc.statut_passage,
                )
            )
        avec_moyenne = sorted(
            (e for e in eleves_out if e.moyenne_annuelle is not None),
            key=lambda e: (-e.moyenne_annuelle, e.matricule),
        )
        for index, e in enumerate(avec_moyenne, start=1):
            e.rang = index
        eleves_out = avec_moyenne + [e for e in eleves_out if e.moyenne_annuelle is None]
        moyenne_classe = round(sum(moyennes) / len(moyennes), 2) if moyennes else None
        classes_out.append(
            schemas.ClasseMoyennes(
                id_classe=classe.id,
                niveau=classe.niveau,
                nom=classe.nom,
                bareme=bareme_niveau(classe.niveau),
                effectif=len(inscriptions),
                moyenne_classe=moyenne_classe,
                eleves=eleves_out,
            )
        )
    return schemas.RapportMoyennesResponse(annee_label=annee.libelle, classes=classes_out)


@router.get("/moyennes-annuelles/pdf")
def moyennes_annuelles_pdf(
    classe_id: Optional[int] = None,
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    rapport = moyennes_annuelles(classe_id, annee_id, db)
    contenu = pdf_service.moyennes_pdf(rapport, _etablissement(db), rapport.annee_label)
    return Response(
        content=contenu,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{_nom_fichier("Rapport_moyennes_annuelles", "classe", str(classe_id or "toutes"), "")}"'
            )
        },
    )


# ─── Proposition de passage ────────────────────────────────────────────────────


@router.get("/proposition-passage", response_model=schemas.PropositionPassageResponse)
def proposition_passage(
    classe_id: Optional[int] = None,
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    annee = _annee(db, annee_id)
    _exiger_classe_notable(db, classe_id)
    classes_out: List[schemas.ClasseProposition] = []
    classes = _classes_annee(db, classe_id, annee.id, exclure_jardin=True)
    for classe in classes:
        inscriptions = (
            db.query(models.Inscriptions)
            .options(joinedload(models.Inscriptions.eleve))
            .filter(
                models.Inscriptions.id_classe == classe.id,
                models.Inscriptions.id_annee_scolaire == annee.id,
            )
            .all()
        )
        if not inscriptions and classe_id is None:
            continue
        est_j = est_jardin(classe.niveau)
        bareme = bareme_niveau(classe.niveau)
        seuil = seuil_passage(bareme)
        n_ordre = niveau_ordre(classe.niveau)
        est_fin = n_ordre == 9

        eleves_out: List[schemas.EleveProposition] = []
        admis = recales = en_attente = exclus = 0
        for insc in inscriptions:
            el = insc.eleve
            if not el:
                continue
            statistique = insc.statut_passage
            m = None if est_j else calculer_moyenne_annuelle(db, el.matricule, annee.id)
            if est_j or (m is None and statistique == "EN_ATTENTE"):
                proposition = "EN_ATTENTE"
            elif statistique == "EXCLU":
                proposition = "EXCLU"
            elif statistique in {"ADMIS", "RECALE"}:
                proposition = statistique
            else:
                proposition = "ADMIS" if m is not None and m >= seuil else "RECALE"

            if proposition == "ADMIS":
                admis += 1
            elif proposition == "RECALE":
                recales += 1
            elif proposition == "EXCLU":
                exclus += 1
            else:
                en_attente += 1

            eleves_out.append(
                schemas.EleveProposition(
                    inscription_id=insc.id,
                    matricule=el.matricule,
                    nom=el.nom,
                    prenom=el.prenom,
                    moyenne_annuelle=m,
                    statut_actuel=statistique,
                    proposition=proposition,
                )
            )
        avec_moy = sorted(
            (e for e in eleves_out if e.moyenne_annuelle is not None),
            key=lambda e: (-e.moyenne_annuelle, e.matricule),
        )
        eleves_out = avec_moy + [e for e in eleves_out if e.moyenne_annuelle is None]
        classes_out.append(
            schemas.ClasseProposition(
                id_classe=classe.id,
                niveau=classe.niveau,
                nom=classe.nom,
                bareme=bareme,
                seuil=seuil,
                est_fin_cycle=est_fin,
                effectif=len(inscriptions),
                admis=admis,
                recales=recales,
                en_attente=en_attente,
                exclus=exclus,
                eleves=eleves_out,
            )
        )
    return schemas.PropositionPassageResponse(annee_label=annee.libelle, classes=classes_out)


# ─── Rapport succinct de rentrée (doc5) ───────────────────────────────────────

@router.get("/rentree", response_model=schemas.RapportRentreeResponse)
def rapport_rentree(
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    annee = _annee(db, annee_id)
    return effectifs_service.rapport_rentree(db, annee, _etablissement(db))


# ─── Classement des élèves (doc1) ──────────────────────────────────────────────

_CLASSEMENT_OBS = {
    "ADMIS": "Admis",
    "RECALE": "Recalé(e)",
    "EN_ATTENTE": "En attente",
    "EXCLU": "Exclu",
}


def _rapport_classement(db: Session, classe_id: Optional[int], annee_id: Optional[int]) -> schemas.ClassementResponse:
    """Recyclage des moyennes annuelles : même calcul, présenté comme classement."""
    rapport = moyennes_annuelles(classe_id, annee_id, db)
    classes_out = [
        schemas.ClassementClasseResponse(
            id_classe=c.id_classe,
            niveau=c.niveau,
            nom=c.nom,
            bareme=c.bareme,
            effectif=c.effectif,
            moyenne_classe=c.moyenne_classe,
            eleves=[
                schemas.ClassementEleve(
                    inscription_id=e.inscription_id,
                    matricule=e.matricule,
                    nom=e.nom,
                    prenom=e.prenom,
                    moyenne_annuelle=e.moyenne_annuelle,
                    rang=e.rang,
                    observation=_CLASSEMENT_OBS.get(e.statut_passage),
                )
                for e in c.eleves
            ],
        )
        for c in rapport.classes
    ]
    return schemas.ClassementResponse(annee_label=rapport.annee_label, classes=classes_out)


@router.get("/classement", response_model=schemas.ClassementResponse)
def classement(
    classe_id: Optional[int] = None,
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return _rapport_classement(db, classe_id, annee_id)


# ─── Fiche de renseignements de rentrée, 2nd cycle (doc6) ─────────────────────

@router.get("/fiche-renseignements", response_model=schemas.FicheRenseignementsResponse)
def fiche_renseignements(
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    annee = _annee(db, annee_id)
    return effectifs_service.fiche_renseignements(db, annee, _etablissement(db))


# ─── Fiche de renseignements de rentrée, 1er cycle (doc5) ─────────────────────

@router.get("/fiche-renseignements-premier-cycle", response_model=schemas.FicheRenseignementsPremierCycleResponse)
def fiche_renseignements_premier_cycle(
    annee_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    annee = _annee(db, annee_id)
    return effectifs_service.fiche_renseignements_premier_cycle(db, annee, _etablissement(db))


# ─── Fiche de notes mensuelle / de composition, élève (doc7 + doc3) ───────────

@router.get("/eleves/{matricule}/fiche-notes-compositions", response_model=schemas.FicheNotesCompoResponse)
def fiche_notes_compositions(
    matricule: str,
    annee_id: Optional[int] = None,
    trimestre_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    annee = _annee(db, annee_id)
    eleve = _get_eleve(db, matricule)
    insc = _inscription(db, matricule, annee.id)
    if not insc:
        raise HTTPException(status_code=404, detail="Aucune inscription pour cette année scolaire")
    try:
        return effectifs_service.fiche_notes_compositions(db, matricule, annee, eleve, insc, trimestre_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/eleves/{matricule}/fiche-notes-compositions/pdf")
def fiche_notes_compositions_pdf(
    matricule: str,
    annee_id: Optional[int] = None,
    trimestre_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    annee = _annee(db, annee_id)
    eleve = _get_eleve(db, matricule)
    insc = _inscription(db, matricule, annee.id)
    if not insc:
        raise HTTPException(status_code=404, detail="Aucune inscription pour cette année scolaire")
    try:
        fiche = effectifs_service.fiche_notes_compositions(db, matricule, annee, eleve, insc, trimestre_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    contenu = pdf_service.fiche_notes_compo_pdf(fiche, _etablissement(db), fiche.annee_label)
    return Response(
        content=contenu,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{_nom_fichier("Fiche_de_notes_compositions", matricule, eleve.nom, eleve.prenom)}"',
        },
    )