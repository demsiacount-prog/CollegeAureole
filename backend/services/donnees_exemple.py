"""Peuplement de données d'exemple réalistes après l'initialisation.

Génère une école malienne crédible (primaire EF1 + collège EF2) :
- familles bamakoises (fratries partageant tuteur, nom et adresse), noms et
  prénoms maliens, quartiers de Bamako, téléphones +223, e-mails plausibles ;
- classes « Xème Année — A/B », maîtres polyvalents en EF1, professeurs
  spécialisés par matière en EF2, salles des blocs primaire/collège ;
- notes réalistes (niveau d'aptitude par élève, dispersion par matière,
  barème /10 en EF1 et /20 en EF2), bulletins conformes à la règle métier
  (moyenne simple en EF1, pondérée par coefficients en EF2) ;
- absences motivées de façon vraisemblable, paiements échelonnés via Orange
  Money / Moov Money / Wave / espèces…, dépenses courantes d'une école.

Ne touche ni au schéma, ni à la fiche établissement, ni à l'année scolaire,
ni aux périodes, ni au compte administrateur créés par l'assistant.
Toute la génération est déterministe (graine fixe) afin que les tests e2e —
notamment l'élève EL2500001, toujours scolarisé en « 1ère Année — A » avec un
historique d'absences garanti — restent stables d'une exécution à l'autre.
"""
import logging
import random
import unicodedata
from datetime import date, time, timedelta

from sqlalchemy import func as _func

from database import SessionLocal
from hashing import hash_password
from enums import RoleUtilisateur
import models
from models.bulletins import BulletinDetails
from models.associations import AffectationCoursClasse
from bareme import bareme_niveau, appreciation_for_moyenne

logger = logging.getLogger("college_aureole")

MOT_DE_PASSE_DEMO = "Password123!"

# ── Graine de déterminisme ───────────────────────────────────────────────────
GRAINE = 20252026

# ── Système scolaire malien ──────────────────────────────────────────────────
ANNEES = [
    "1ère Année", "2ème Année", "3ème Année",
    "4ème Année", "5ème Année", "6ème Année",
    "7ème Année", "8ème Année", "9ème Année",
]
EF1 = ANNEES[:6]
EF2 = ANNEES[6:]
DIVISIONS = ["A", "B"]

# Effectif cible (~29 élèves/classe sur 18 classes).
NB_ELEVES = 520

MATIERES_EF1 = [
    ("Lecture / Écriture",                     "Apprentissage de la lecture, écriture et lecture à voix haute", 6),
    ("Mathématiques",                          "Calcul, numération, géométrie et mesures",                       6),
    ("Langue Nationale (Bambara)",             "Expression orale et écrite en bambara",                          3),
    ("Sciences et Éveil au Milieu",            "Découverte du milieu naturel, santé et environnement",           3),
    ("Histoire-Géographie",                    "Initiation à l'histoire du Mali et aux milieux de vie",          2),
    ("Éducation Civique et Morale",            "Vivre ensemble, droits et devoirs du citoyen",                   2),
    ("Éducation Physique et Sportive",         "Motricité, jeux collectifs et hygiène",                          2),
    ("Arts Plastiques et Travaux Manuels",     "Dessin, modelage et travaux manuels",                            2),
]

MATIERES_EF2 = [
    ("Français",                        "Grammaire, conjugaison, expression écrite et littérature",   5),
    ("Mathématiques",                   "Algèbre, géométrie, statistiques et probabilités",           5),
    ("Anglais",                         "Expression écrite et orale en anglais",                      3),
    ("SVT",                             "Sciences de la Vie et de la Terre",                          3),
    ("Physique-Chimie",                 "Mécanique, électricité et chimie",                           3),
    ("Histoire-Géographie",             "Histoire du Mali, de l'Afrique et géographie mondiale",      3),
    ("Éducation Civique et Morale",     "Droits, devoirs, citoyenneté et valeurs",                    2),
    ("Éducation Physique et Sportive",  "Sport, athlétisme et hygiène de vie",                        2),
    ("Informatique",                    "Initiation aux outils numériques et bureautique",            2),
]

# Ajustement de difficulté par matière (sur base /20, ramené au barème).
AJUSTEMENT_MATIERE = {
    "Mathématiques": -0.9, "Physique-Chimie": -0.6, "Anglais": -0.5,
    "Français": -0.4, "SVT": -0.2, "Lecture": 0.6, "Informatique": 0.8,
    "Éducation Civique": 0.9, "Éducation Physique": 1.4,
    "Arts Plastiques": 1.2, "Langue Nationale": 0.5, "Expression": 0.3,
    "Sciences et Éveil": 0.2,
}

# Frais de scolarité réalistes (école privée de Bamako, FCFA).
FRAIS_PAR_NIVEAU = {
    # niveau: (frais d'inscription, mensualité)
    "1ère Année": (8_000, 12_000),
    "2ème Année": (8_000, 12_000),
    "3ème Année": (9_000, 13_000),
    "4ème Année": (9_000, 13_000),
    "5ème Année": (10_000, 14_000),
    "6ème Année": (10_000, 14_000),
    "7ème Année": (15_000, 17_500),
    "8ème Année": (15_000, 17_500),
    "9ème Année": (20_000, 20_000),  # année d'examen (BEPC)
}

