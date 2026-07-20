import random
from datetime import date, time
from faker import Faker
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from hashing import hash_password
from enums import RoleUtilisateur
import models
from models.bulletins import BulletinDetails
from models.associations import AffectationCoursClasse

fake = Faker("fr_FR")

# ──────────────────────────────────────────────────────────────────────────────
# Système scolaire malien
# 1ère → 6ème année  : Enseignement Fondamental 1er cycle (EF1)
# 7ème → 9ème année  : Enseignement Fondamental 2ème cycle (EF2)
# ──────────────────────────────────────────────────────────────────────────────

NB_TUTEURS              = 220
NB_ELEVES               = 450   # ~25 élèves par classe (18 classes)
NB_NOTES_PAR_COURS      = 3     # évaluations par trimestre par cours
PROBA_ABSENCE_JUSTIFIEE = 0.4   # ~40 % des absences sont justifiées

# Pourcentage d'élèves qui ont un historique sur l'année précédente
PROBA_HISTORIQUE_ANCIEN = 0.30  # ~30 % des élèves ont une inscription sur 2024-2025

# Frais de scolarité annuels (FCFA) selon le cycle
FRAIS_EF1 = 75_000
FRAIS_EF2 = 95_000

MODES_PAIEMENT = ["Espèces", "Mobile Money", "Chèque", "Virement"]

ANNEES = [
    "1ère Année", "2ème Année", "3ème Année",
    "4ème Année", "5ème Année", "6ème Année",   # EF1
    "7ème Année", "8ème Année", "9ème Année",   # EF2
]

DIVISIONS = ["A"]  # 2 divisions → 18 classes au total

MATIERES_EF1 = [
    ("Lecture / Écriture",           "Apprentissage de la lecture et de l'écriture en français", 6),
    ("Mathématiques",                "Calcul, numération, géométrie et mesures",                 6),
    ("Langue Nationale (Bambara)",   "Expression orale et écrite en bambara",                    4),
    ("Activités d'Éveil",            "Découverte du monde, sciences et société",                 3),
    ("Éducation Physique",           "Motricité, jeux collectifs et hygiène",                    2),
    ("Dessin / Travaux Manuels",     "Arts plastiques et activités manuelles",                   2),
]

MATIERES_EF2 = [
    ("Français",                     "Grammaire, conjugaison, expression écrite et littérature", 5),
    ("Mathématiques",                "Algèbre, géométrie, statistiques et probabilités",         5),
    ("Sciences Naturelles",          "Biologie, écologie et sciences de la vie",                 3),
    ("Physique-Chimie",              "Mécanique, électricité et chimie",                         3),
    ("Histoire-Géographie",          "Histoire du Mali, de l'Afrique et géographie mondiale",    3),
    ("Éducation Civique et Morale",  "Droits, devoirs, citoyenneté et valeurs",                  2),
    ("Anglais",                      "Initiation à la langue anglaise",                          3),
    ("Éducation Physique",           "Sport, athlétisme et hygiène de vie",                      2),
    ("Informatique",                 "Initiation aux outils numériques et bureautique",           2),
]

# Année active : 2025-2026
TRIMESTRES_ACTIFS = [
    ("Trimestre 1", date(2025, 10, 1),  date(2025, 12, 20)),
    ("Trimestre 2", date(2026, 1, 5),   date(2026, 3, 31)),
    ("Trimestre 3", date(2026, 4, 6),   date(2026, 7, 31)),
]

# Année précédente : 2024-2025 (terminée → statut_passage défini)
TRIMESTRES_ANCIENS = [
    ("Trimestre 1", date(2024, 10, 1),  date(2024, 12, 20)),
    ("Trimestre 2", date(2025, 1, 5),   date(2025, 3, 31)),
    ("Trimestre 3", date(2025, 4, 6),   date(2025, 7, 31)),
]

PROFESSIONS_TUTEURS = [
    "Cultivateur", "Commerçant(e)", "Fonctionnaire", "Enseignant(e)", "Artisan",
    "Mécanicien", "Couturier(ère)", "Infirmier(e)", "Chauffeur", "Maçon",
    "Forgeron", "Pêcheur", "Éleveur", "Menuisier", "Agent de sécurité",
    "Boutiquier", "Tailleur", "Sage-femme", "Électricien", "Plombier",
    "Médecin", "Pharmacien(ne)", "Comptable", "Juriste", "Militaire",
]

