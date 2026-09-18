#!/usr/bin/env python3
"""
seed.py — Données de test pour le Collège Privé Excellence (Bamako, Mali)
=========================================================================

Usage :
  python seed.py           # peuple la base existante
  python seed.py --reset   # drop + recreate toutes les tables, puis peuple

Le script est reproductible (random.seed fixé) et génère :
  • 2 années scolaires (2023-2024 clôturée, 2024-2025 active)
  • 12 classes — 3 jardin (Petite → Grande Section) + 9 (1ère → 9ème)
  • 10 enseignants, 10 cours, coefficients par cycle
  • 25 tuteurs, 84 élèves (7/classe)
  • Inscriptions + échéances (frais + 9 mensualités) + paiements simulés
  • Notes pour la 1ère période de chaque niveau + bulletins de la 1ère période (avec rangs)
  • Absences justifiées / injustifiées
  • Dépenses courantes de l'établissement
  • 1 utilisateur (admin)

Adapté au projet CollegeAureole : modèles importés via le paquet `models`,
hash des mots de passe via `hashing.hash_password` (argon2, comme l'app).
"""

import sys
import os
import random
from datetime import date, datetime, timedelta, time as dtime
from collections import defaultdict

# ── Chemin du projet ──────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Base, engine          # adapte selon ton projet
from sqlalchemy.orm import Session

import models
from models.echeances import MOIS_ANNEE_SCOLAIRE
from hashing import hash_password
from bareme import appreciation_for_moyenne, bareme_niveau

# ═══════════════════════════════════════════════════════════════════════════════
#  SEED REPRODUCTIBLE
# ═══════════════════════════════════════════════════════════════════════════════
random.seed(42)

# ═══════════════════════════════════════════════════════════════════════════════
#  RÉFÉRENTIEL MALIEN
# ═══════════════════════════════════════════════════════════════════════════════

NOMS = [
    "Coulibaly", "Diallo", "Traoré", "Konaté", "Keïta", "Sissoko",
    "Sanogo", "Dembélé", "Doumbia", "Touré", "Diabaté", "Kouyaté",
    "Diarra", "Camara", "Bah", "Sylla", "Cissé", "Barry",
    "Samaké", "Koné", "Sidibé", "Fofana", "Niaré", "Maïga",
]
PRENOMS_M = [
    "Moussa", "Ibrahim", "Mamadou", "Oumar", "Sékou", "Boubacar",
    "Abdoulaye", "Modibo", "Seydou", "Youssouf", "Adama", "Lassana",
    "Cheick", "Hamidou", "Souleymane", "Drissa", "Daouda", "Kalilou",
    "Tiémoko", "Bakary",
]
PRENOMS_F = [
    "Aminata", "Fatoumata", "Mariam", "Kadiatou", "Awa", "Hawa",
    "Kadidiatou", "Oumou", "Rokia", "Bintou", "Sira", "Nènè",
    "Djénéba", "Korotoumou", "Salimata", "Djenabou", "Aïssata",
    "Néné", "Coumba",
]
PROFESSIONS = [
    "Commerçant(e)", "Fonctionnaire", "Enseignant(e)", "Médecin",
    "Mécanicien(ne)", "Artisan(e)", "Infirmier(ère)", "Chauffeur",
    "Agriculteur/rice", "Agent de sécurité", "Juriste", "Comptable",
    "Technicien(ne)", "Gérant(e) de boutique",
]
QUARTIERS = [
    "Badalabougou", "Hamdallaye", "Magnambougou", "Lafiabougou",
    "Kalaban-Coro", "Sogoniko", "Missabougou", "Niamakoro",
    "Faladiè", "Banconi", "Medina-Coura", "Quinzambougou",
    "Sabalibougou", "Sikoroni", "Djélibougou",
]
VILLES_MALI = [
    "Bamako", "Ségou", "Mopti", "Sikasso", "Kayes",
    "Koulikoro", "Kati", "San", "Markala", "Niono",
    "Bougouni", "Kita", "Gao",
]

# Correspondance mois → date d'échéance (année scolaire 2024-2025)
MOIS_A_DATE = {
    "Octobre":  date(2024, 10,  5),
    "Novembre": date(2024, 11,  5),
    "Décembre": date(2024, 12,  5),
    "Janvier":  date(2025,  1,  5),
    "Février":  date(2025,  2,  5),
    "Mars":     date(2025,  3,  5),
    "Avril":    date(2025,  4,  5),
    "Mai":      date(2025,  5,  5),
    "Juin":     date(2025,  6,  5),
}

# Modes de paiement courants au Mali
MODES_PAIEMENT = ["Espèces", "Orange Money", "Moov Money", "Virement bancaire"]


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

_emails_vus: set = set()


def _normalise(s: str) -> str:
    """Retire les accents pour construire des adresses e-mail ASCII."""
    table = str.maketrans(
        "àâäéèêëîïôöùûüçñÀÂÄÉÈÊËÎÏÔÖÙÛÜÇÑ",
        "aaaeeeeiioouuucnAAaEEEEIIOOUUUCN",
    )
    return s.lower().translate(table).replace(" ", "").replace("'", "").replace("-", "")