MODES_PAIEMENT = ["Espèces", "Orange Money", "Moov Money", "Wave", "Chèque", "Virement bancaire"]
PROBA_MODES = [45, 25, 10, 12, 5, 3]

# ── Données démographiques maliennes ────────────────────────────────────────
NOMS_FAMILLE = [
    "Coulibaly", "Diarra", "Traoré", "Keïta", "Diallo", "Sissoko", "Cissé",
    "Touré", "Konaté", "Kanté", "Sidibé", "Maïga", "Fofana", "Dembélé",
    "Doumbia", "Ouattara", "Koné", "Bagayoko", "Haïdara", "Sangaré", "Samaké",
    "Togola", "Diawara", "Sylla", "Camara", "Tembely", "Guindo", "Kassambara",
    "Sacko", "Sanogo", "Dicko", "Sow", "Barry", "Bah", "Thiam", "N'Diaye",
    "Fall", "Sy", "Sakho", "Dansokho", "Attaher", "Ag Ahmed", "Hamey",
    "Tandina", "Oumarou", "Niangado", "Fané", "Daou", "Crépin", "Tembiné",
    "Poudiougou", "Djiré", "Kida", "Couloubaly", "Sissao", "Gaoussou",
]

PRENOMS_M = [
    "Amadou", "Mamadou", "Moussa", "Adama", "Boubacar", "Ibrahima", "Ousmane",
    "Souleymane", "Seydou", "Boukary", "Salif", "Modibo", "Mahamadou", "Cheick",
    "Cheickna", "Bakary", "Drissa", "Tiécoura", "Fousseyni", "Fousseni",
    "Karim", "Youssouf", "Lassana", "Sékou", "Issa", "Abdoulaye", "Malick",
    "Nouhoum", "Bourama", "Yacouba", "Aliou", "Hamidou", "Samba", "Demba",
    "Makan", "Aboubacar", "Sidiki", "Oumar", "Bassidi", "Mahamane", "Alou",
    "Mamoutou", "Soungalo", "Ballaké",
]

PRENOMS_F = [
    "Fatoumata", "Aïssata", "Mariam", "Awa", "Kadiatou", "Bintou", "Fanta",
    "Djeneba", "Assitan", "Oumou", "Rokia", "Maïmouna", "Hawa", "Safiatou",
    "Ramatoulaye", "Kadidia", "Salimata", "Coumba", "Asseta", "Sira", "Tenin",
    "Diora", "Sanata", "Kani", "Sitan", "Aminata", "Aïcha", "Zeinab",
    "Mariama", "Fatimata", "Founé", "Tabara", "Khady", "Dieynabou", "Nana",
    "Korotoumou", "Massitan", "Siramane",
]

LIEUX_NAISSANCE = (
    ["Bamako"] * 8
    + [
        "Sikasso", "Ségou", "Mopti", "Kayes", "Koulikoro", "Koutiala",
        "Bougouni", "Kati", "Dioïla", "Bla", "San", "Djenné", "Bandiagara",
        "Douentza", "Goundam", "Diré", "Tombouctou", "Gao", "Ansongo",
        "Nioro du Sahel", "Kita", "Yélimané", "Markala", "Ouéléssébougou",
        "Kangaba", "Kolokani", "Banamba", "Nara",
        "Abidjan", "Ouagadougou", "Conakry", "Niamey", "Dakar",
    ]
)

QUARTIERS_BAMAKO = [
    "Badalabougou", "Hamdallaye ACI 2000", "Quartier du Fleuve", "Sogoniko",
    "Magnambougou", "Faladié", "Yirimadio", "Banankabougou", "Niamakoro",
    "Sotuba", "Sébénikoro", "Kabala", "N'Tomikorobougou", "Torokorobougou",
    "Sabalibougou", "Djélibougou", "Lafiabougou", "Hippodrome", "Point G",
    "Bolibana", "Bagadadji", "Médina Coura", "Quinzambougou", "Niaréla",
    "Korofina Nord", "Baco Djicoroni", "Garantiguibougou", "Sikoro Soroba",
    "Kalaban Coura", "Kalaban Grosso", "Daoudabougou", "Missira",
    "Boulkassoumbougou", "Dougouolo", "Banconi", "Djicoroni Para", "Lassa",
]

PROFESSIONS_TUTEURS = [
    "Commerçant(e)", "Cultivateur", "Maraîcher", "Éleveur", "Pêcheur",
    "Boutiquier(ère)", "Vendeuse au marché", "Tailleur", "Couturière",
    "Teinturière", "Coiffeuse", "Mécanicien", "Soudeur", "Menuisier",
    "Maçon", "Plombier", "Électricien", "Forgeron", "Cordonnier", "Chauffeur",
    "Taximan", "Motorisé (taxi-moto)", "Transporteur", "Fonctionnaire",
    "Enseignant(e)", "Infirmier(ère)", "Sage-femme", "Médecin", "Pharmacien(ne)",
    "Comptable", "Secrétaire", "Gestionnaire", "Juriste", "Ingénieur",
    "Informaticien(ne)", "Militaire", "Agent de sécurité", "Douanier",
    "Ménagère", "Restauratrice", "Boulanger", "Boucher", "Photographe",
    "Imprimeur", "Retraité(e)", "Sans emploi stable",
]