MOTIFS_ABSENCE_JUSTIFIEE = [
    "Maladie", "Rendez-vous médical", "Événement familial",
    "Cérémonie traditionnelle", "Problème de transport",
]

JOURS_SEMAINE   = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
CRENEAUX_HORAIRES = [
    (time(8, 0),   time(10, 0)),
    (time(10, 15), time(12, 15)),
    (time(14, 0),  time(16, 0)),
    (time(16, 15), time(18, 15)),
]

EF1 = ANNEES[:6]
EF2 = ANNEES[6:]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def niveau_precedent(niveau: str) -> str | None:
    """Retourne l'année précédente dans le cursus, ou None si c'est la 1ère."""
    idx = ANNEES.index(niveau)
    return ANNEES[idx - 1] if idx > 0 else None


def _mettre_a_jour_statut_echeance(ech):
    if ech.montant_paye <= 0:
        ech.statut = "EN_ATTENTE"
    elif ech.montant_paye >= ech.montant_du:
        ech.statut = "SOLDE"
    else:
        ech.statut = "PARTIEL"


def _generer_echeances_seed(db, inscription, annee_debut):
    """Génère les échéances pour une inscription (frais + 9 mensualités)."""
    from models.echeances import MOIS_ANNEE_SCOLAIRE
    classe = db.query(models.Classes).filter(models.Classes.id == inscription.id_classe).first()
    frais_insc = getattr(classe, 'frais_inscription', 0.0) or 0.0
    mensualite = getattr(classe, 'mensualite', 0.0) or 0.0
    annee_int  = annee_debut.year

    # Frais inscription
    ech_insc = models.Echeances(
        id_inscription=inscription.id,
        id_classe=inscription.id_classe,
        type_echeance="INSCRIPTION",
        mois=None,
        date_echeance=inscription.date_inscription,
        montant_du=frais_insc,
        montant_paye=0.0,
        statut="EN_ATTENTE" if frais_insc > 0 else "SOLDE",
    )
    db.add(ech_insc)

    # Mensualités
    for i, mois in enumerate(MOIS_ANNEE_SCOLAIRE):
        if i < 3:
            annee_m, num_m = annee_int, 10 + i
        else:
            annee_m, num_m = annee_int + 1, i - 2
        db.add(models.Echeances(
            id_inscription=inscription.id,
            id_classe=inscription.id_classe,
            type_echeance="MENSUALITE",
            mois=mois,
            date_echeance=date(annee_m, num_m, 5),
            montant_du=mensualite,
            montant_paye=0.0,
            statut="EN_ATTENTE" if mensualite > 0 else "SOLDE",
        ))

    # Mettre à jour montant_total
    inscription.montant_total = frais_insc + (mensualite * 9)
    db.flush()


def generer_paiements(db, inscription, annee_debut, annee_fin, modes):
    """Génère des paiements réalistes distribués sur les échéances."""
    montant_du = inscription.montant_total
    profil = random.choices(
        ["solde_complet", "echelonne", "partiel", "aucun"],
        weights=[35, 40, 15, 10], k=1
    )[0]

    if profil == "aucun":
        return 0, 0.0

    elif profil == "solde_complet":
        versements = [montant_du]

    elif profil == "echelonne":
        nb_v = random.choice([2, 3])
        parts = sorted(random.sample(range(1, 100), nb_v - 1))
        parts = [0] + parts + [100]
        versements = [
            round(montant_du * (parts[k + 1] - parts[k]) / 100, 0)
            for k in range(nb_v)
        ]
    else:  # partiel
        nb_v = random.choice([1, 2])
        fraction = random.uniform(0.2, 0.7)
        montant_paye = round(montant_du * fraction, 0)
        if nb_v == 1:
            versements = [montant_paye]
        else:
            p1 = round(montant_paye * random.uniform(0.4, 0.6), 0)
            versements = [p1, montant_paye - p1]

    date_courante   = annee_debut
    total_paiements = 0
    total_montant   = 0.0

    for num, montant_v in enumerate(versements, start=1):
        if montant_v <= 0:
            continue
        date_courante = fake.date_between(
            start_date=date_courante,
            end_date=min(date.today(), annee_fin)
        )

        # Distribuer sur les échéances impayées
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
            sur_ech = min(reste, a_payer)
            db.add(models.Paiements(
                id_inscription=inscription.id,
                id_echeance=ech.id,
                date=date_courante,
                numero_recu=f"REC-{annee_debut.year}-{inscription.id:05d}-{num}",
                montant=sur_ech,
                mode=random.choice(modes),
                observation=None,
            ))
            ech.montant_paye += sur_ech
            _mettre_a_jour_statut_echeance(ech)
            reste -= sur_ech

        total_paiements += 1
        total_montant   += float(montant_v)

    return total_paiements, total_montant


