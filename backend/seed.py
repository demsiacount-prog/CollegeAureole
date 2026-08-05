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
from bareme import bareme_niveau

fake = Faker("fr_FR")

# Système scolaire malien
# 1ère → 6ème année  : Enseignement Fondamental 1er cycle (EF1) → Compositions
# 7ème → 9ème année  : Enseignement Fondamental 2ème cycle (EF2) → Trimestres

NB_TUTEURS              = 220
NB_ELEVES               = 450
NB_NOTES_PAR_COURS      = 3
PROBA_ABSENCE_JUSTIFIEE = 0.4

FRAIS_EF1 = 75_000
FRAIS_EF2 = 95_000

MODES_PAIEMENT = ["Espèces", "Mobile Money", "Chèque", "Virement"]

ANNEES = [
    "1ère Année", "2ème Année", "3ème Année",
    "4ème Année", "5ème Année", "6ème Année",
    "7ème Année", "8ème Année", "9ème Année",
]

DIVISIONS = ["A"]

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

COMPOSITIONS = [
    ("Composition 1",  date(2025, 10, 1),   date(2025, 10, 17)),
    ("Composition 2",  date(2025, 10, 27),  date(2025, 11, 14)),
    ("Composition 3",  date(2025, 11, 24),  date(2025, 12, 12)),
    ("Composition 4",  date(2026, 1, 5),    date(2026, 1, 23)),
    ("Composition 5",  date(2026, 2, 2),    date(2026, 2, 20)),
    ("Composition 6",  date(2026, 3, 2),    date(2026, 3, 20)),
    ("Composition 7",  date(2026, 4, 6),    date(2026, 4, 24)),
    ("Composition 8",  date(2026, 5, 4),    date(2026, 5, 22)),
    ("Composition 9",  date(2026, 6, 1),    date(2026, 6, 30)),
]

TRIMESTRES = [
    ("Trimestre 1", date(2025, 10, 1),  date(2025, 12, 20)),
    ("Trimestre 2", date(2026, 1, 5),   date(2026, 3, 31)),
    ("Trimestre 3", date(2026, 4, 6),   date(2026, 7, 31)),
]

PROFESSIONS_TUTEURS = [
    "Cultivateur", "Commerçant(e)", "Fonctionnaire", "Enseignant(e)", "Artisan",
    "Mécanicien", "Couturier(ère)", "Infirmier(e)", "Chauffeur", "Maçon",
    "Forgeron", "Pêcheur", "Éleveur", "Menuisier", "Agent de sécurité",
    "Boutiquier", "Tailleur", "Sage-femme", "Électricien", "Plombier",
    "Médecin", "Pharmacien(ne)", "Comptable", "Juriste", "Militaire",
]

MOTIFS_ABSENCE = [
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
    frais_insc = getattr(classe, 'frais_inscription', 0.0) or 0.0
    mensualite = getattr(classe, 'mensualite', 0.0) or 0.0
    annee_int  = annee_debut.year

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


def generer_paiements(db, inscription, annee_debut, annee_fin, modes):
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
    else:
        nb_v = random.choice([1, 2])
        fraction = random.uniform(0.2, 0.7)
        montant_paye = round(montant_du * fraction, 0)
        versements = [montant_paye] if nb_v == 1 else [
            round(montant_paye * random.uniform(0.4, 0.6), 0),
            montant_paye - round(montant_paye * random.uniform(0.4, 0.6), 0),
        ]

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
                numero_recu=f"REC-{annee_debut.year}-{inscription.id:05d}-{num}",
                montant=sur_ech, mode=random.choice(modes), observation=None,
            ))
            ech.montant_paye += sur_ech
            _mettre_a_jour_statut_echeance(ech)
            reste -= sur_ech
        total_paiements += 1
        total_montant   += float(montant_v)

    return total_paiements, total_montant


def generer_planning_evaluations(cours_list, periodes):
    planning = {}
    for co in cours_list:
        for nom, date_debut, date_fin, trim_obj in periodes:
            planning[(co.id, trim_obj.id)] = fake.date_between(start_date=date_debut, end_date=date_fin)
    return planning