def email_unique(prenom: str, nom: str, domaine: str = "gmail.com") -> str:
    base  = f"{_normalise(prenom)}.{_normalise(nom)}"
    email = f"{base}@{domaine}"
    cpt   = 1
    while email in _emails_vus:
        email = f"{base}{cpt}@{domaine}"
        cpt  += 1
    _emails_vus.add(email)
    return email


def telephone_mali() -> str:
    """Numéro fictif au format malien (+223 XX XX XX XX)."""
    prefixes = ["76", "77", "78", "79", "70", "65", "66", "67", "68", "90", "91"]
    p = random.choice(prefixes)
    return f"+223 {p} {random.randint(10, 99):02d} {random.randint(10, 99):02d} {random.randint(10, 99):02d}"


def adresse_bamako(quartier: str = None) -> str:
    q = quartier or random.choice(QUARTIERS)
    return f"Quartier {q}, Bamako, Mali"


def nina_mali(rng=None) -> str:
    """Numéro d'identification nationale malien (13 chiffres) fictif."""
    rng = rng or random
    return "".join(str(rng.randint(0, 9)) for _ in range(13))


CATEGORIES_ENSEIGNANT = [
    "Instituteur", "Instituteur adjoint", "Maitre", "Professeur contractuel",
]

ECHELONS_ENSEIGNANT = ["Échelon 1", "Échelon 2", "Échelon 3", "Échelon 4"]

SITUATIONS_MATRIMONIALES = ["Célibataire", "Marié(e)", "Divorcé(e)", "Veuf(ve)"]

DIPLOMES_PROF = ["DEF", "BAC", "CAP", "Licence", "Maîtrise", "Master"]

DERNIERS_POSTES = [
    "Collège Badalabougou", "Groupe scolaire Hamdallaye",
    "École publique Magnambougou", "Collège Lafiabougou",
    "Lycée Niamakoro", "Collège Notre Dame du Mali",
]


def date_naissance_eleve(niveau: str) -> date:
    """
    Âge cohérent par rapport au niveau scolaire malien.
    L'âge légal d'entrée en 1ère année est 6 ans.
    """
    tranches = {
        "Petite Section": (3, 4), "Moyenne Section": (4, 5), "Grande Section": (5, 6),
        "1ère Année": (6,  8), "2ème Année": (7,  9), "3ème Année": (8, 10),
        "4ème Année": (9, 11), "5ème Année": (10, 12), "6ème Année": (11, 13),
        "7ème Année": (12, 14), "8ème Année": (13, 15), "9ème Année": (14, 16),
    }
    lo, hi = tranches.get(niveau, (10, 14))
    age    = random.randint(lo, hi)
    # Référence : début de l'année scolaire = octobre 2024
    annee  = 2024 - age
    mois   = random.randint(1, 12)
    jour   = random.randint(1, 28)
    return date(annee, mois, jour)


def note_alea(mini: float, maxi: float) -> float:
    """Note arrondie au quart de point, sur 20."""
    n = random.uniform(mini, maxi)
    return round(round(n * 4) / 4, 2)


def appreciation(moy: float, bareme: int) -> str:
    """Mention selon la moyenne générale — barème malien standard."""
    return appreciation_for_moyenne(moy, bareme)


def nom_parent(sexe: str) -> str:
    """Nom d'un parent, depuis les mêmes pools que les élèves."""
    return random.choice(NOMS)


def prenom_parent(sexe: str) -> str:
    """Prénom d'un parent."""
    return random.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)


FONCTIONS_PARENTS = ["Cultivateur", "Commerçant", "Ménagère", "Enseignant", "Agent de santé", "Chauffeur", "Comptable", "Artisan"]


# ═══════════════════════════════════════════════════════════════════════════════
#  SCRIPT PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def _assurer_etablissement(session: Session) -> None:
    """Garantit la présence de la fiche établissement (une seule ligne id=1).

    Après un --reset cette ligne disparaît (elle est créée par l'assistant
    d'initialisation) : on la recrée pour que l'app reste configurée.
    """
    if session.query(models.Etablissement).first():
        return
    session.add(models.Etablissement(
        nom="Collège Auréole",
        sigle="CA",
        devise="L'Éducation, notre devoir",
        adresse=adresse_bamako("Hamdallaye"),
        telephone="+223 20 23 45 67",
        email="contact@collegeaureole.ml",
        logo=None,
        date_initialisation=date.today(),
        academie="Bamako",
        cap="Tiebani",
    ))


