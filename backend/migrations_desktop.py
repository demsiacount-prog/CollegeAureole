"""Migrations légères pour le mode desktop (SQLite).

`Base.metadata.create_all()` ne modifie jamais un schéma existant : cette
fonction comble le fossé pour les évolutions de modèle ajoutées après la
première installation, de façon idempotente. Les bases PostgreSQL (production)
suivent les révisions Alembic dans /alembic.
"""
import logging
from datetime import date, datetime

from sqlalchemy import inspect, text
from database import engine, SessionLocal, Base

logger = logging.getLogger("college_aureole")


def migrer_sqlite():
    if not engine.url.drivername.startswith("sqlite"):
        return

    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    # Ajouts de colonnes : plusieurs opérations par table sont possibles.
    for table, operations in _ALTERS.items():
        if table not in tables:
            continue
        colonnes = {c["name"] for c in inspector.get_columns(table)}
        for colonne, alter_sql, index_sql, backfill in operations:
            ajoutee = False
            if colonne and colonne not in colonnes and alter_sql:
                with engine.begin() as conn:
                    conn.execute(text(alter_sql))
                ajoutee = True
                logger.info("Migration SQLite : colonne %s.%s ajoutée.", table, colonne)
            if index_sql:
                with engine.begin() as conn:
                    conn.execute(text(index_sql))
            if ajoutee and backfill:
                backfill(table)

    # Suppressions de colonnes (SQLite ≥ 3.35).
    for table, colonne, drop_sql in _DROPS:
        if table not in tables:
            continue
        colonnes = {c["name"] for c in inspector.get_columns(table)}
        if colonne in colonnes:
            with engine.begin() as conn:
                conn.execute(text(drop_sql))
            logger.info("Migration SQLite : colonne %s.%s supprimée.", table, colonne)

    # Documents : nouvelle forme (BLOB + entités multiples + matricule_eleve
    # nullable pour les uploads enseignant/tuteur). SQLite ne permet pas de
    # retirer NOT NULL par ALTER : la table est reconstruite, puis le contenu
    # des anciens fichiers disque est chargé en base.
    _migrer_documents()

    # Paiements à montant nul (échéances déjà soldées) : invalides, ils
    # bloquaient la sérialisation des dossiers élèves. Neutre financièrement.
    _nettoyer_paiements_zero()


def _attribuer_codes(db, rows, groupe, prefixe, colonne):
    """Attribue {préfixe}{année:02d}{compteur:05d}, compteur par année."""
    compteurs = {}
    for row in rows:
        annee = groupe(row)
        compteurs[annee] = compteurs.get(annee, 0) + 1
        setattr(row, colonne, f"{prefixe}{annee:02d}{compteurs[annee]:05d}")


def _annee_inscription(db, id_inscription):
    from models.inscriptions import Inscriptions
    from models.annees_scolaires import AnneesScolaires

    annee = (
        db.query(AnneesScolaires.date_debut)
        .join(Inscriptions, Inscriptions.id_annee_scolaire == AnneesScolaires.id)
        .filter(Inscriptions.id == id_inscription)
        .scalar()
    )
    return (annee.year if annee else date.today().year) % 100


def _annee_scolaire(db, id_annee_scolaire):
    from models.annees_scolaires import AnneesScolaires

    annee = db.query(AnneesScolaires.date_debut).filter(AnneesScolaires.id == id_annee_scolaire).scalar()
    return (annee.year if annee else date.today().year) % 100


def _annee_pour_date(db, date_valeur):
    from models.annees_scolaires import AnneesScolaires

    annee = (
        db.query(AnneesScolaires.date_debut)
        .filter(
            AnneesScolaires.date_debut <= date_valeur,
            AnneesScolaires.date_fin >= date_valeur,
        )
        .order_by(AnneesScolaires.date_debut.desc())
        .first()
    )
    return (annee.year if annee else date.today().year) % 100


def _backfill_inscriptions(table=None):
    from models.inscriptions import Inscriptions

    with SessionLocal() as db:
        rows = (
            db.query(Inscriptions)
            .filter(Inscriptions.code_inscription.is_(None))
            .order_by(Inscriptions.id_annee_scolaire, Inscriptions.id)
            .all()
        )
        if not rows:
            return
        _attribuer_codes(db, rows, lambda r: _annee_scolaire(db, r.id_annee_scolaire), "INS", "code_inscription")
        db.commit()
        logger.info("Migration SQLite : %d code(s) d'inscription attribué(s).", len(rows))