def generer_planning_evaluations(cours_list, trimestres_objets, trimestres_dates):
    """
    Génère à l'avance les dates fixes des évaluations par cours et par trimestre.
    Structure retournée : planning[(id_cours, id_trimestre)] = [date1, date2, date3]
    """
    planning = {}
    for co in cours_list:
        for (_, date_debut, date_fin), trim_obj in zip(trimestres_dates, trimestres_objets):
            dates_evals = sorted([
                fake.date_between(start_date=date_debut, end_date=date_fin)
                for _ in range(NB_NOTES_PAR_COURS)
            ])
            planning[(co.id, trim_obj.id)] = dates_evals
    return planning


def generer_notes_pour_eleve(db, eleve, id_classe_courante, cours_eleve, trimestres_objets, planning_evals):
    """Génère les notes d'un élève à partir des dates d'évaluations prédéfinies."""
    total = 0
    for co in cours_eleve:
        for trim_obj in trimestres_objets:
            dates_evals = planning_evals.get((co.id, trim_obj.id), [])
            for date_eval in dates_evals:
                db.add(models.Notes(
                    date=date_eval,  # On passe un objet datetime.date propre
                    note=round(random.uniform(0.0, 20.0), 2),
                    matricule_eleve=eleve.matricule,
                    id_cours=co.id,
                    id_classe=id_classe_courante,
                    matricule_enseignant=co.matricule_enseignant,
                    id_trimestre=trim_obj.id,
                ))
                total += 1
    return total


def generer_bulletins_pour_classe(db, classe, eleves_classe, cours_list, trimestres_objets):
    """Génère les bulletins (3 trimestres) pour tous les élèves d'une classe."""
    from sqlalchemy import func as _func
    total = 0

    for trimestre_obj in trimestres_objets:
        bulletins_classe = []

        for eleve in eleves_classe:
            moyennes_par_cours = (
                db.query(models.Notes.id_cours, _func.avg(models.Notes.note))
                .filter(
                    models.Notes.matricule_eleve == eleve.matricule,
                    models.Notes.id_trimestre == trimestre_obj.id,
                )
                .group_by(models.Notes.id_cours)
                .all()
            )
            if not moyennes_par_cours:
                continue

            total_pondere, total_coef = 0.0, 0
            details = []
            for id_cours, moyenne in moyennes_par_cours:
                cours_obj = next((c for c in cours_list if c.id == id_cours), None)
                if cours_obj is None:
                    continue
                coef = cours_obj.coefficient_pour_classe(classe.id)
                total_pondere += float(moyenne) * coef
                total_coef    += coef
                details.append((id_cours, round(float(moyenne), 2), coef))

            moyenne_generale = round(total_pondere / total_coef, 2) if total_coef else 0.0
            appreciation = (
                "Excellent"    if moyenne_generale >= 16 else
                "Très bien"    if moyenne_generale >= 14 else
                "Bien"         if moyenne_generale >= 12 else
                "Passable"     if moyenne_generale >= 10 else
                "Insuffisant"
            )

            # Vérifier qu'un bulletin n'existe pas déjà (clé unique eleve+trimestre)
            existant = (
                db.query(models.Bulletins)
                .filter_by(matricule_eleve=eleve.matricule, id_trimestre=trimestre_obj.id)
                .first()
            )
            if existant:
                continue

            bulletin = models.Bulletins(
                matricule_eleve=eleve.matricule,
                id_trimestre=trimestre_obj.id,
                id_classe=classe.id,
                moyenne_generale=moyenne_generale,
                appreciation=appreciation,
            )
            db.add(bulletin)
            db.commit()

            for id_cours, moyenne, coef in details:
                db.add(BulletinDetails(
                    id_bulletin=bulletin.id,
                    id_cours=id_cours,
                    moyenne=moyenne,
                    coefficient=coef,
                ))
            bulletins_classe.append(bulletin)
            total += 1

        # Classement au sein du trimestre
        bulletins_classe.sort(key=lambda b: b.moyenne_generale, reverse=True)
        for rang, bulletin in enumerate(bulletins_classe, start=1):
            bulletin.rang = rang
        db.commit()

    return total