def seed():
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        print("🌱  Collège Auréole — Bamako, Mali")
        print("=" * 58)

        # ─────────────────────────────────────────────────────────────────────
        # 1. UTILISATEURS
        #    Un seul compte administrateur pilote toute l'application.
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Utilisateurs…")
        admin = models.Utilisateurs(
            nom="Konaté", prenom="Modibo",
            email="malademsi@collegeaureole.ml",
            mot_de_passe=hash_password("malademsi"),
            actif=True,
        )
        session.add(admin)
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 2. ANNÉES SCOLAIRES
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Années scolaires…")
        annee_prec = models.AnneesScolaires(
            libelle="2023-2024",
            date_debut=date(2023, 10,  2),
            date_fin  =date(2024,  6, 28),
            active=False,
            cloturee=True,
        )
        annee_cur = models.AnneesScolaires(
            libelle="2024-2025",
            date_debut=date(2024, 10,  7),
            date_fin  =date(2025,  6, 27),
            active=True,
            cloturee=False,
        )
        session.add_all([annee_prec, annee_cur])
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 3. TRIMESTRES / COMPOSITIONS
        #    • 1er cycle (1ère → 5ème) : 9 Compositions
        #    • 6ème (classe spéciale)  : 3 Trimestres + compositions intermédiaires
        #    • 2nd cycle (7ème → 9ème) : 3 Trimestres
        #    Génération via la même routine que l'app (periodes.py) : source de vérité.
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Trimestres et compositions…")
        from periodes import generer_periodes_par_defaut
        crees = generer_periodes_par_defaut(session, annee_cur.id, annee_cur.date_debut, annee_cur.date_fin)
        print(f"    → {crees} périodes créées")

        compos = (
            session.query(models.Trimestres)
            .filter(models.Trimestres.annee_scolaire_id == annee_cur.id, models.Trimestres.type == "COMPOSITION")
            .order_by(models.Trimestres.date_debut.asc())
            .all()
        )
        trims = (
            session.query(models.Trimestres)
            .filter(models.Trimestres.annee_scolaire_id == annee_cur.id, models.Trimestres.type == "TRIMESTRE")
            .order_by(models.Trimestres.date_debut.asc())
            .all()
        )

        # Verrouille la 1ère période (compos. 1 pour le 1er cycle, 1er trimestre
        # pour le 2nd cycle) pour simuler une période déjà clôturée/publée.
        if compos:
            compos[0].verrouille = True
        if trims:
            trims[0].verrouille = True
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 4. SALLES
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Salles…")
        salles_cfg = [
            ("Salle A",            42),
            ("Salle B",            42),
            ("Salle C",            38),
            ("Salle D",            38),
            ("Salle E",            38),
            ("Salle F",            38),
            ("Salle G",            38),
            ("Salle H",            38),
            ("Salle I",            38),
            ("Salle J",            38),
            ("Salle K",            38),


            ("Salle de Sciences",  30),
            ("Salle Informatique", 24),
        ]
        salles = []
        for nom, cap in salles_cfg:
            s = models.Salles(nom=nom, capacite=cap)
            session.add(s)
            salles.append(s)
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 5. ENSEIGNANTS
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Enseignants…")
        ens_data = [
            # (nom, prénom, spécialité, genre, classe tenue)
            ("Kouyaté", "Sékou",     "Mathématiques",                       "M", "7ème A"),
            ("Diabaté", "Mariam",    "Français",                            "F", "5ème A"),
            ("Sissoko", "Hamidou",   "Sciences de la Vie et de la Terre",   "M", "8ème A"),
            ("Dembélé", "Fatoumata", "Histoire-Géographie",                 "F", "8ème A"),
            ("Touré",   "Abdoulaye", "Physique-Chimie",                     "M", "9ème A"),
            ("Camara",  "Aminata",   "Anglais",                             "F", "7ème A"),
            ("Diarra",  "Modibo",    "Arabe",                               "M", "6ème A"),
            ("Sanogo",  "Boubacar",  "Éducation Physique et Sportive",      "M", "3ème A"),
            ("Konaté",  "Sira",      "Sciences d'Éveil",                    "F", "1ère A"),
            ("Bah",     "Lassana",   "Éducation Civique et Morale",         "M", "4ème A"),
        ]
        # Flux aléatoire dédié : les champs administratifs ne consomment pas le
        # générateur global, pour préserver la reproductibilité du reste du seed.
        rng_prof = random.Random(777)
        enseignants = []
        for nom, prenom, spec, genre, classe_tenue in ens_data:
            date_contrat = date(
                rng_prof.randint(2000, 2023), rng_prof.randint(1, 12), rng_prof.randint(1, 28)
            )
            date_titularisation = date_contrat + timedelta(days=rng_prof.randint(180, 2190))
            date_dernier_avancement = date_titularisation + timedelta(days=rng_prof.randint(180, 1095))
            e = models.Enseignants(
                nom=nom, prenom=prenom,
                email=email_unique(prenom, nom, "collegeaureole.ml"),
                telephone=telephone_mali(),
                adresse=adresse_bamako(),
                specialite=spec,
                genre=genre,
                nina=nina_mali(rng_prof),
                date_naissance=date(
                    rng_prof.randint(1965, 1995), rng_prof.randint(1, 12), rng_prof.randint(1, 28)
                ),
                lieu_de_naissance=rng_prof.choice(VILLES_MALI),
                nationalite="Malienne",
                situation_matrimoniale=rng_prof.choice(SITUATIONS_MATRIMONIALES),
                categorie=rng_prof.choice(CATEGORIES_ENSEIGNANT),
                echelon=rng_prof.choice(ECHELONS_ENSEIGNANT),
                fonction=f"Professeur de {spec}",
                sf_nombre_enfants=str(rng_prof.randint(0, 5)),
                date_contrat=date_contrat,
                date_titularisation=date_titularisation,
                date_dernier_avancement=date_dernier_avancement,
                classe_tenue=classe_tenue,
                dernier_poste=rng_prof.choice(DERNIERS_POSTES),
                date_arrivee_cap=date(
                    rng_prof.randint(2005, 2023), rng_prof.randint(1, 12), rng_prof.randint(1, 28)
                ),
                diplome=rng_prof.choice(DIPLOMES_PROF),
            )
            session.add(e)
            enseignants.append(e)
        session.flush()

        # Personnel administratif (directeur, secrétaire) — alimente la section
        # « Personnel administratif » des fiches de renseignements.
        admin_data = [
            ("Abdoulaye", "Traoré",    "Directeur",   "M", "Direction de l'établissement"),
            ("Safiatou",  "Coulibaly", "Secrétaire",  "F", "Secrétariat de direction"),
            ("Moussa",    "Koné",      "Intendant",   "M", "Gestion comptable"),
        ]
        for prenom, nom, fonction, genre, dernier_poste in admin_data:
            date_contrat = date(
                rng_prof.randint(1998, 2020), rng_prof.randint(1, 12), rng_prof.randint(1, 28)
            )
            date_titularisation = date_contrat + timedelta(days=rng_prof.randint(180, 2190))
            date_dernier_avancement = date_titularisation + timedelta(days=rng_prof.randint(180, 1095))
            session.add(models.Enseignants(
                nom=nom, prenom=prenom,
                email=email_unique(prenom, nom, "collegeaureole.ml"),
                telephone=telephone_mali(),
                adresse=adresse_bamako(),
                specialite="Administration",
                genre=genre,
                nina=nina_mali(rng_prof),
                date_naissance=date(
                    rng_prof.randint(1960, 1985), rng_prof.randint(1, 12), rng_prof.randint(1, 28)
                ),
                lieu_de_naissance=rng_prof.choice(VILLES_MALI),
                nationalite="Malienne",
                situation_matrimoniale=rng_prof.choice(SITUATIONS_MATRIMONIALES),
                categorie="Personnel administratif",
                echelon=rng_prof.choice(ECHELONS_ENSEIGNANT),
                fonction=fonction,
                sf_nombre_enfants=str(rng_prof.randint(0, 5)),
                date_contrat=date_contrat,
                date_titularisation=date_titularisation,
                date_dernier_avancement=date_dernier_avancement,
                dernier_poste=dernier_poste,
                date_arrivee_cap=date(
                    rng_prof.randint(1998, 2023), rng_prof.randint(1, 12), rng_prof.randint(1, 28)
                ),
                diplome=rng_prof.choice(["BAC", "Licence", "Maîtrise"]),
            ))
        session.flush()

        e_math, e_fr, e_svt, e_hg, e_pc, e_ang, e_ar, e_eps, e_se, e_ecm = enseignants

        # ─────────────────────────────────────────────────────────────────────
        # 6. COURS
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Cours…")
        cours_data = [
            # (nom, description, volume_horaire_hebdo, enseignant)
            ("Français",
             "Langue française, expression écrite et littérature", 6, e_fr),
            ("Mathématiques",
             "Arithmétique, algèbre, géométrie et statistiques", 6, e_math),
            ("Sciences de la Vie et de la Terre",
             "Biologie, géologie et écologie fondamentales", 3, e_svt),
            ("Histoire-Géographie",
             "Histoire du Mali, de l'Afrique et géographie mondiale", 2, e_hg),
            ("Physique-Chimie",
             "Physique et chimie appliquées au niveau fondamental", 3, e_pc),
            ("Anglais",
             "Langue anglaise — niveaux A2 à B1 du CECRL", 3, e_ang),
            ("Arabe",
             "Langue arabe classique et civilisation islamique", 3, e_ar),
            ("Éducation Physique et Sportive",
             "Activités physiques, sportives et santé", 2, e_eps),
            ("Sciences d'Éveil",
             "Éveil scientifique, technologique et environnemental (1er cycle)", 3, e_se),
            ("Éducation Civique et Morale",
             "Citoyenneté, droits, devoirs et valeurs républicaines", 2, e_ecm),
        ]
        cours_list = []
        for nom, desc, vh, ens in cours_data:
            c = models.Cours(
                nom=nom, description=desc, volume_horaire=vh,
                matricule_enseignant=ens.matricule,
            )
            session.add(c)
            cours_list.append(c)
        session.flush()

        c_fr, c_math, c_svt, c_hg, c_pc, c_ang, c_ar, c_eps, c_se, c_ecm = cours_list

        # ─────────────────────────────────────────────────────────────────────
        # 7. CLASSES (jardin → 9ème)
        #    Frais pratiqués dans les collèges privés de Bamako (FCFA)
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Classes…")
        #              niveau           nom               inscription  mensualité  salle
        classes_cfg = [
            ("Petite Section",   "Petite Section A",   5_000,   2_000, salles[0]),
            ("Moyenne Section",  "Moyenne Section A",  6_000,   2_500, salles[1]),
            ("Grande Section",   "Grande Section A",   7_000,   3_000, salles[2]),
            ("1ère Année", "1ère A",  15_000,  5_000, salles[3]),
            ("2ème Année", "2ème A",  15_000,  5_500, salles[4]),
            ("3ème Année", "3ème A",  17_000,  6_000, salles[5]),
            ("4ème Année", "4ème A",  17_000,  6_500, salles[6]),
            ("5ème Année", "5ème A",  20_000,  7_500, salles[7]),
            ("6ème Année", "6ème A",  22_000,  8_500, salles[11]),
            ("7ème Année", "7ème A",  25_000, 10_000, salles[8]),
            ("8ème Année", "8ème A",  25_000, 10_000, salles[9]),
            ("9ème Année", "9ème A",  30_000, 12_000, salles[10]),
        ]
        classes = []
        for niveau, nom, frais, mens, salle in classes_cfg:
            cl = models.Classes(
                niveau=niveau, nom=nom,
                frais_inscription=float(frais),
                mensualite=float(mens),
                id_salle=salle.id,
            )
            session.add(cl)
            classes.append(cl)
        session.flush()

        classes_jardin = classes[:3]   # Petite → Grande Section
        classes_1er    = classes[3:9]  # 1ère → 6ème
        classes_2nd    = classes[9:]   # 7ème → 9ème
        classes_6eme   = [classes[8]]  # 6ème (classe spéciale : trimestres coefficies)

        # ─────────────────────────────────────────────────────────────────────
        # 8. AFFECTATION COURS ↔ CLASSES (avec coefficients par cycle)
        #
        #    1er cycle (1ère à 5ème) — 7 matières, SANS coefficients (moyenne simple)
        #    6ème (classe spéciale)   — 7 matières, coefficients uniquement pour
        #                               les TRIMESTRES (toujours notés sur 10)
        #    2nd cycle (7ème à 9ème)  — 9 matières, coefficients
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Affectation cours ↔ classes…")

        # (cours_obj, coefficient)
        matieres_1er = [
            (c_fr,   1), (c_math, 1), (c_se,  1),
            (c_hg,   1), (c_ecm, 1),  (c_eps, 1), (c_ar, 1),
        ]
        # Coefficients appliqués aux TRIMESTRES de la 6ème (sur 10) : mêmes
        # matières que le 1er cycle, mais pondérées pour le bulletin trimestriel.
        matieres_6eme = [
            (c_fr,   4), (c_math, 4), (c_se,  3),
            (c_hg,   2), (c_ecm, 2),  (c_eps, 1), (c_ar, 2),
        ]
        matieres_2nd = [
            (c_fr,   4), (c_math, 4), (c_svt, 3), (c_hg,  2),
            (c_pc,   3), (c_ang,  2), (c_ar,  2), (c_eps, 1), (c_ecm, 1),
        ]

        for cl in classes_1er:
            if cl in classes_6eme:
                mats = matieres_6eme
            else:
                mats = matieres_1er
            for c_obj, coef in mats:
                session.add(models.AffectationCoursClasse(
                    id_classe=cl.id, id_cours=c_obj.id, coefficient=float(coef),
                ))
        for cl in classes_2nd:
            for c_obj, coef in matieres_2nd:
                session.add(models.AffectationCoursClasse(
                    id_classe=cl.id, id_cours=c_obj.id, coefficient=float(coef),
                ))
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 9. SÉANCES (emploi du temps type — un créneau par matière)
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Séances (emploi du temps)…")
        JOURS  = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"]
        PLAGES = [
            (dtime(7, 30), dtime(9,  0)),
            (dtime(9,  0), dtime(10, 30)),
            (dtime(10,45), dtime(12, 15)),
            (dtime(14,  0), dtime(15, 30)),
            (dtime(15, 30), dtime(17,  0)),
        ]

        for cl in classes_1er + classes_2nd:
            mats = matieres_1er if cl in classes_1er else matieres_2nd
            for idx, (c_obj, _) in enumerate(mats):
                debut, fin = PLAGES[idx % len(PLAGES)]
                session.add(models.Seances(
                    id_cours=c_obj.id,
                    id_classe=cl.id,
                    id_annee_scolaire=annee_cur.id,
                    id_salle=cl.id_salle,
                    jour_semaine=JOURS[idx % len(JOURS)],
                    heure_debut=debut,
                    heure_fin=fin,
                ))
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 10. TUTEURS
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Tuteurs…")
        tuteurs = []
        for _ in range(25):
            sexe_t   = random.choice(["M", "F"])
            prenom_t = random.choice(PRENOMS_M if sexe_t == "M" else PRENOMS_F)
            nom_t    = random.choice(NOMS)
            t = models.Tuteurs(
                nom=nom_t, prenom=prenom_t,
                email=email_unique(prenom_t, nom_t),
                telephone=telephone_mali(),
                adresse=adresse_bamako(),
                profession=random.choice(PROFESSIONS),
            )
            session.add(t)
            tuteurs.append(t)
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 11. ÉLÈVES + INSCRIPTIONS + ÉCHÉANCES + PAIEMENTS
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Élèves, inscriptions, échéances, paiements…")

        N_PAR_CLASSE = 7   # → 84 élèves au total (12 classes)

        # Structure de collecte pour les sections suivantes
        # (eleve, classe, inscription, matieres, periodes)
        tous_eleves: list = []

        for cl in classes:
            jardin          = cl in classes_jardin
            if jardin:
                mats     = []
                periodes = []
            elif cl in classes_6eme:
                # 6ème (classe spéciale) : trimestres + compositions intermédiaires
                mats     = matieres_6eme
                periodes = compos + trims
            elif cl in classes_1er:
                mats     = matieres_1er
                periodes = compos
            else:
                mats     = matieres_2nd
                periodes = trims

            for _ in range(N_PAR_CLASSE):
                sexe     = random.choice(["M", "F"])
                prenom_e = random.choice(PRENOMS_M if sexe == "M" else PRENOMS_F)
                nom_e    = random.choice(NOMS)
                tuteur   = random.choice(tuteurs)
                acte     = random.choices([True, False], weights=[80, 20])[0]

                # ── Élève ───────────────────────────────────────────────────
                eleve = models.Eleves(
                    nom=nom_e,
                    prenom=prenom_e,
                    date_de_naissance=date_naissance_eleve(cl.niveau),
                    lieu_de_naissance=random.choice(VILLES_MALI),
                    sexe=sexe,
                    adresse=adresse_bamako(),
                    statut="actif",
                    acte_naissance=acte,
                    carnet_sante=random.choices([True, False], weights=[65, 35])[0],
                    nom_pere=nom_parent("M"),
                    prenom_pere=prenom_parent("M"),
                    fonction_pere=random.choice(FONCTIONS_PARENTS),
                    nom_mere=nom_parent("F"),
                    prenom_mere=prenom_parent("F"),
                    fonction_mere=random.choice(FONCTIONS_PARENTS),
                    tuteur_id=tuteur.id,
                    classe_id=cl.id,
                )
                # Attribut transitoire requis par le listener before_insert
                eleve.annee_scolaire_id = annee_cur.id
                session.add(eleve)
                session.flush()   # ← génère le matricule via before_insert

                # ── Inscription ─────────────────────────────────────────────
                date_insc    = date(2024, 10, random.randint(1, 15))
                montant_total = cl.frais_inscription + cl.mensualite * 9

                insc = models.Inscriptions(
                    matricule_eleve=eleve.matricule,
                    id_classe=cl.id,
                    id_annee_scolaire=annee_cur.id,
                    statut="Inscrit",
                    statut_passage="EN_ATTENTE",
                    montant_total=montant_total,
                    credit_disponible=0.0,
                    date_inscription=date_insc,
                )
                session.add(insc)
                session.flush()

                # ── Échéance : frais d'inscription (toujours soldée) ────────
                ech_ins = models.Echeances(
                    id_inscription=insc.id,
                    id_classe=cl.id,
                    type_echeance="INSCRIPTION",
                    mois=None,
                    date_echeance=date_insc,
                    montant_du=cl.frais_inscription,
                    montant_paye=cl.frais_inscription,
                    statut="SOLDE",
                )
                session.add(ech_ins)
                session.flush()

                session.add(models.Paiements(
                    id_inscription=insc.id,
                    id_echeance=ech_ins.id,
                    date=date_insc,
                    montant=cl.frais_inscription,
                    mode=random.choice(MODES_PAIEMENT),
                    observation="Règlement frais d'inscription",
                ))

                # ── Échéances mensuelles (octobre → juin) ───────────────────
                for i, mois in enumerate(MOIS_ANNEE_SCOLAIRE):
                    ech_date = MOIS_A_DATE[mois]

                    # Simulation de l'avancement des paiements :
                    #   Oct–Déc (i 0-2)  : 100 % soldés
                    #   Jan–Fév (i 3-4)  : 75 % soldés, 15 % partiels (50 %)
                    #   Mar–Avr (i 5-6)  : 50 % soldés, 20 % partiels
                    #   Mai–Jun (i 7-8)  : 30 % soldés, 10 % partiels
                    if i <= 2:
                        r = 1.0
                    elif i <= 4:
                        r = random.choices([1.0, 0.5, 0.0], weights=[75, 15, 10])[0]
                    elif i <= 6:
                        r = random.choices([1.0, 0.5, 0.0], weights=[50, 20, 30])[0]
                    else:
                        r = random.choices([1.0, 0.5, 0.0], weights=[30, 10, 60])[0]

                    paye = round(cl.mensualite * r, 2)

                    if paye >= cl.mensualite:
                        statut = "SOLDE"
                    elif paye > 0:
                        statut = "PARTIEL"
                    else:
                        statut = "EN_ATTENTE"

                    ech = models.Echeances(
                        id_inscription=insc.id,
                        id_classe=cl.id,
                        type_echeance="MENSUALITE",
                        mois=mois,
                        date_echeance=ech_date,
                        montant_du=cl.mensualite,
                        montant_paye=paye,
                        statut=statut,
                    )
                    session.add(ech)
                    session.flush()

                    if paye > 0:
                        session.add(models.Paiements(
                            id_inscription=insc.id,
                            id_echeance=ech.id,
                            date=ech_date + timedelta(days=random.randint(0, 8)),
                            montant=paye,
                            mode=random.choice(MODES_PAIEMENT),
                        ))

                session.flush()
                tous_eleves.append((eleve, cl, insc, mats, periodes))

        # ─────────────────────────────────────────────────────────────────────
        # 12. ABSENCES
        #     Jours de classe : octobre 2024 (hors week-end)
        #     30 % des élèves ont eu au moins une absence
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Absences…")
        debut_annee = date(2024, 10, 7)
        jours_classe = [
            debut_annee + timedelta(days=k)
            for k in range(55)
            if (debut_annee + timedelta(days=k)).weekday() < 5
        ]

        eleves_absents = random.sample(
            tous_eleves,
            k=max(1, len(tous_eleves) * 30 // 100),
        )
        for eleve, cl, insc, mats, *_ in eleves_absents:
            jours_vus = set()
            for _ in range(random.randint(1, 4)):
                jour = random.choice(jours_classe)
                if jour in jours_vus:
                    continue         # une seule absence déclarée par jour
                jours_vus.add(jour)

                justifiee = random.choices([True, False], weights=[60, 40])[0]
                session.add(models.Absences(
                    matricule_eleve=eleve.matricule,
                    id_cours=random.choice(mats)[0].id if mats else None,
                    date_absence=jour,
                    justifiee=justifiee,
                    motif="Maladie" if justifiee else None,
                    justifiee_par_id=admin.id if justifiee else None,
                    date_justification=(
                        datetime(jour.year, jour.month, jour.day, 8, 0)
                        if justifiee else None
                    ),
                ))
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 13. NOTES
        #     Chaque élève a un « profil de niveau » fixe
        #     qui lui assure une certaine cohérence d'une matière à l'autre.
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Notes (1ère période de chaque niveau)…")

        # {(matricule, id_classe): {id_trim: {id_cours: (note, note_classe, coef)}}}
        notes_index: dict = {}

        for eleve, cl, insc, mats, periodes in tous_eleves:
            # Profil de l'élève : bon / moyen / faible (exprimé sur 20)
            profil = random.choices(
                [("bon", 12, 19.5), ("moyen", 7, 15), ("faible", 3, 11)],
                weights=[35, 45, 20],
            )[0]
            _, p_min, p_max = profil

            # Les notes respectent le barème malien : /10 en EF1 (1ère-6ème),
            # /20 en EF2 (7ème-9ème) et lycée.
            bareme = bareme_niveau(cl.niveau)
            echelle_profil = 20.0
            p_min = p_min / echelle_profil * bareme
            p_max = p_max / echelle_profil * bareme

            notes_index[(eleve.matricule, cl.id)] = {}

            for periode in periodes:
                notes_index[(eleve.matricule, cl.id)][periode.id] = {}

                for c_obj, coef in mats:
                    # Légère variation aléatoire autour du profil
                    mini = max(0.0, p_min + random.uniform(-2, 1))
                    maxi = min(float(bareme), p_max + random.uniform(-1, 2))
                    if mini >= maxi:
                        mini, maxi = max(0.0, maxi - 3), min(float(bareme), mini + 3)

                    val = note_alea(mini, maxi)

                    # Note de classe : proche de la note de composition
                    # (moyenne matière = 60% composition + 40% classe).
                    val_classe = round(
                        min(float(bareme), max(0.0, val + random.uniform(-1.5, 1.5))),
                        1,
                    )

                    # La date de la note est proche de la fin de chaque période
                    jours_avant_fin = random.randint(3, 14)
                    note_date = periode.date_fin - timedelta(days=jours_avant_fin)

                    session.add(models.Notes(
                        matricule_eleve=eleve.matricule,
                        id_cours=c_obj.id,
                        id_classe=cl.id,
                        matricule_enseignant=c_obj.matricule_enseignant,
                        id_trimestre=periode.id,
                        note=val,
                        note_classe=val_classe,
                        date=note_date,
                    ))
                    notes_index[(eleve.matricule, cl.id)][periode.id][c_obj.id] = (val, val_classe, coef)

        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 14. BULLETINS (1ère période uniquement — verrouillée et publiée)
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Bulletins (1ère période, publiés)…")

        # Groupement pour le calcul des rangs : {(id_classe, id_periode): [(moy, bul)]}
        bulletins_par_groupe: dict = defaultdict(list)

        for eleve, cl, insc, mats, periodes in tous_eleves:
            if not periodes:
                continue   # jardin : évaluation par appréciation, pas de bulletins
            periode = periodes[0]   # 1ère période, verrouillée et publiée

            # Barème malien selon le niveau : EF1 → /10, EF2/lycée → /20.
            bareme = bareme_niveau(cl.niveau)
            # 6ème : trimestre → moyenne pondérée (coeff.), composition → moyenne simple.
            trimestre_6eme = cl in classes_6eme and periode.type == "TRIMESTRE"
            utilise_coeff = (bareme != 10) or trimestre_6eme

            notes_p = notes_index[(eleve.matricule, cl.id)][periode.id]

            # Moyenne matière = 60% note de composition + 40% note de classe
            # (si absente, la note de composition fait foi).
            matieres_moy = []
            somme_pts = 0.0
            somme_coef = 0.0
            for note_v, note_classe_v, coef_v in notes_p.values():
                mv = 0.6 * note_v + 0.4 * (note_classe_v if note_classe_v is not None else note_v)
                matieres_moy.append(mv)
                if utilise_coeff:
                    somme_pts += mv * coef_v
                    somme_coef += coef_v

            if utilise_coeff:
                moy = round(somme_pts / somme_coef, 2) if somme_coef else 0.0
            else:
                moy = round(sum(matieres_moy) / len(matieres_moy), 2) if matieres_moy else 0.0

            bul = models.Bulletins(
                matricule_eleve=eleve.matricule,
                id_trimestre=periode.id,
                id_classe=cl.id,
                moyenne_generale=moy,
                rang=None,          # calculé après le flush
                appreciation=appreciation(moy, bareme),
                statut="PUBLIE",
                generated_at=datetime(2024, 12, 10, 9, 0),
                published_at=datetime(2024, 12, 15, 8, 0),
            )
            session.add(bul)
            session.flush()

            # Détails par matière (coefficient miroir de _calculer_bulletin :
            # compositions → 1.0 ; trimestre 6ème / EF2 → coefficient réel)
            for c_obj, coef in mats:
                note_v, note_classe_v, _ = notes_p.get(c_obj.id, (0.0, None, coef))
                mv = 0.6 * note_v + 0.4 * (note_classe_v if note_classe_v is not None else note_v)
                session.add(models.BulletinDetails(
                    id_bulletin=bul.id,
                    id_cours=c_obj.id,
                    moyenne=round(mv, 2),
                    coefficient=float(coef) if utilise_coeff else 1.0,
                ))

            bulletins_par_groupe[(cl.id, periode.id)].append((moy, bul))

        session.flush()

        # Calcul des rangs au sein de chaque classe
        for (id_cl, id_per), liste in bulletins_par_groupe.items():
            tries = sorted(liste, key=lambda x: x[0], reverse=True)
            for rang, (_, bul) in enumerate(tries, start=1):
                bul.rang = rang
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 15. DÉPENSES
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Dépenses…")
        depenses_data = [
            # (libelle, montant FCFA, categorie, date)
            ("Salaires enseignants — Octobre 2024",  1_050_000, "SALAIRES",    date(2024, 10, 31)),
            ("Salaires enseignants — Novembre 2024", 1_050_000, "SALAIRES",    date(2024, 11, 29)),
            ("Salaires enseignants — Décembre 2024", 1_050_000, "SALAIRES",    date(2024, 12, 31)),
            ("Eau et électricité — Octobre 2024",       48_000, "CHARGES",     date(2024, 10, 20)),
            ("Eau et électricité — Novembre 2024",      51_000, "CHARGES",     date(2024, 11, 20)),
            ("Eau et électricité — Décembre 2024",      57_000, "CHARGES",     date(2024, 12, 20)),
            ("Fournitures scolaires (craies, marqueurs, cahiers)",
                                                        42_000, "FOURNITURES", date(2024, 10,  8)),
            ("Achat de manuels pédagogiques 2024-2025",
                                                        95_000, "FOURNITURES", date(2024, 10,  3)),
            ("Réparation tableau — Salle C",            12_000, "MAINTENANCE", date(2024, 11,  5)),
            ("Réparation ventilateurs — Salles A et B", 18_000, "MAINTENANCE", date(2024, 10, 22)),
            ("Abonnement Internet (forfait mensuel)",    25_000, "CHARGES",     date(2024, 10,  1)),
            ("Produits d'entretien et ménage",           9_500, "FOURNITURES", date(2024, 10, 15)),
            ("Photocopies et impressions",              16_000, "FOURNITURES", date(2024, 11,  3)),
            ("Frais bancaires",                          4_500, "AUTRE",       date(2024, 12,  5)),
            ("Déplacement — réunion DCSE Bamako",        8_000, "AUTRE",       date(2024, 11, 14)),
        ]
        for libelle, montant, cat, dt in depenses_data:
            session.add(models.Depenses(
                libelle=libelle,
                montant=float(montant),
                categorie=cat,
                date=dt,
                description=f"Collège Auréole — {cat.lower()}",
            ))
        session.flush()

        # ─────────────────────────────────────────────────────────────────────
        # 16. ÉTABLISSEMENT (préservé après un --reset)
        # ─────────────────────────────────────────────────────────────────────
        print("▶  Établissement…")
        _assurer_etablissement(session)

        # ─────────────────────────────────────────────────────────────────────
        # COMMIT FINAL
        # ─────────────────────────────────────────────────────────────────────
        session.commit()

        # ── Résumé ────────────────────────────────────────────────────────────
        n_e = len(tous_eleves)
        print()
        print("✅  Base de données remplie avec succès !")
        print(f"    Établissement  : Collège Auréole, Bamako")
        print(f"    Année active   : 2024-2025")
        print(f"    Classes        : {len(classes)}  "
              f"({len(classes_jardin)} × jardin, {len(classes_1er)} × 1er cycle dont 6ème, {len(classes_2nd)} × 2nd cycle)")
        print(f"    Élèves         : {n_e}  ({N_PAR_CLASSE}/classe)")
        print(f"    Tuteurs        : {len(tuteurs)}")
        print(f"    Enseignants    : {len(enseignants)}")
        print(f"    Cours          : {len(cours_list)}")
        print(f"    Inscriptions   : {n_e}  + {n_e * 10} échéances")
        print(f"    Bulletins      : {len(classes_1er) * N_PAR_CLASSE + len(classes_2nd) * N_PAR_CLASSE}  "
              f"(1ère période, publiés avec rangs — pas de bulletins en jardin)")
        print(f"    Dépenses       : {len(depenses_data)}")
        print(f"    Utilisateurs   : 1  (admin)")


# ═══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if "--reset" in sys.argv:
        print("⚠️   Suppression et recréation de toutes les tables…")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print()
    else:
        with Session(engine) as session:
            if session.query(models.Utilisateurs).first():
                print("ℹ️   La base contient déjà des données (seed non idempotent).")
                print("     Relancez avec `--reset` pour tout régénérer — "
                      "⚠️ cela efface les données existantes.")
                sys.exit(1)
    seed()