def _backfill_paiements(table=None):
    from models.paiements import Paiements

    with SessionLocal() as db:
        rows = (
            db.query(Paiements)
            .filter(Paiements.code_paiement.is_(None))
            .order_by(Paiements.id)
            .all()
        )
        if not rows:
            return
        _attribuer_codes(db, rows, lambda r: _annee_inscription(db, r.id_inscription), "PAI", "code_paiement")
        db.commit()
        logger.info("Migration SQLite : %d code(s) de paiement attribué(s).", len(rows))


def _backfill_depenses(table=None):
    from models.depenses import Depenses

    with SessionLocal() as db:
        rows = (
            db.query(Depenses)
            .filter(Depenses.code_depense.is_(None))
            .order_by(Depenses.date, Depenses.id)
            .all()
        )
        if not rows:
            return
        _attribuer_codes(db, rows, lambda r: _annee_pour_date(db, r.date), "DEP", "code_depense")
        db.commit()
        logger.info("Migration SQLite : %d code(s) de dépense attribué(s).", len(rows))


def _backfill_globaux(table):
    """Cours, tuteurs, classes, salles : compteur global, année de la migration.

    Ne traite que la table dont la colonne vient d'être ajoutée : à ce stade
    les colonnes des autres tables n'existent pas encore (itération de _ALTERS).
    """
    from models.cours import Cours
    from models.tuteurs import Tuteurs
    from models.classes import Classes
    from models.salles import Salles

    configurations = {
        "cours": (Cours, "code_cours", "COU"),
        "tuteurs": (Tuteurs, "code_tuteur", "TUT"),
        "classes": (Classes, "code_classe", "CLA"),
        "salles": (Salles, "code_salle", "SAL"),
    }
    if table not in configurations:
        return
    model, colonne, prefixe = configurations[table]
    annee = datetime.now().year % 100

    with SessionLocal() as db:
        rows = (
            db.query(model)
            .filter(getattr(model, colonne).is_(None))
            .order_by(model.id)
            .all()
        )
        if not rows:
            return
        compteurs = {}
        for row in rows:
            compteurs[annee] = compteurs.get(annee, 0) + 1
            setattr(row, colonne, f"{prefixe}{annee:02d}{compteurs[annee]:05d}")
        db.commit()
        logger.info("Migration SQLite : %d code(s) %s attribué(s).", len(rows), prefixe)