# ──────────────────────────────────────────────────────────────────────────────
# Seed principal
# ──────────────────────────────────────────────────────────────────────────────

def seed_database():
    print("⏳ Purge et réinitialisation de la base de données...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:

        # ── UTILISATEURS (ADMINISTRATION) ───────────────────────────────────
        print("🔐 Création des comptes d'administration...")
        comptes_admin = [
            ("Diarra",    "Admin",      "admin@collegeaureole.ml",      RoleUtilisateur.ADMIN),
            ("Traoré",    "Directeur",  "directeur@collegeaureole.ml",  RoleUtilisateur.DIRECTEUR),
            ("Coulibaly", "Comptable",  "comptable@collegeaureole.ml",  RoleUtilisateur.COMPTABLE),
        ]
        for nom, prenom, email, role in comptes_admin:
            db.add(models.Utilisateurs(
                nom=nom, prenom=prenom, email=email,
                mot_de_passe=hash_password("Password123!"), role=role,
            ))
        db.commit()
        print(f"   ✅ {len(comptes_admin)} comptes créés (mot de passe par défaut : Password123!).")

        # ── ANNÉES SCOLAIRES ────────────────────────────────────────────────
        print("📅 Création des années scolaires (2024-2025 et 2025-2026)...")

        annee_ancienne = models.AnneesScolaires(
            libelle="2024-2025",
            date_debut=date(2024, 10, 1),
            date_fin=date(2025, 7, 31),
            active=False,
        )
        db.add(annee_ancienne)
        db.commit()

        annee_active = models.AnneesScolaires(
            libelle="2025-2026",
            date_debut=date(2025, 10, 1),
            date_fin=date(2026, 7, 31),
            active=True,
        )
        db.add(annee_active)
        db.commit()

        # ── TRIMESTRES ──────────────────────────────────────────────────────
        trimestres_anciens_objets = []
        for nom, debut, fin in TRIMESTRES_ANCIENS:
            t = models.Trimestres(
                nom=nom, date_debut=debut, date_fin=fin,
                annee_scolaire_id=annee_ancienne.id,
            )
            db.add(t)
            db.commit()
            trimestres_anciens_objets.append(t)

        trimestres_actifs_objets = []
        for nom, debut, fin in TRIMESTRES_ACTIFS:
            t = models.Trimestres(
                nom=nom, date_debut=debut, date_fin=fin,
                annee_scolaire_id=annee_active.id,
            )
            db.add(t)
            db.commit()
            trimestres_actifs_objets.append(t)

        print(f"   ✅ 2 années scolaires créées avec {len(trimestres_anciens_objets) + len(trimestres_actifs_objets)} trimestres au total.")

        # ── TUTEURS ──────────────────────────────────────────────────────────
        print(f"👥 Création de {NB_TUTEURS} tuteurs...")
        tuteurs = []
        for _ in range(NB_TUTEURS):
            tuteur = models.Tuteurs(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                email=fake.unique.email(),
                telephone=fake.phone_number(),
                adresse=fake.address().replace("\n", " "),
                profession=random.choice(PROFESSIONS_TUTEURS),
            )
            db.add(tuteur)
            db.commit()
            tuteurs.append(tuteur)
        print(f"   ✅ {len(tuteurs)} tuteurs créés.")

        # ── ENSEIGNANTS ──────────────────────────────────────────────────────
        nb_enseignants = len(EF1) * len(DIVISIONS) + len(MATIERES_EF2)
        print(f"👨‍🏫 Création de {nb_enseignants} enseignants...")
        enseignants = []
        for i in range(nb_enseignants):
            if i < len(EF1) * len(DIVISIONS):
                profession = "Maître d'école (EF1 — polyvalent)"
            else:
                mat_idx = i - len(EF1) * len(DIVISIONS)
                profession = f"Professeur de {MATIERES_EF2[mat_idx % len(MATIERES_EF2)][0]}"
            enseignant = models.Enseignants(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                email=fake.unique.email(),
                telephone=fake.phone_number(),
                adresse=fake.address().replace("\n", " "),
                profession=profession,
            )
            db.add(enseignant)
            db.commit()
            db.refresh(enseignant)
            enseignants.append(enseignant)
        print(f"   ✅ {len(enseignants)} enseignants créés.")

        maitres_ef1 = enseignants[:len(EF1) * len(DIVISIONS)]
        profs_ef2   = enseignants[len(EF1) * len(DIVISIONS):]

        # ── CLASSES ──────────────────────────────────────────────────────────
        nb_classes = len(ANNEES) * len(DIVISIONS)
        print(f"🏫 Création de {nb_classes} classes...")
        classes = []
        classes_par_annee = {}
        for annee in ANNEES:
            classes_par_annee[annee] = []
            for div in DIVISIONS:
                est_ef1 = annee in EF1
                classe = models.Classes(
                    niveau=annee,
                    nom=div,
                    frais_inscription=5_000.0 if est_ef1 else 8_000.0,
                    mensualite=7_000.0 if est_ef1 else 9_500.0,
                )
                db.add(classe)
                db.commit()
                classes.append(classe)
                classes_par_annee[annee].append(classe)
        print(f"   ✅ {len(classes)} classes créées.")

        # ── COURS ────────────────────────────────────────────────────────────
        print("📚 Création des cours...")
        cours_list = []
        maitre_idx = 0

        def _creer_cours_avec_affectations(nom, desc, vh, matricule_enseignant, annees):
            """Crée un cours puis affecte chaque classe des `annees` données, avec
            comme coefficient de pondération (bulletins) le poids horaire de la matière."""
            cours = models.Cours(
                nom=nom,
                description=desc,
                volume_horaire=vh * 30,
                matricule_enseignant=matricule_enseignant,
            )
            db.add(cours)
            db.commit()
            db.refresh(cours)
            for annee in annees:
                for classe_aff in classes_par_annee[annee]:
                    db.add(AffectationCoursClasse(
                        id_classe=classe_aff.id,
                        id_cours=cours.id,
                        coefficient=float(vh),
                    ))
            db.commit()
            return cours

        for nom_m, desc_m, vh in MATIERES_EF1:
            for annee in EF1:
                maitre = maitres_ef1[maitre_idx % len(maitres_ef1)]
                maitre_idx += 1
                cours = _creer_cours_avec_affectations(
                    f"{nom_m} — {annee}", desc_m, vh, maitre.matricule, [annee]
                )
                cours_list.append(cours)

        for i, (nom_m, desc_m, vh) in enumerate(MATIERES_EF2):
            prof = profs_ef2[i % len(profs_ef2)]
            for annee in EF2:
                cours = _creer_cours_avec_affectations(
                    f"{nom_m} — {annee}", desc_m, vh, prof.matricule, [annee]
                )
                cours_list.append(cours)

        print(f"   ✅ {len(cours_list)} cours créés.")

        # ── SALLES ───────────────────────────────────────────────────────────
        print("🚪 Création des salles...")
        salles = []
        salle_par_classe = {}
        for i, classe in enumerate(classes, start=1):
            salle = models.Salles(
                nom=f"Salle {i} ({classe.niveau} {classe.nom})",
                capacite=random.choice([25, 30, 35, 40]),
            )
            db.add(salle)
            db.commit()
            db.refresh(salle)
            salles.append(salle)
            salle_par_classe[classe.id] = salle
        print(f"   ✅ {len(salles)} salles créées.")

        # ── SÉANCES (EMPLOI DU TEMPS) ─────────────────────────────────────
        print("📅 Génération des séances de cours (emploi du temps 2024-2025 et 2025-2026)...")
        total_seances = 0

        for annee_obj in [annee_ancienne, annee_active]:
            for classe in classes:
                salle_classe = salle_par_classe[classe.id]
                cours_de_la_classe = [c for c in cours_list if classe.id in [cls.id for cls in c.classes]]
                idx_cours = 0
                for jour in JOURS_SEMAINE:
                    for debut, fin in CRENEAUX_HORAIRES:
                        if idx_cours >= len(cours_de_la_classe):
                            break
                        co = cours_de_la_classe[idx_cours]
                        db.add(models.Seances(
                            id_cours=co.id,
                            id_classe=classe.id,
                            id_annee_scolaire=annee_obj.id,
                            id_salle=salle_classe.id,
                            jour_semaine=jour,
                            heure_debut=debut,
                            heure_fin=fin,
                        ))
                        total_seances += 1
                        idx_cours += 1
            db.commit()

        print(f"   ✅ {total_seances} séances d'emploi du temps créées (2 années).")

        # ── ÉLÈVES & INSCRIPTIONS (multi-années) ──────────────────────────
        print(f"👶 Création de {NB_ELEVES} élèves avec inscriptions (certains sur 2 années)...")

        eleves                 = []
        inscriptions_actives   = []   # inscriptions année 2025-2026
        inscriptions_anciennes = []  # inscriptions année 2024-2025

        classe_pool = (classes * (NB_ELEVES // len(classes) + 1))[:NB_ELEVES]
        random.shuffle(classe_pool)

        nb_multi_annees = 0

        for i in range(NB_ELEVES):
            date_naiss     = fake.date_of_birth(minimum_age=6, maximum_age=16)
            cible_classe   = classe_pool[i]
            niveau_actuel  = cible_classe.niveau

            eleve = models.Eleves(
                nom=fake.last_name(),
                prenom=fake.first_name(),
                photo=None,
                date_de_naissance=date_naiss.isoformat(),
                lieu_de_naissance=fake.city(),
                sexe=random.choice(["M", "F"]),
                adresse=fake.address().replace("\n", " "),
                tuteur_id=random.choice(tuteurs).id,
                classe_id=cible_classe.id,
                statut="actif",
            )
            db.add(eleve)
            db.commit()
            db.refresh(eleve)
            eleves.append(eleve)

            # ── Inscription année active (2025-2026) ──
            montant_actuel = FRAIS_EF1 if niveau_actuel in EF1 else FRAIS_EF2
            a_historique   = random.random() < PROBA_HISTORIQUE_ANCIEN

            if a_historique:
                statut_ancien_passage = random.choices(["ADMIS", "RECALE"], weights=[80, 20], k=1)[0]
                statut_inscription_active = "Redoublant" if statut_ancien_passage == "RECALE" else "Inscrit"
            else:
                statut_inscription_active = "Inscrit"
                statut_ancien_passage = None

            insc_active = models.Inscriptions(
                matricule_eleve=eleve.matricule,
                id_classe=cible_classe.id,
                id_annee_scolaire=annee_active.id,
                statut=statut_inscription_active,
                statut_passage="EN_ATTENTE",
                montant_total=float(montant_actuel),
                date_inscription=annee_active.date_debut,
                date_fin=None,
                observation=None,
            )
            db.add(insc_active)
            db.commit()
            db.refresh(insc_active)
            _generer_echeances_seed(db, insc_active, annee_active.date_debut)
            db.commit()
            inscriptions_actives.append(insc_active)

            # ── Inscription année précédente (2024-2025) ──
            if a_historique:
                nb_multi_annees += 1

                if statut_ancien_passage == "RECALE":
                    niveau_ancien = niveau_actuel
                else:
                    niveau_ancien = niveau_precedent(niveau_actuel) or niveau_actuel

                classe_ancienne = random.choice(classes_par_annee[niveau_ancien])
                montant_ancien  = FRAIS_EF1 if niveau_ancien in EF1 else FRAIS_EF2

                insc_ancienne = models.Inscriptions(
                    matricule_eleve=eleve.matricule,
                    id_classe=classe_ancienne.id,
                    id_annee_scolaire=annee_ancienne.id,
                    statut=random.choices(
                        ["Inscrit", "Redoublant"], weights=[85, 15], k=1
                    )[0],
                    statut_passage=statut_ancien_passage,
                    montant_total=float(montant_ancien),
                    date_inscription=annee_ancienne.date_debut,
                    date_fin=annee_ancienne.date_fin,
                    observation=(
                        "Passage validé — admis en classe supérieure."
                        if statut_ancien_passage == "ADMIS"
                        else "Résultats insuffisants — redoublement prononcé."
                    ),
                )
                db.add(insc_ancienne)
                db.commit()
                db.refresh(insc_ancienne)
                _generer_echeances_seed(db, insc_ancienne, annee_ancienne.date_debut)
                db.commit()
                inscriptions_anciennes.append((eleve, insc_ancienne, classe_ancienne, niveau_ancien))

            if (i + 1) % 90 == 0:
                print(f"   ... {i + 1}/{NB_ELEVES} élèves insérés")

        print(f"   ✅ {len(eleves)} élèves créés.")
        print(f"   📚 {nb_multi_annees} élèves ont un historique sur 2 années scolaires.")

        # ── GÉNÉRATION DES PLANNINGS D'ÉVALUATIONS ─────────────────────
        print("🗓️ Préparation du planning des évaluations...")
        planning_actifs   = generer_planning_evaluations(cours_list, trimestres_actifs_objets, TRIMESTRES_ACTIFS)
        planning_anciens  = generer_planning_evaluations(cours_list, trimestres_anciens_objets, TRIMESTRES_ANCIENS)

        # ── NOTES — ANNÉE ACTIVE (2025-2026) ─────────────────────────────
        print("📝 Génération des notes — année active 2025-2026...")
        total_notes = 0
        for idx, el in enumerate(eleves):
            cours_eleve = [c for c in cours_list if el.classe_id in [cls.id for cls in c.classes]]
            total_notes += generer_notes_pour_eleve(
                db, el, el.classe_id, cours_eleve,
                trimestres_actifs_objets, planning_actifs
            )
            if (idx + 1) % 30 == 0:
                db.commit()
                print(f"   ... {total_notes} notes insérées ({idx + 1}/{NB_ELEVES} élèves)")
        db.commit()
        print(f"   ✅ {total_notes} notes créées pour 2025-2026.")

        # ── NOTES — ANNÉE ANCIENNE (2024-2025) ───────────────────────────
        print("📝 Génération des notes — année ancienne 2024-2025...")
        total_notes_anciens = 0
        for el, insc_anc, classe_anc, niveau_anc in inscriptions_anciennes:
            cours_anciens = [c for c in cours_list if classe_anc.id in [cls.id for cls in c.classes]]
            total_notes_anciens += generer_notes_pour_eleve(
                db, el, classe_anc.id, cours_anciens,
                trimestres_anciens_objets, planning_anciens
            )
            if total_notes_anciens % 5000 < NB_NOTES_PAR_COURS * 3:
                db.commit()
        db.commit()
        print(f"   ✅ {total_notes_anciens} notes créées pour 2024-2025.")

        # ── BULLETINS — ANNÉE ACTIVE (3 trimestres) ──────────────────────
        print("🧾 Génération des bulletins — année active 2025-2026 (3 trimestres)...")
        total_bulletins = 0
        for classe in classes:
            eleves_classe = [e for e in eleves if e.classe_id == classe.id]
            total_bulletins += generer_bulletins_pour_classe(
                db, classe, eleves_classe,
                cours_list, trimestres_actifs_objets
            )
        print(f"   ✅ {total_bulletins} bulletins générés pour 2025-2026.")

        # ── BULLETINS — ANNÉE ANCIENNE (3 trimestres) ───────────────────
        print("🧾 Génération des bulletins — année ancienne 2024-2025 (3 trimestres)...")
        total_bulletins_anciens = 0

        classes_anciennes_map: dict[int, list] = {}
        for el, insc_anc, classe_anc, niveau_anc in inscriptions_anciennes:
            classes_anciennes_map.setdefault(classe_anc.id, []).append(el)

        for classe_id, eleves_anciens in classes_anciennes_map.items():
            classe_obj = next(c for c in classes if c.id == classe_id)
            total_bulletins_anciens += generer_bulletins_pour_classe(
                db, classe_obj, eleves_anciens,
                cours_list, trimestres_anciens_objets
            )
        print(f"   ✅ {total_bulletins_anciens} bulletins générés pour 2024-2025.")

        # ── ABSENCES ─────────────────────────────────────────────────────
        print("📋 Génération des absences (années active + ancienne)...")
        aujourdhui = date.today()
        total_absences = 0

        periodes_actives = [
            (nom, debut, min(fin, aujourdhui))
            for nom, debut, fin in TRIMESTRES_ACTIFS
            if debut <= aujourdhui
        ]
        periodes_anciennes = list(TRIMESTRES_ANCIENS)

        for idx, el in enumerate(eleves):
            nb_abs = random.choices(
                [0, 1, 2, 3, 4, 5, 6, 7, 8],
                weights=[30, 20, 15, 12, 10, 6, 4, 2, 1], k=1
            )[0]
            for _ in range(nb_abs):
                if not periodes_actives:
                    break
                _, debut_p, fin_p = random.choice(periodes_actives)
                justifiee = random.random() < PROBA_ABSENCE_JUSTIFIEE
                db.add(models.Absences(
                    matricule_eleve=el.matricule,
                    date_absence=fake.date_between(start_date=debut_p, end_date=fin_p),
                    justifiee=justifiee,
                    motif=random.choice(MOTIFS_ABSENCE_JUSTIFIEE) if justifiee else None,
                ))
                total_absences += 1

            if (idx + 1) % 90 == 0:
                db.commit()
                print(f"   ... {total_absences} absences insérées ({idx + 1}/{NB_ELEVES} élèves)")

        for el, insc_anc, classe_anc, niveau_anc in inscriptions_anciennes:
            nb_abs = random.choices(
                [0, 1, 2, 3, 4, 5, 6, 7, 8],
                weights=[30, 20, 15, 12, 10, 6, 4, 2, 1], k=1
            )[0]
            for _ in range(nb_abs):
                _, debut_p, fin_p = random.choice(periodes_anciennes)
                justifiee = random.random() < PROBA_ABSENCE_JUSTIFIEE
                db.add(models.Absences(
                    matricule_eleve=el.matricule,
                    date_absence=fake.date_between(start_date=debut_p, end_date=fin_p),
                    justifiee=justifiee,
                    motif=random.choice(MOTIFS_ABSENCE_JUSTIFIEE) if justifiee else None,
                ))
                total_absences += 1

        db.commit()
        print(f"   ✅ {total_absences} absences générées.")

        # ── PAIEMENTS ────────────────────────────────────────────────────
        print("💰 Génération des paiements — toutes les inscriptions...")
        total_paiements      = 0
        montant_total_collecte = 0.0

        for idx, insc in enumerate(inscriptions_actives):
            nb_p, montant_p = generer_paiements(
                db, insc,
                annee_active.date_debut, annee_active.date_fin,
                MODES_PAIEMENT
            )
            total_paiements       += nb_p
            montant_total_collecte += montant_p
            if (idx + 1) % 90 == 0:
                db.commit()

        for el, insc_anc, classe_anc, niveau_anc in inscriptions_anciennes:
            nb_p, montant_p = generer_paiements(
                db, insc_anc,
                annee_ancienne.date_debut, annee_ancienne.date_fin,
                MODES_PAIEMENT
            )
            total_paiements       += nb_p
            montant_total_collecte += montant_p

        db.commit()
        print(f"   ✅ {total_paiements} paiements générés — {montant_total_collecte:,.0f} FCFA collectés au total.")

        # ── RÉSUMÉ ───────────────────────────────────────────────────────
        print()
        print("🎉 Base de données peuplée avec succès !")
        print("   • Années scolaires : 2 (2024-2025 archivée, 2025-2026 active)")
        print(f"   • Élèves           : {len(eleves)}")
        print(f"   • Multi-années     : {nb_multi_annees} élèves inscrits sur les 2 années")
        print(f"   • Trimestres       : {len(trimestres_anciens_objets) + len(trimestres_actifs_objets)} (3 par année)")
        print(f"   • Salles           : {len(salles)}")
        print(f"   • Notes            : {total_notes + total_notes_anciens}")
        print(f"   • Bulletins        : {total_bulletins + total_bulletins_anciens} (3 trimestres × chaque classe)")
        print(f"   • Absences         : {total_absences}")
        print(f"   • Paiements        : {total_paiements}")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur rencontrée : {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()