MOTIFS_ABSENCE_JUSTIFIEE = [
    "Maladie", "Rendez-vous médical", "Décès dans la famille",
    "Mariage ou baptême familial", "Pluies : route impraticable",
    "Voyage familial", "Travaux champêtres",
]
PROBA_ABSENCE_JUSTIFIEE = 0.55

DOMAINES_EMAIL = ["gmail.com", "yahoo.fr", "hotmail.fr", "outlook.com"]
POIDS_DOMAINES = [55, 22, 13, 10]

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
CRENEAUX_HORAIRES = [
    (time(8, 0), time(10, 0)),
    (time(10, 15), time(12, 15)),
    (time(14, 0), time(16, 0)),
    (time(16, 15), time(18, 15)),
]

COMPTE_DIRECTEUR = "directeur"
COMPTE_COMPTABLE = "comptable"


# ── Petits utilitaires déterministes ────────────────────────────────────────

def _sans_accents(texte: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _slug(texte: str) -> str:
    return "".join(c for c in _sans_accents(texte).lower() if c.isalnum())


def _date_entre(rng: random.Random, debut: date, fin: date) -> date:
    if fin <= debut:
        return debut
    return debut + timedelta(days=rng.randint(0, (fin - debut).days))


def _telephone(rng: random.Random) -> str:
    prefixe = rng.choice(["76", "77", "70", "78", "79", "65", "66", "68", "91", "92", "94", "95", "96"])
    return f"+223 {prefixe} {rng.randint(10, 99):02d} {rng.randint(10, 99):02d} {rng.randint(10, 99):02d}"


def _email(rng: random.Random, prenom: str, nom: str, utilises: set[str]) -> str:
    base = f"{_slug(prenom)}.{_slug(nom)}"
    domaine = rng.choices(DOMAINES_EMAIL, weights=POIDS_DOMAINES, k=1)[0]
    adresse = f"{base}@{domaine}"
    n = 2
    while adresse in utilises:
        adresse = f"{base}{n}@{domaine}"
        n += 1
    utilises.add(adresse)
    return adresse


def _adresse_bamako(rng: random.Random) -> str:
    quartier = rng.choice(QUARTIERS_BAMAKO)
    if rng.random() < 0.7:
        return f"Rue {rng.randint(1, 900)}, {quartier}, Bamako"
    return f"{quartier}, Bamako"


def _comptes_demo(email_admin: str):
    """Directeur + comptable de démonstration sur le domaine de l'e-mail admin."""
    domaine = email_admin.split("@")[-1] if "@" in email_admin else "etablissement.com"
    return [
        ("Traoré", "Directeur", f"{COMPTE_DIRECTEUR}@{domaine}", RoleUtilisateur.DIRECTEUR),
        ("Koné", "Comptable", f"{COMPTE_COMPTABLE}@{domaine}", RoleUtilisateur.COMPTABLE),
    ]


def _mettre_a_jour_statut_echeance(ech):
    if ech.montant_paye <= 0:
        ech.statut = "EN_ATTENTE"
    elif ech.montant_paye >= ech.montant_du:
        ech.statut = "SOLDE"
    else:
        ech.statut = "PARTIEL"


def _generer_echeances(db, inscription, annee_debut):
    from models.echeances import MOIS_ANNEE_SCOLAIRE
    classe = db.query(models.Classes).filter(models.Classes.id == inscription.id_classe).first()
    frais_insc = getattr(classe, "frais_inscription", 0.0) or 0.0
    mensualite = getattr(classe, "mensualite", 0.0) or 0.0
    annee_int = annee_debut.year

    db.add(models.Echeances(
        id_inscription=inscription.id, id_classe=inscription.id_classe,
        type_echeance="INSCRIPTION", mois=None,
        date_echeance=inscription.date_inscription,
        montant_du=frais_insc, montant_paye=0.0,
        statut="EN_ATTENTE" if frais_insc > 0 else "SOLDE",
    ))

    for i, mois in enumerate(MOIS_ANNEE_SCOLAIRE):
        if i < 3:
            annee_m, num_m = annee_int, 10 + i
        else:
            annee_m, num_m = annee_int + 1, i - 2
        db.add(models.Echeances(
            id_inscription=inscription.id, id_classe=inscription.id_classe,
            type_echeance="MENSUALITE", mois=mois,
            date_echeance=date(annee_m, num_m, 5),
            montant_du=mensualite, montant_paye=0.0,
            statut="EN_ATTENTE" if mensualite > 0 else "SOLDE",
        ))

    inscription.montant_total = frais_insc + (mensualite * 9)
    db.flush()


def generer_paiements(db, inscription, annee_debut, annee_fin, rng):
    """Versements réalistes : paiement comptant, échelonné, partiel ou nul."""
    montant_du = inscription.montant_total
    profil = rng.choices(
        ["solde_complet", "echelonne", "partiel", "aucun"],
        weights=[35, 40, 15, 10], k=1,
    )[0]

    if profil == "aucun":
        return 0, 0.0
    elif profil == "solde_complet":
        versements = [montant_du]
    elif profil == "echelonne":
        nb_v = rng.choice([2, 3])
        parts = sorted(rng.sample(range(1, 100), nb_v - 1))
        parts = [0] + parts + [100]
        versements = [
            round(montant_du * (parts[k + 1] - parts[k]) / 100, 0)
            for k in range(nb_v)
        ]
    else:
        nb_v = rng.choice([1, 2])
        fraction = rng.uniform(0.2, 0.7)
        montant_paye = round(montant_du * fraction, 0)
        versements = [montant_paye] if nb_v == 1 else [
            round(montant_paye * rng.uniform(0.4, 0.6), 0),
            montant_paye - round(montant_paye * rng.uniform(0.4, 0.6), 0),
        ]

    date_courante = annee_debut
    total_paiements = 0
    total_montant = 0.0

    for montant_v in versements:
        if montant_v <= 0:
            continue
        date_courante = _date_entre(rng, date_courante, min(date.today(), annee_fin))
        echeances_impayees = (
            db.query(models.Echeances)
            .filter(
                models.Echeances.id_inscription == inscription.id,
                models.Echeances.statut.in_(["EN_ATTENTE", "PARTIEL"]),
            )
            .order_by(models.Echeances.date_echeance.asc())
            .all()
        )
        reste = float(montant_v)
        for ech in echeances_impayees:
            if reste <= 0:
                break
            a_payer = max(ech.montant_du - ech.montant_paye, 0.0)
            if a_payer <= 0:
                continue  # échéance déjà soldée : pas de paiement à 0
            sur_ech = min(reste, a_payer)
            db.add(models.Paiements(
                id_inscription=inscription.id, id_echeance=ech.id,
                date=date_courante,
                montant=sur_ech,
                mode=rng.choices(MODES_PAIEMENT, weights=PROBA_MODES, k=1)[0],
                observation=None,
            ))
            ech.montant_paye += sur_ech
            _mettre_a_jour_statut_echeance(ech)
            reste -= sur_ech
        total_paiements += 1
        total_montant += float(montant_v)

    return total_paiements, total_montant


def generer_planning_evaluations(cours_list, periodes, rng):
    planning = {}
    for co in cours_list:
        for nom, date_debut, date_fin, trim_obj in periodes:
            planning[(co.id, trim_obj.id)] = _date_entre(rng, date_debut, date_fin)
    return planning


def _ajustement_matiere(nom_cours: str) -> float:
    for cle, ajust in AJUSTEMENT_MATIERE.items():
        if nom_cours.startswith(cle) or cle in nom_cours:
            return ajust
    return 0.0


def generer_notes_pour_eleve(db, eleve, id_classe_courante, cours_eleve, periodes, planning,
                             classe_niveau: str = "", aptitude: float = 0.0, rng=None):
    """Notes réalistes : niveau moyen de la classe ± aptitude de l'élève
    ± difficulté de la matière ± bruit de copie, borné au barème."""
    rng = rng or random.Random()
    total = 0
    bareme = bareme_niveau(classe_niveau)
    idx_niveau = ANNEES.index(classe_niveau) if classe_niveau in ANNEES else 0

    if bareme == 10:
        mu = 6.3 - 0.12 * idx_niveau          # 6.30 (1ère) → 5.66 (6ème) sur /10
        sigma_eleve, sigma_note = 1.2, 0.7
    else:
        mu = [11.2, 10.6, 9.9][min(idx_niveau - 6, 2)]  # 7ème → 9ème sur /20
        sigma_eleve, sigma_note = 2.6, 1.5

    for co in cours_eleve:
        ajust = _ajustement_matiere(co.nom) * (bareme / 20.0)
        for _, _, _, trim_obj in periodes:
            date_eval = planning.get((co.id, trim_obj.id))
            if date_eval is None:
                continue
            note = mu + aptitude * sigma_eleve + ajust + rng.gauss(0, sigma_note)
            note = max(0.0, min(float(bareme), round(note, 2)))
            db.add(models.Notes(
                date=date_eval,
                note=note,
                matricule_eleve=eleve.matricule,
                id_cours=co.id,
                id_classe=id_classe_courante,
                matricule_enseignant=co.matricule_enseignant,
                id_trimestre=trim_obj.id,
            ))
            total += 1
    return total


def generer_bulletins_pour_classe(db, classe, eleves_classe, cours_list, periodes):
    total = 0
    bareme = bareme_niveau(classe.niveau)
    coef_map = {
        (c.id, a.id_classe): a.coefficient
        for c in cours_list
        for a in c.classes_affectations
    }

    for _, _, _, trimestre_obj in periodes:
        bulletins_classe = []
        details_par_bulletin = {}
        moyennes_par_eleve: dict[str, list] = {}
        for mat, id_cours, moyenne in (
            db.query(
                models.Notes.matricule_eleve,
                models.Notes.id_cours,
                _func.avg(models.Notes.note),
            )
            .filter(
                models.Notes.id_classe == classe.id,
                models.Notes.id_trimestre == trimestre_obj.id,
            )
            .group_by(models.Notes.matricule_eleve, models.Notes.id_cours)
            .all()
        ):
            moyennes_par_eleve.setdefault(mat, []).append((id_cours, float(moyenne)))

        existants = {
            m for (m,) in db.query(models.Bulletins.matricule_eleve).filter(
                models.Bulletins.id_classe == classe.id,
                models.Bulletins.id_trimestre == trimestre_obj.id,
            ).all()
        }

        for eleve in eleves_classe:
            moyennes_par_cours = moyennes_par_eleve.get(eleve.matricule, [])
            if not moyennes_par_cours:
                continue
            if eleve.matricule in existants:
                continue

            # EF1 (barème /10) : moyenne simple, aucun coefficient.
            est_ef1 = bareme == 10
            total_pondere, total_coef = 0.0, 0
            total_simple, nb_matieres = 0.0, 0
            details = []
            for id_cours, moyenne in moyennes_par_cours:
                coef = 1.0 if est_ef1 else coef_map.get((id_cours, classe.id), 1.0)
                total_pondere += float(moyenne) * coef
                total_coef += coef
                total_simple += float(moyenne)
                nb_matieres += 1
                details.append((id_cours, round(float(moyenne), 2), coef))

            if total_coef == 0:
                continue

            moyenne_generale = (
                round(total_simple / nb_matieres, 2) if est_ef1
                else round(total_pondere / total_coef, 2)
            )
            appreciation = appreciation_for_moyenne(moyenne_generale, bareme)

            bulletin = models.Bulletins(
                matricule_eleve=eleve.matricule, id_trimestre=trimestre_obj.id,
                id_classe=classe.id, moyenne_generale=moyenne_generale,
                appreciation=appreciation,
            )
            db.add(bulletin)
            bulletins_classe.append(bulletin)
            details_par_bulletin[bulletin] = details
            total += 1

        db.flush()
        for bulletin in bulletins_classe:
            for id_cours, moyenne, coef in details_par_bulletin[bulletin]:
                db.add(BulletinDetails(
                    id_bulletin=bulletin.id, id_cours=id_cours,
                    moyenne=moyenne, coefficient=coef,
                ))

        bulletins_classe.sort(key=lambda b: b.moyenne_generale, reverse=True)
        for rang, bulletin in enumerate(bulletins_classe, start=1):
            bulletin.rang = rang
        db.commit()

    return total


def periodes_pour_niveau(classe_niveau: str, periodes_ef1, periodes_ef2):
    """EF1 → compositions, EF2 → trimestres (jamais les deux chez un même élève)."""
    return periodes_ef1 if classe_niveau in EF1 else periodes_ef2


def peupler(annee_id: int, annee_debut: date, annee_fin: date, email_admin: str) -> None:
    """Crée les données d'exemple attachées à l'année scolaire donnée."""
    rng = random.Random(GRAINE)
    emails_utilises: set[str] = set()
    db = SessionLocal()
    try:
        annee = db.query(models.AnneesScolaires).filter(models.AnneesScolaires.id == annee_id).first()
        if annee is None:
            raise ValueError(f"Année scolaire {annee_id} introuvable")
        # ── COMPTES DE DÉMONSTRATION ─────────────────────────────────────────
        for nom, prenom, email, role in _comptes_demo(email_admin):
            existe = db.query(models.Utilisateurs).filter(models.Utilisateurs.email == email).first()
            if not existe:
                db.add(models.Utilisateurs(
                    nom=nom, prenom=prenom, email=email,
                    mot_de_passe=hash_password(MOT_DE_PASSE_DEMO), role=role,
                ))
        db.commit()

        # ── PÉRIODES DE L'ANNÉE (créées par l'assistant) ────────────────────
        periodes_db = (
            db.query(models.Trimestres)
            .filter(models.Trimestres.annee_scolaire_id == annee.id)
            .order_by(models.Trimestres.date_debut.asc())
            .all()
        )
        periodes_ef1 = [(t.nom, t.date_debut, t.date_fin, t) for t in periodes_db if t.type == "COMPOSITION"]
        periodes_ef2 = [(t.nom, t.date_debut, t.date_fin, t) for t in periodes_db if t.type == "TRIMESTRE"]
        total_periodes = periodes_ef1 + periodes_ef2

        # ── CLASSES (A d'abord : ids 1-9 = « Xème Année — A ») ──────────────
        classes = []
        classes_par_niveau: dict[str, list] = {niveau: [] for niveau in ANNEES}
        for div in DIVISIONS:
            for niveau in ANNEES:
                frais_insc, mensualite = FRAIS_PAR_NIVEAU[niveau]
                classe = models.Classes(
                    niveau=niveau, nom=div,
                    frais_inscription=float(frais_insc),
                    mensualite=float(mensualite),
                )
                db.add(classe)
                db.flush()
                classes.append(classe)
                classes_par_niveau[niveau].append(classe)
        db.commit()

        # ── TUTEURS (une famille = un tuteur, un nom, une adresse) ──────────
        tailles_familles = []
        effectif_vise = 0
        while effectif_vise < NB_ELEVES:
            taille = rng.choices([1, 2, 3, 4, 5], weights=[28, 34, 22, 11, 5], k=1)[0]
            tailles_familles.append(taille)
            effectif_vise += taille
        while sum(tailles_familles) > NB_ELEVES and min(tailles_familles) < sum(tailles_familles) - NB_ELEVES + 1:
            # Retire les excédents en réduisant d'abord les plus grandes familles.
            tailles_familles[tailles_familles.index(max(tailles_familles))] -= 1

        tuteurs = []
        for _ in range(len(tailles_familles)):
            nom_tuteur = rng.choice(NOMS_FAMILLE)
            sexe_tuteur = rng.random() < 0.3
            prenom = rng.choice(PRENOMS_F if sexe_tuteur else PRENOMS_M)
            t = models.Tuteurs(
                nom=nom_tuteur, prenom=prenom,
                email=_email(rng, prenom, nom_tuteur, emails_utilises),
                telephone=_telephone(rng),
                adresse=_adresse_bamako(rng),
                profession=rng.choice(PROFESSIONS_TUTEURS),
            )
            db.add(t)
            db.flush()
            tuteurs.append(t)
        db.commit()

        # ── ENSEIGNANTS ─────────────────────────────────────────────────────
        nb_maitres = len(EF1) * len(DIVISIONS)
        nb_profs = len(MATIERES_EF2)
        enseignants = []
        for i in range(nb_maitres + nb_profs):
            if i < nb_maitres:
                specialite = "Maître d'école (EF1 — polyvalent)"
            else:
                specialite = f"Professeur de {MATIERES_EF2[i - nb_maitres][0]}"
            prenom = rng.choice(PRENOMS_M)
            nom = rng.choice(NOMS_FAMILLE)
            e = models.Enseignants(
                nom=nom, prenom=prenom,
                email=_email(rng, prenom, nom, emails_utilises),
                telephone=_telephone(rng),
                adresse=_adresse_bamako(rng),
                specialite=specialite,
            )
            db.add(e)
            db.flush()
            enseignants.append(e)
        db.commit()

        maitres_ef1 = enseignants[:nb_maitres]
        profs_ef2 = enseignants[nb_maitres:]

        # ── COURS ───────────────────────────────────────────────────────────
        cours_list = []

        def creer_cours(nom, desc, vh, matr_ens, niveau, classes_cibles=None):
            c = models.Cours(
                nom=nom, description=desc,
                volume_horaire=vh * 30,
                matricule_enseignant=matr_ens,
            )
            db.add(c)
            db.flush()
            # EF1 : les coefficients ne s'appliquent pas (notes /10, moyenne
            # simple) → coefficient 1. EF2 : coefficient = volume horaire.
            coef = 1.0 if niveau in EF1 else float(vh)
            for classe_aff in (classes_cibles if classes_cibles is not None else classes_par_niveau[niveau]):
                db.add(AffectationCoursClasse(
                    id_classe=classe_aff.id, id_cours=c.id,
                    coefficient=coef,
                ))
            db.flush()
            return c

        # EF1 : un maître polyvalent par classe ; chaque matière donne lieu à
        # un cours propre à la section confiée à ce maître. La section A garde
        # le nom canonique « Matière — Niveau », la B est suffixée.
        for nom_m, desc_m, vh in MATIERES_EF1:
            for j, niveau in enumerate(EF1):
                for d, div in enumerate(DIVISIONS):
                    maitre = maitres_ef1[j * len(DIVISIONS) + d]
                    suffixe = "" if d == 0 else f" ({div})"
                    cours_list.append(creer_cours(
                        f"{nom_m} — {niveau}{suffixe}", desc_m, vh,
                        maitre.matricule, niveau,
                        classes_cibles=classes_par_niveau[niveau][d:d + 1],
                    ))

        # EF2 : un professeur spécialisé par matière, commun aux deux sections.
        for i, (nom_m, desc_m, vh) in enumerate(MATIERES_EF2):
            prof = profs_ef2[i % len(profs_ef2)]
            for niveau in EF2:
                cours_list.append(creer_cours(
                    f"{nom_m} — {niveau}", desc_m, vh, prof.matricule, niveau,
                ))
        db.commit()

        # ── SALLES (blocs primaire P / collège C + salles communes) ─────────
        salles = []
        salle_par_classe = {}
        for idx_c, classe in enumerate(classes):
            bloc = "P" if classe.niveau in EF1 else "C"
            numero = ANNEES.index(classe.niveau) + 1
            salle = models.Salles(
                nom=f"Salle {bloc}-{numero}{classe.nom}",
                capacite=rng.randint(38, 48) if bloc == "P" else rng.randint(32, 42),
            )
            db.add(salle)
            db.flush()
            salles.append(salle)
            salle_par_classe[classe.id] = salle
        for nom_salle, capacite in [("Salle informatique", 25), ("Bibliothèque", 30), ("Laboratoire SVT-Physique", 24)]:
            salle = models.Salles(nom=nom_salle, capacite=capacite)
            db.add(salle)
            db.flush()
            salles.append(salle)
        db.commit()

        # Carte classe → cours (évite les lazy-loads en cascade dans les boucles)
        cours_par_id = {c.id: c for c in cours_list}
        cours_par_classe_map: dict[int, list] = {}
        for aff in db.query(AffectationCoursClasse).all():
            co = cours_par_id.get(aff.id_cours)
            if co is not None:
                cours_par_classe_map.setdefault(aff.id_classe, []).append(co)

        # ── SÉANCES ─────────────────────────────────────────────────────────
        for classe in classes:
            salle_classe = salle_par_classe[classe.id]
            cours_de_la_classe = cours_par_classe_map.get(classe.id, [])
            idx_cours = 0
            for jour in JOURS_SEMAINE:
                for debut, fin in CRENEAUX_HORAIRES:
                    if idx_cours >= len(cours_de_la_classe):
                        break
                    co = cours_de_la_classe[idx_cours]
                    db.add(models.Seances(
                        id_cours=co.id, id_classe=classe.id,
                        id_annee_scolaire=annee.id,
                        id_salle=salle_classe.id,
                        jour_semaine=jour, heure_debut=debut, heure_fin=fin,
                    ))
                    idx_cours += 1
            db.commit()

        # ── ÉLÈVES & INSCRIPTIONS (fratries regroupées par famille) ─────────
        eleves = []
        inscriptions = []

        classe_pool = (classes * (NB_ELEVES // len(classes) + 1))[:NB_ELEVES]
        rng.shuffle(classe_pool)

        idx_famille = 0
        enfants_restants = 0
        nom_famille = ""
        adresse_famille = ""

        for i in range(NB_ELEVES):
            if enfants_restants == 0:
                nom_famille = tuteurs[idx_famille].nom
                adresse_famille = tuteurs[idx_famille].adresse
                enfants_restants = tailles_familles[idx_famille]
                idx_famille += 1
            enfants_restants -= 1

            # EL2500001 (i == 0) : élève de référence des tests e2e, toujours
            # en EF1 (« 1ère Année — A », barème /10, compositions).
            cible = classes[0] if i == 0 else classe_pool[i]
            niveau_actuel = cible.niveau
            frais_insc, mensualite = FRAIS_PAR_NIVEAU[niveau_actuel]

            sexe = "M" if rng.random() < 0.52 else "F"
            prenom = rng.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)

            # Âge cohérent avec le niveau (+ redoublements occasionnels).
            age = 6 + ANNEES.index(niveau_actuel) + rng.choice([-1, 0, 0, 0, 1])
            if rng.random() < 0.12:
                age += 1
            annee_naissance = annee.date_debut.year - age
            date_naiss = date(annee_naissance, rng.randint(1, 12), rng.randint(1, 28))

            eleve = models.Eleves(
                nom=nom_famille, prenom=prenom,
                date_de_naissance=date_naiss,
                lieu_de_naissance=rng.choice(LIEUX_NAISSANCE),
                sexe=sexe,
                adresse=adresse_famille,
                tuteur_id=tuteurs[idx_famille - 1].id,
                classe_id=cible.id, statut="actif",
                acte_naissance=rng.random() < 0.85,
                carnet_sante=rng.random() < 0.75,
            )
            # Transitoire : année d'inscription pour le matricule EL (voir eleves.py)
            eleve.annee_scolaire_id = annee.id
            db.add(eleve)
            db.flush()
            eleves.append(eleve)

            insc = models.Inscriptions(
                matricule_eleve=eleve.matricule, id_classe=cible.id,
                id_annee_scolaire=annee.id, statut="Inscrit",
                statut_passage="EN_ATTENTE",
                montant_total=float(frais_insc + mensualite * 9),
                date_inscription=annee.date_debut,
            )
            db.add(insc)
            db.flush()
            _generer_echeances(db, insc, annee.date_debut)
            inscriptions.append(insc)

            if (i + 1) % 90 == 0:
                db.commit()
        db.commit()

        # ── PLANNING DES ÉVALUATIONS ────────────────────────────────────────
        planning = generer_planning_evaluations(cours_list, total_periodes, rng)

        # ── NOTES (profil d'aptitude par élève) ─────────────────────────────
        classes_map = {c.id: c.niveau for c in classes}
        for idx, el in enumerate(eleves):
            cours_eleve = [c for c in cours_list if el.classe_id in [cls.id for cls in c.classes]]
            generer_notes_pour_eleve(
                db, el, el.classe_id, cours_eleve,
                periodes_pour_niveau(classes_map.get(el.classe_id, ""), periodes_ef1, periodes_ef2),
                planning,
                classe_niveau=classes_map.get(el.classe_id, ""),
                aptitude=rng.gauss(0, 1),
                rng=rng,
            )
            if (idx + 1) % 30 == 0:
                db.commit()
        db.commit()

        # ── BULLETINS ───────────────────────────────────────────────────────
        for classe in classes:
            eleves_classe = [e for e in eleves if e.classe_id == classe.id]
            generer_bulletins_pour_classe(
                db, classe, eleves_classe, cours_list,
                periodes_pour_niveau(classe.niveau, periodes_ef1, periodes_ef2),
            )

        # ── ABSENCES ────────────────────────────────────────────────────────
        aujourdhui = date.today()
        cours_par_classe = {}
        for c in cours_list:
            for aff in c.classes_affectations:
                cours_par_classe.setdefault(aff.id_classe, []).append(c)
        periodes_abs = [
            (nom, debut, min(fin, aujourdhui))
            for nom, debut, fin, _ in total_periodes
            if debut <= aujourdhui
        ]
        for idx, el in enumerate(eleves):
            cours_classe = cours_par_classe.get(el.classe_id, [])
            nb_abs = rng.choices(
                [0, 1, 2, 3, 4, 5, 6, 7, 8],
                weights=[22, 20, 16, 14, 11, 7, 5, 3, 2], k=1,
            )[0]
            if idx == 0:
                # EL2500001 (premier élève inséré) : l'onglet Absences du
                # dossier élève ne rend les groupes par année que s'il existe
                # au moins une absence — on garantit donc un historique.
                nb_abs = max(nb_abs, 4)
            for _ in range(nb_abs):
                if not periodes_abs:
                    break
                _, debut_p, fin_p = rng.choice(periodes_abs)
                justifiee = rng.random() < PROBA_ABSENCE_JUSTIFIEE
                db.add(models.Absences(
                    matricule_eleve=el.matricule,
                    id_cours=rng.choice(cours_classe).id if cours_classe else None,
                    date_absence=_date_entre(rng, debut_p, fin_p),
                    justifiee=justifiee,
                    motif=rng.choice(MOTIFS_ABSENCE_JUSTIFIEE) if justifiee else None,
                ))
            if (idx + 1) % 90 == 0:
                db.commit()
        db.commit()

        # ── PAIEMENTS ───────────────────────────────────────────────────────
        for idx, insc in enumerate(inscriptions):
            generer_paiements(db, insc, annee.date_debut, annee.date_fin, rng)
            if (idx + 1) % 90 == 0:
                db.commit()
        db.commit()

        # ── DÉPENSES ────────────────────────────────────────────────────────
        depenses_seed = [
            ("Salaires des enseignants — Octobre",       "SALAIRES",      "Paie mensuelle du personnel enseignant"),
            ("Salaires des enseignants — Février",       "SALAIRES",      "Paie mensuelle du personnel enseignant"),
            ("Salaire du gardien — Novembre",            "SALAIRES",      "Gardiennage nuit et week-end"),
            ("Prime des surveillants — Décembre",        "SALAIRES",      "Surveillance des récréations et sorties"),
            ("Rames de papier et fournitures de bureau", "FOURNITURES",   "Papier, stylos, craies et classeurs"),
            ("Guides pédagogiques et cahiers",           "FOURNITURES",   "Matériel de préparation des enseignants"),
            ("Manuels scolaires de 7ème Année",          "MATERIEL",      "Jeux de manuels pour le bloc collège"),
            ("Tables-bancs du primaire",                 "MATERIEL",      "Mobiliers pour deux salles du bloc P"),
            ("Matériel informatique",                    "MATERIEL",      "Ordinateurs de la salle informatique"),
            ("Ballons et chasubles",                     "MATERIEL",      "Équipement d'EPS"),
            ("Facture EDM — Novembre",                   "ELECTRICITE",   "Électricité des blocs P et C"),
            ("Facture EDM — Mars",                       "ELECTRICITE",   "Climatisation de la direction"),
            ("Facture SOMAGEP — Janvier",                "EAU",           "Eau des robinets et de la cantine"),
            ("Peinture et entretien des salles",         "ENTRETIEN",     "Réfection avant la rentrée de janvier"),
            ("Réparation de la pompe du forage",         "ENTRETIEN",     "Cour et bloc sanitaire"),
            ("Internet et crédit téléphonique",          "COMMUNICATION", "Connexion du bureau de la direction"),
            ("Location de bus — sortie pédagogique",     "TRANSPORT",     "Visite du musée national (classes de 5ème)"),
            ("Cantine : sacs de riz et huile",           "ALIMENTATION",  "Approvisionnement trimestriel de la cantine"),
        ]
        for libelle, categorie, description in depenses_seed:
            montant_base = rng.randint(45_000, 450_000)
            if categorie == "SALAIRES":
                montant_base = rng.randint(65_000, 2_600_000)
            db.add(models.Depenses(
                libelle=libelle,
                montant=float(round(montant_base, 0)),
                categorie=categorie,
                date=_date_entre(rng, annee.date_debut, min(annee.date_fin, date.today())),
                description=description,
            ))
        db.commit()

        logger.info(
            "Données d'exemple créées : %d élèves (%d familles), %d enseignants, %d classes.",
            len(eleves), len(tuteurs), len(enseignants), len(classes),
        )
    finally:
        db.close()