def generer_notes_pour_eleve(db, eleve, id_classe_courante, cours_eleve, periodes, planning, classe_niveau: str = ""):
    total = 0
    bareme = bareme_niveau(classe_niveau)
    for co in cours_eleve:
        for _, _, _, trim_obj in periodes:
            date_eval = planning.get((co.id, trim_obj.id))
            if date_eval is None:
                continue
            db.add(models.Notes(
                date=date_eval,
                note=round(random.uniform(0.0, float(bareme)), 2),
                matricule_eleve=eleve.matricule,
                id_cours=co.id,
                id_classe=id_classe_courante,
                matricule_enseignant=co.matricule_enseignant,
                id_trimestre=trim_obj.id,
            ))
            total += 1
    return total


def generer_bulletins_pour_classe(db, classe, eleves_classe, cours_list, periodes):
    from sqlalchemy import func as _func
    total = 0
    cours_par_id = {c.id: c for c in cours_list}
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

            total_pondere, total_coef = 0.0, 0
            details = []
            for id_cours, moyenne in moyennes_par_cours:
                coef = coef_map.get((id_cours, classe.id), 1.0)
                total_pondere += float(moyenne) * coef
                total_coef    += coef
                details.append((id_cours, round(float(moyenne), 2), coef))

            if total_coef == 0:
                continue

            moyenne_generale = round(total_pondere / total_coef, 2)
            appreciation = (
                "Excellent"    if moyenne_generale >= 16 else
                "Très bien"    if moyenne_generale >= 14 else
                "Bien"         if moyenne_generale >= 12 else
                "Passable"     if moyenne_generale >= 10 else
                "Insuffisant"
            )

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


# ── MAIN SEED ──────────────────────────────────────────────────────────────────

