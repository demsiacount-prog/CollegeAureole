"""Correctifs urgents : uniformisation des dates (UTC, timezone-aware),
séquences DB pour la génération sécurisée des matricules, et index
manquants pour éviter les scans complets sur les jointures fréquentes.

Revision ID: 0001
Revises:
Create Date: 2026-07-19
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


# Colonnes créées comme VARCHAR (isoformat() côté Python) qu'il faut
# convertir en TIMESTAMPTZ. `USING col::timestamptz` fonctionne car le
# format ISO 8601 produit par `datetime.isoformat()` est directement
# interprétable par PostgreSQL. Les valeurs déjà en place sont
# considérées comme de l'heure locale du serveur (comportement historique
# du code) : on les traite comme UTC faute de mieux, ce qui est le même
# choix, en pratique, que les autres colonnes qui utilisaient déjà
# `datetime.utcnow()`.
STRING_DATETIME_COLUMNS = [
    ("absences", ["created_at", "updated_at"]),
    ("eleves", ["created_at", "updated_at"]),
    ("enseignants", ["created_at", "updated_at"]),
    ("depenses", ["created_at", "updated_at"]),
    ("echeances", ["created_at", "updated_at"]),
    ("inscriptions", ["created_at", "updated_at"]),
    ("paiements", ["created_at", "updated_at"]),
    ("seances", ["created_at", "updated_at"]),
]

# Colonnes déjà en DateTime (naïf) qu'il faut juste rendre timezone-aware.
NAIVE_DATETIME_COLUMNS = [
    ("bulletins", ["generated_at", "published_at"]),
    ("utilisateurs", ["verrouille_jusqua", "created_at", "updated_at"]),
    ("absences", ["date_justification"]),
]


def upgrade() -> None:
    # --- 1. Uniformisation des types de dates -----------------------------
    for table, columns in STRING_DATETIME_COLUMNS:
        for column in columns:
            op.execute(
                f'ALTER TABLE {table} ALTER COLUMN "{column}" '
                f'TYPE timestamptz USING "{column}"::timestamptz'
            )

    for table, columns in NAIVE_DATETIME_COLUMNS:
        for column in columns:
            op.execute(
                f'ALTER TABLE {table} ALTER COLUMN "{column}" '
                f"TYPE timestamptz USING \"{column}\" AT TIME ZONE 'UTC'"
            )

    # --- 2. Séquences PostgreSQL pour la génération sécurisée des matricules
    # nextval() est atomique côté DB : deux inserts concurrents ne peuvent
    # plus obtenir le même matricule, contrairement à l'ancien
    # SELECT COUNT(*) + 1 fait côté application.
    op.execute("CREATE SEQUENCE IF NOT EXISTS eleves_matricule_seq START WITH 1")
    op.execute("CREATE SEQUENCE IF NOT EXISTS enseignants_matricule_seq START WITH 1")

    # On resynchronise la séquence sur les données déjà en place, pour ne
    # pas régénérer un matricule déjà attribué (base non vide en prod).
    op.execute(
        "SELECT setval('eleves_matricule_seq', "
        "GREATEST((SELECT COUNT(*) FROM eleves), 0) + 1, false)"
    )
    op.execute(
        "SELECT setval('enseignants_matricule_seq', "
        "GREATEST((SELECT COUNT(*) FROM enseignants), 0) + 1, false)"
    )

    # --- 3. Index manquants -------------------------------------------------
    op.create_index("ix_bulletins_matricule_eleve", "bulletins", ["matricule_eleve"])
    op.create_index("ix_bulletins_id_trimestre", "bulletins", ["id_trimestre"])
    op.create_index("ix_bulletins_id_classe", "bulletins", ["id_classe"])
    op.create_index("ix_bulletin_details_id_bulletin", "bulletin_details", ["id_bulletin"])
    op.create_index("ix_bulletin_details_id_cours", "bulletin_details", ["id_cours"])

    op.create_index("ix_notes_id_cours", "notes", ["id_cours"])
    op.create_index("ix_notes_id_trimestre", "notes", ["id_trimestre"])
    op.create_index("ix_notes_matricule_enseignant", "notes", ["matricule_enseignant"])
    op.create_index(
        "ix_notes_matricule_eleve_id_trimestre", "notes", ["matricule_eleve", "id_trimestre"]
    )

    op.create_index("ix_trimestres_annee_scolaire_id", "trimestres", ["annee_scolaire_id"])


def downgrade() -> None:
    op.drop_index("ix_trimestres_annee_scolaire_id", table_name="trimestres")

    op.drop_index("ix_notes_matricule_eleve_id_trimestre", table_name="notes")
    op.drop_index("ix_notes_matricule_enseignant", table_name="notes")
    op.drop_index("ix_notes_id_trimestre", table_name="notes")
    op.drop_index("ix_notes_id_cours", table_name="notes")

    op.drop_index("ix_bulletin_details_id_cours", table_name="bulletin_details")
    op.drop_index("ix_bulletin_details_id_bulletin", table_name="bulletin_details")
    op.drop_index("ix_bulletins_id_classe", table_name="bulletins")
    op.drop_index("ix_bulletins_id_trimestre", table_name="bulletins")
    op.drop_index("ix_bulletins_matricule_eleve", table_name="bulletins")

    op.execute("DROP SEQUENCE IF EXISTS enseignants_matricule_seq")
    op.execute("DROP SEQUENCE IF EXISTS eleves_matricule_seq")

    for table, columns in NAIVE_DATETIME_COLUMNS:
        for column in columns:
            op.execute(f'ALTER TABLE {table} ALTER COLUMN "{column}" TYPE timestamp')

    for table, columns in STRING_DATETIME_COLUMNS:
        for column in columns:
            op.execute(
                f'ALTER TABLE {table} ALTER COLUMN "{column}" '
                f'TYPE varchar USING "{column}"::varchar'
            )