def _recreer_documents_table():
    """Reconstruit `documents` au schéma du modèle courant.

    Nécessaire pour les bases pré-BLOB : ajout des colonnes (matricule_enseignant,
    code_tuteur, contenu, taille, mime_type) et passage de matricule_eleve en
    nullable (les uploads enseignant/tuteur n'ont pas de matricule élève).
    Les données communes sont recopiées, les index recréés explicitement.
    """
    tmp = "documents_migration_tmp"
    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {tmp}"))
        conn.execute(text(f"""
            CREATE TABLE {tmp} (
                id INTEGER NOT NULL,
                matricule_eleve VARCHAR,
                matricule_enseignant VARCHAR,
                code_tuteur VARCHAR,
                type_document VARCHAR NOT NULL,
                filename VARCHAR NOT NULL,
                filepath VARCHAR NOT NULL,
                contenu BLOB,
                taille INTEGER,
                mime_type VARCHAR,
                uploaded_at VARCHAR NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY (matricule_eleve) REFERENCES eleves (matricule) ON DELETE CASCADE
            )
        """))
        communes = [
            c["name"] for c in inspect(conn).get_columns("documents")
            if c["name"] in {c["name"] for c in inspect(conn).get_columns(tmp)}
        ]
        if communes:
            liste = ", ".join(communes)
            conn.execute(text(f"INSERT INTO {tmp} ({liste}) SELECT {liste} FROM documents"))
        conn.execute(text("DROP TABLE documents"))
        conn.execute(text(f"ALTER TABLE {tmp} RENAME TO documents"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_matricule_eleve ON documents (matricule_eleve)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_matricule_enseignant ON documents (matricule_enseignant)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_documents_code_tuteur ON documents (code_tuteur)"))
    logger.info("Migration SQLite : table documents reconstruite (BLOB + entités multiples).")


def _backfill_documents(table=None):
    """Charge en base le contenu des anciens documents stockés sur disque.

    Les fichiers disque sont conservés comme filet de sécurité : un snapshot
    restauré antérieur à cette migration pourra encore les relire via le
    fallback disque de téléchargement.
    """
    import mimetypes
    import os
    from models.documents import Documents

    with SessionLocal() as db:
        rows = db.query(Documents).filter(Documents.contenu.is_(None)).all()
        if not rows:
            return
        backfilles = 0
        for doc in rows:
            chemin = doc.filepath
            if not chemin or not os.path.isfile(chemin):
                continue
            try:
                with open(chemin, "rb") as f:
                    contenu = f.read()
            except OSError:
                continue
            doc.contenu = contenu
            doc.taille = len(contenu)
            if not doc.mime_type:
                doc.mime_type = mimetypes.guess_type(chemin)[0] or "application/octet-stream"
            backfilles += 1
        db.commit()
        if backfilles:
            logger.info("Migration SQLite : %d document(s) backfillé(s) en base.", backfilles)


def _nettoyer_paiements_zero():
    """Supprime les paiements de montant <= 0 (historique invalide).

    Ces lignes ont été créées quand une échéance déjà soldée restait dans la
    file EN_ATTENTE/PARTIEL (sur_ech = 0) : elles ne contribuent à aucun total
    financier (montant 0) et bloquaient le chargement des dossiers élèves.
    """
    from models.paiements import Paiements

    with SessionLocal() as db:
        nb = db.query(Paiements).filter(Paiements.montant <= 0).delete(synchronize_session=False)
        if nb:
            db.commit()
            logger.info("Migration SQLite : %d paiement(s) à montant nul supprimé(s).", nb)


def _migrer_documents():
    inspector = inspect(engine)
    if "documents" not in {t for t in inspector.get_table_names()}:
        return
    cols = {c["name"] for c in inspector.get_columns("documents")}
    matricule_eleve = next((c for c in inspector.get_columns("documents") if c["name"] == "matricule_eleve"), None)
    schema_a_jour = (
        {"matricule_enseignant", "code_tuteur", "contenu", "taille", "mime_type"} <= cols
        and matricule_eleve is not None
        and matricule_eleve.get("nullable") is True
    )
    if not schema_a_jour:
        _recreer_documents_table()
    _backfill_documents()


# table -> liste de (colonne, ALTER SQL, index SQL, backfill) — plusieurs
# colonnes par table sont possibles.
_ALTERS = {
    "inscriptions": [
        ("code_inscription",
         "ALTER TABLE inscriptions ADD COLUMN code_inscription VARCHAR",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_inscriptions_code_inscription ON inscriptions (code_inscription)",
         _backfill_inscriptions),
    ],
    "paiements": [
        ("code_paiement",
         "ALTER TABLE paiements ADD COLUMN code_paiement VARCHAR",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_paiements_code_paiement ON paiements (code_paiement)",
         _backfill_paiements),
    ],
    "depenses": [
        ("code_depense",
         "ALTER TABLE depenses ADD COLUMN code_depense VARCHAR",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_depenses_code_depense ON depenses (code_depense)",
         _backfill_depenses),
    ],
    "cours": [
        ("code_cours",
         "ALTER TABLE cours ADD COLUMN code_cours VARCHAR",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_cours_code_cours ON cours (code_cours)",
         _backfill_globaux),
    ],
    "tuteurs": [
        ("code_tuteur",
         "ALTER TABLE tuteurs ADD COLUMN code_tuteur VARCHAR",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_tuteurs_code_tuteur ON tuteurs (code_tuteur)",
         _backfill_globaux),
    ],
    "classes": [
        ("code_classe",
         "ALTER TABLE classes ADD COLUMN code_classe VARCHAR",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_classes_code_classe ON classes (code_classe)",
         _backfill_globaux),
    ],
    "salles": [
        ("code_salle",
         "ALTER TABLE salles ADD COLUMN code_salle VARCHAR",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_salles_code_salle ON salles (code_salle)",
         _backfill_globaux),
    ],
}

# table -> (colonne, DROP SQL) — suppressions de colonnes (SQLite ≥ 3.35).
_DROPS = [
    ("eleves", "certificat_radiation", "ALTER TABLE eleves DROP COLUMN certificat_radiation"),
]