def seed_database():
    print("Purge et réinitialisation de la base de données...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # ── UTILISATEURS ──────────────────────────────────────────────────────
        print("Création des comptes d'administration...")
        comptes = [
            ("Diarra",    "Admin",      "admin@collegeaureole.ml",      RoleUtilisateur.ADMIN),
            ("Traoré",    "Directeur",  "directeur@collegeaureole.ml",  RoleUtilisateur.DIRECTEUR),
            ("Coulibaly", "Comptable",  "comptable@collegeaureole.ml",  RoleUtilisateur.COMPTABLE),
        ]
        for nom, prenom, email, role in comptes:
            db.add(models.Utilisateurs(
                nom=nom, prenom=prenom, email=email,
                mot_de_passe=hash_password("Password123!"), role=role,
            ))
        db.commit()
        print(f"   {len(comptes)} comptes créés (mot de passe : Password123!).")

        # ── ANNÉE SCOLAIRE UNIQUE ────────────────────────────────────────────
        print("Création de l'année scolaire 2025-2026...")
        annee = models.AnneesScolaires(
            libelle="2025-2026",
            date_debut=date(2025, 10, 1),
            date_fin=date(2026, 7, 31),
            active=True,
        )
        db.add(annee)
        db.commit()

        # ── PÉRIODES (trimestres + compositions) ─────────────────────────────
        print("Création des périodes d'évaluation...")
        periodes_ef1 = []
        for nom, debut, fin in COMPOSITIONS:
            t = models.Trimestres(
                nom=nom, date_debut=debut, date_fin=fin,
                type="COMPOSITION", annee_scolaire_id=annee.id,
            )
            db.add(t)
            db.flush()
            periodes_ef1.append((nom, debut, fin, t))

        periodes_ef2 = []
        for nom, debut, fin in TRIMESTRES:
            t = models.Trimestres(
                nom=nom, date_debut=debut, date_fin=fin,
                type="TRIMESTRE", annee_scolaire_id=annee.id,
            )
            db.add(t)
            db.flush()
            periodes_ef2.append((nom, debut, fin, t))
        db.commit()

        total_periodes = periodes_ef1 + periodes_ef2
        print(f"   {len(total_periodes)} périodes créées ({len(periodes_ef1)} compositions + {len(periodes_ef2)} trimestres).")

        # ── TUTEURS ───────────────────────────────────────────────────────────
        print(f"Création de {NB_TUTEURS} tuteurs...")
        tuteurs = []
        for _ in range(NB_TUTEURS):
            t = models.Tuteurs(
                nom=fake.last_name(), prenom=fake.first_name(),
                email=fake.unique.email(), telephone=fake.phone_number(),
                adresse=fake.address().replace("\n", " "),
                profession=random.choice(PROFESSIONS_TUTEURS),
            )
            db.add(t)
            db.flush()
            tuteurs.append(t)
        db.commit()
        print(f"   {len(tuteurs)} tuteurs créés.")

        # ── ENSEIGNANTS ──────────────────────────────────────────────────────
        nb_ens = len(EF1) * len(DIVISIONS) + len(MATIERES_EF2)
        print(f"Création de {nb_ens} enseignants...")
        enseignants = []
        for i in range(nb_ens):
            if i < len(EF1) * len(DIVISIONS):
                specialite = "Maître d'école (EF1 — polyvalent)"
            else:
                mat_idx = i - len(EF1) * len(DIVISIONS)
                specialite = f"Professeur de {MATIERES_EF2[mat_idx % len(MATIERES_EF2)][0]}"
            e = models.Enseignants(
                nom=fake.last_name(), prenom=fake.first_name(),
                email=fake.unique.email(), telephone=fake.phone_number(),
                adresse=fake.address().replace("\n", " "),
                specialite=specialite,
            )
            db.add(e)
            db.flush()
            enseignants.append(e)
        db.commit()
        print(f"   {len(enseignants)} enseignants créés.")

        maitres_ef1 = enseignants[:len(EF1) * len(DIVISIONS)]
        profs_ef2   = enseignants[len(EF1) * len(DIVISIONS):]

        # ── CLASSES ───────────────────────────────────────────────────────────
        print("Création des classes...")
        classes = []
        classes_par_niveau = {}
        for niveau in ANNEES:
            classes_par_niveau[niveau] = []
            for div in DIVISIONS:
                est_ef1 = niveau in EF1
                classe = models.Classes(
                    niveau=niveau, nom=div,
                    frais_inscription=5_000.0 if est_ef1 else 8_000.0,
                    mensualite=7_000.0 if est_ef1 else 9_500.0,
                )
                db.add(classe)
                db.flush()
                classes.append(classe)
                classes_par_niveau[niveau].append(classe)
        db.commit()
        print(f"   {len(classes)} classes créées.")

        # ── COURS ────────────────────────────────────────────────────────────
        print("Création des cours...")
        cours_list = []
        maitre_idx = 0

        def creer_cours(nom, desc, vh, matr_ens, niveau):
            c = models.Cours(
                nom=nom, description=desc,
                volume_horaire=vh * 30,
                matricule_enseignant=matr_ens,
            )
            db.add(c)
            db.flush()
            for classe_aff in classes_par_niveau[niveau]:
                db.add(AffectationCoursClasse(
                    id_classe=classe_aff.id, id_cours=c.id,
                    coefficient=float(vh),
                ))
            db.flush()
            return c

        for nom_m, desc_m, vh in MATIERES_EF1:
            for niveau in EF1:
                maitre = maitres_ef1[maitre_idx % len(maitres_ef1)]
                maitre_idx += 1
                cours_list.append(creer_cours(
                    f"{nom_m} — {niveau}", desc_m, vh, maitre.matricule, niveau
                ))

        for i, (nom_m, desc_m, vh) in enumerate(MATIERES_EF2):
            prof = profs_ef2[i % len(profs_ef2)]
            for niveau in EF2:
                cours_list.append(creer_cours(
                    f"{nom_m} — {niveau}", desc_m, vh, prof.matricule, niveau
                ))
        db.commit()
        print(f"   {len(cours_list)} cours créés.")

        # ── SALLES ────────────────────────────────────────────────────────────
        print("Création des salles...")
        salles = []
        salle_par_classe = {}
        for i, classe in enumerate(classes, start=1):
            salle = models.Salles(
                nom=f"Salle {i} ({classe.niveau} {classe.nom})",
                capacite=random.choice([25, 30, 35, 40]),
            )
            db.add(salle)
            db.flush()
            salles.append(salle)
            salle_par_classe[classe.id] = salle
        db.commit()
        print(f"   {len(salles)} salles créées.")

        # ── SÉANCES ──────────────────────────────────────────────────────────
        print("Génération de l'emploi du temps...")
        total_seances = 0
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
                        id_cours=co.id, id_classe=classe.id,
                        id_annee_scolaire=annee.id,
                        id_salle=salle_classe.id,
                        jour_semaine=jour, heure_debut=debut, heure_fin=fin,
                    ))
                    total_seances += 1
                    idx_cours += 1
            db.commit()
        print(f"   {total_seances} séances créées.")

        # ── ÉLÈVES & INSCRIPTIONS ────────────────────────────────────────────
        print(f"Création de {NB_ELEVES} élèves...")
        eleves = []
        inscriptions = []

        classe_pool = (classes * (NB_ELEVES // len(classes) + 1))[:NB_ELEVES]
        random.shuffle(classe_pool)

        for i in range(NB_ELEVES):
            date_naiss = fake.date_of_birth(minimum_age=6, maximum_age=16)
            cible = classe_pool[i]
            niveau_actuel = cible.niveau
            montant = FRAIS_EF1 if niveau_actuel in EF1 else FRAIS_EF2

            eleve = models.Eleves(
                nom=fake.last_name(), prenom=fake.first_name(),
                date_de_naissance=date_naiss.isoformat(),
                lieu_de_naissance=fake.city(),
                sexe=random.choice(["M", "F"]),
                adresse=fake.address().replace("\n", " "),
                tuteur_id=random.choice(tuteurs).id,
                classe_id=cible.id, statut="actif",
            )
            # Transitoire : année d'inscription pour le matricule EL (voir eleves.py)
            eleve.annee_scolaire_id = annee.id
            db.add(eleve)
            db.flush()
            eleves.append(eleve)

            insc = models.Inscriptions(
                matricule_eleve=eleve.matricule, id_classe=cible.id,
                id_annee_scolaire=annee.id, statut="Inscrit",
                statut_passage="EN_ATTENTE", montant_total=float(montant),
                date_inscription=annee.date_debut,
            )
            db.add(insc)
            db.flush()
            _generer_echeances(db, insc, annee.date_debut)
            inscriptions.append(insc)

            if (i + 1) % 90 == 0:
                db.commit()
                print(f"   ... {i + 1}/{NB_ELEVES} élèves insérés")
        db.commit()

        print(f"   {len(eleves)} élèves créés.")

        # ── PLANNING DES ÉVALUATIONS ─────────────────────────────────────────
        print("Planification des évaluations...")
        planning = generer_planning_evaluations(cours_list, total_periodes)

        # ── NOTES ────────────────────────────────────────────────────────────
        print("Génération des notes...")
        total_notes = 0
        classes_map = {c.id: c.niveau for c in classes}
        for idx, el in enumerate(eleves):
            cours_eleve = [c for c in cours_list if el.classe_id in [cls.id for cls in c.classes]]
            total_notes += generer_notes_pour_eleve(
                db, el, el.classe_id, cours_eleve,
                periodes_pour_niveau(classes_map.get(el.classe_id, ""), periodes_ef1, periodes_ef2),
                planning,
                classe_niveau=classes_map.get(el.classe_id, ""),
            )
            if (idx + 1) % 30 == 0:
                db.commit()
                print(f"   ... {total_notes} notes insérées ({idx + 1}/{NB_ELEVES} élèves)")
        db.commit()
        print(f"   {total_notes} notes créées.")

        # ── BULLETINS ─────────────────────────────────────────────────────────
        print("Génération des bulletins...")
        total_bulletins = 0
        for classe in classes:
            eleves_classe = [e for e in eleves if e.classe_id == classe.id]
            total_bulletins += generer_bulletins_pour_classe(
                db, classe, eleves_classe, cours_list,
                periodes_pour_niveau(classe.niveau, periodes_ef1, periodes_ef2),
            )
        print(f"   {total_bulletins} bulletins générés.")

        # ── ABSENCES ─────────────────────────────────────────────────────────
        print("Génération des absences...")
        aujourdhui = date.today()
        total_absences = 0
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
            nb_abs = random.choices(
                [0, 1, 2, 3, 4, 5, 6, 7, 8],
                weights=[30, 20, 15, 12, 10, 6, 4, 2, 1], k=1
            )[0]
            for _ in range(nb_abs):
                if not periodes_abs:
                    break
                _, debut_p, fin_p = random.choice(periodes_abs)
                justifiee = random.random() < PROBA_ABSENCE_JUSTIFIEE
                db.add(models.Absences(
                    matricule_eleve=el.matricule,
                    id_cours=random.choice(cours_classe).id if cours_classe else None,
                    date_absence=fake.date_between(start_date=debut_p, end_date=fin_p),
                    justifiee=justifiee,
                    motif=random.choice(MOTIFS_ABSENCE) if justifiee else None,
                ))
                total_absences += 1
            if (idx + 1) % 90 == 0:
                db.commit()
                print(f"   ... {total_absences} absences insérées ({idx + 1}/{NB_ELEVES} élèves)")
        db.commit()
        print(f"   {total_absences} absences générées.")

        # ── PAIEMENTS ─────────────────────────────────────────────────────────
        print("Génération des paiements...")
        total_paiements = 0
        montant_collecte = 0.0
        for idx, insc in enumerate(inscriptions):
            nb_p, montant_p = generer_paiements(
                db, insc, annee.date_debut, annee.date_fin, MODES_PAIEMENT
            )
            total_paiements   += nb_p
            montant_collecte  += montant_p
            if (idx + 1) % 90 == 0:
                db.commit()
        db.commit()
        print(f"   {total_paiements} paiements — {montant_collecte:,.0f} FCFA collectés.")

        # ── DÉPENSES ──────────────────────────────────────────────────────────
        print("Génération des dépenses...")
        depenses_seed = [
            ("Fournitures de bureau",     "FOURNITURES",  "Rames de papier, stylos et classeurs"),
            ("Matériel pédagogique",      "MATERIEL",     "Manuels et cahiers d'exercices des élèves"),
            ("Entretien de la plomberie", "ENTRETIEN",    "Réparation du bloc sanitaire du bâtiment B"),
            ("Facture d'électricité",     "ELECTRICITE",  "Électricité du mois du collège"),
            ("Facture d'eau",             "EAU",          "Eau de la cantine scolaire"),
            ("Tables-bancs de 6e A",      "MATERIEL",     "Mobiliers scolaires pour la salle de 6e A"),
            ("Cartouches d'imprimante",   "COMMUNICATION","Entretien du secrétariat"),
            ("Matériel sportif",          "MATERIEL",     "Ballons et chasubles pour l'EPS"),
            ("Carburant sorties scolaires","TRANSPORT",   "Sorties pédagogiques"),
            ("Trousse de premiers secours","ALIMENTATION","Pharmacie de l'infirmerie"),
        ]
        for libelle, categorie, description in depenses_seed:
            db.add(models.Depenses(
                libelle=libelle,
                montant=round(random.uniform(15_000, 250_000), 0),
                categorie=categorie,
                date=fake.date_between(start_date=annee.date_debut, end_date=date.today()),
                description=description,
            ))
        db.commit()
        print(f"   {len(depenses_seed)} dépenses créées.")

        # ── RÉSUMÉ ────────────────────────────────────────────────────────────
        print()
        print("Base de données peuplée avec succès !")
        print(f"   Année scolaire : 2025-2026 (active)")
        print(f"   Périodes       : {len(total_periodes)} ({len(periodes_ef1)} compositions EF1 + {len(periodes_ef2)} trimestres EF2)")
        print(f"   Élèves         : {len(eleves)}")
        print(f"   Enseignants    : {len(enseignants)}")
        print(f"   Salles         : {len(salles)}")
        print(f"   Notes          : {total_notes}")
        print(f"   Bulletins      : {total_bulletins}")
        print(f"   Absences       : {total_absences}")
        print(f"   Paiements      : {total_paiements} — {montant_collecte:,.0f} FCFA")

    except Exception as e:
        db.rollback()
        print(f"Erreur : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
