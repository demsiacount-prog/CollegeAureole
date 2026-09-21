"""solidifier_unicite_notes_fk_enseignant

Sur `notes` :
- l'unicité (élève, cours, période) laisse passer des doublons quand
  id_trimestre EST NULL (NULL ≠ NULL en SQL) : on transforme la contrainte en
  index UNIQUE classique et on ajoute un index UNIQUE partiel dédié aux notes
  sans période — au plus une note « orpheline » par (élève, cours) ;
- la FK matricule_enseignant passe de ON DELETE CASCADE à ON DELETE SET NULL
  avec colonne nullable : la suppression d'un enseignant ne doit jamais
  effacer ses notes héritées (la couche applicative bloque déjà, ce réglage
  protège les imports/scripts directs).

Revision ID: a6c8e0f2b4d6
Revises: 9b1a2c3d4e5f
Create Date: 2026-09-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6c8e0f2b4d6'
down_revision: Union[str, Sequence[str], None] = '9b1a2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _est_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def _upgrade_sqlite() -> None:
    """SQLite ne sait ni retirer une contrainte UNIQUE ni modifier une FK :
    reconstruction complète de la table (données copiées à l'identique)."""
    conn = op.get_bind()
    op.execute(
        """
        CREATE TABLE notes__reconstruite (
            id INTEGER NOT NULL,
            date DATE NOT NULL,
            note FLOAT NOT NULL,
            note_classe FLOAT,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            matricule_eleve VARCHAR NOT NULL,
            id_cours INTEGER NOT NULL,
            id_classe INTEGER NOT NULL,
            matricule_enseignant VARCHAR,
            id_trimestre INTEGER,
            PRIMARY KEY (id),
            CONSTRAINT uq_note_eleve_cours_trimestre UNIQUE (matricule_eleve, id_cours, id_trimestre),
            FOREIGN KEY(matricule_eleve) REFERENCES eleves (matricule) ON DELETE CASCADE,
            FOREIGN KEY(id_cours) REFERENCES cours (id) ON DELETE CASCADE,
            FOREIGN KEY(id_classe) REFERENCES classes (id) ON DELETE CASCADE,
            FOREIGN KEY(matricule_enseignant) REFERENCES enseignants (matricule) ON DELETE SET NULL,
            FOREIGN KEY(id_trimestre) REFERENCES trimestres (id) ON DELETE CASCADE
        )
        """
    )
    op.execute(
        """
        INSERT INTO notes__reconstruite (
            id, date, note, note_classe, created_at, updated_at,
            matricule_eleve, id_cours, id_classe, matricule_enseignant, id_trimestre
        )
        SELECT id, date, note, note_classe, created_at, updated_at,
            matricule_eleve, id_cours, id_classe, matricule_enseignant, id_trimestre
        FROM notes
        """
    )
    op.execute("DROP TABLE notes")
    op.execute("ALTER TABLE notes__reconstruite RENAME TO notes")
    conn.exec_driver_sql(
        "CREATE INDEX ix_notes_matricule_eleve ON notes (matricule_eleve)"
    )
    conn.exec_driver_sql(
        "CREATE INDEX ix_notes_id_classe ON notes (id_classe)"
    )
    _dedupe_notes_sans_trimestre()
    op.create_index(
        "uq_note_eleve_cours_sans_trimestre", "notes",
        ["matricule_eleve", "id_cours"], unique=True,
        sqlite_where=sa.text("id_trimestre IS NULL"),
    )


def _dedupe_notes_sans_trimestre() -> None:
    """Purge des doublons « orphelins » (élève, cours) sans période qui ont pu
    être créés AVANT que l'index UNIQUE partiel ne le bloque : l'unicité
    (élève, cours, période) ne couvrait pas les lignes à id_trimestre NULL.
    On conserve la première saisie (id minimal) de chaque couple."""
    op.execute(
        """
        DELETE FROM notes
         WHERE id_trimestre IS NULL
           AND id NOT IN (
               SELECT MIN(id) FROM notes
                WHERE id_trimestre IS NULL
                GROUP BY matricule_eleve, id_cours
           )
        """
    )


def _upgrade_postgres() -> None:
    op.drop_constraint("uq_note_eleve_cours_trimestre", "notes", type_="unique")
    op.create_index(
        "uq_note_eleve_cours_trimestre", "notes",
        ["matricule_eleve", "id_cours", "id_trimestre"], unique=True,
    )
    _dedupe_notes_sans_trimestre()
    op.create_index(
        "uq_note_eleve_cours_sans_trimestre", "notes",
        ["matricule_eleve", "id_cours"], unique=True,
        postgresql_where=sa.text("id_trimestre IS NULL"),
    )
    op.alter_column(
        "notes", "matricule_enseignant",
        existing_type=sa.String(), nullable=True,
    )
    fk_names = [
        fk["name"]
        for fk in op.get_bind().dialect.get_foreign_keys(
            op.get_bind(), "notes"
        )
        if fk["constrained_columns"] == ["matricule_enseignant"]
    ]
    for nom in fk_names:
        if nom:
            op.drop_constraint(nom, "notes", type_="foreignkey")
    op.create_foreign_key(
        "notes_matricule_enseignant_fkey", "notes", "enseignants",
        ["matricule_enseignant"], ["matricule"], ondelete="SET NULL",
    )


def upgrade() -> None:
    if _est_sqlite():
        _upgrade_sqlite()
    else:
        _upgrade_postgres()


def downgrade() -> None:
    if _est_sqlite():
        conn = op.get_bind()
        conn.exec_driver_sql(
            "DROP INDEX IF EXISTS uq_note_eleve_cours_sans_trimestre"
        )
        op.execute(
            """
            CREATE TABLE notes__reconstruite (
                id INTEGER NOT NULL,
                date DATE NOT NULL,
                note FLOAT NOT NULL,
                note_classe FLOAT,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                matricule_eleve VARCHAR NOT NULL,
                id_cours INTEGER NOT NULL,
                id_classe INTEGER NOT NULL,
                matricule_enseignant VARCHAR NOT NULL,
                id_trimestre INTEGER,
                PRIMARY KEY (id),
                CONSTRAINT uq_note_eleve_cours_trimestre UNIQUE (matricule_eleve, id_cours, id_trimestre),
                FOREIGN KEY(matricule_eleve) REFERENCES eleves (matricule) ON DELETE CASCADE,
                FOREIGN KEY(id_cours) REFERENCES cours (id) ON DELETE CASCADE,
                FOREIGN KEY(id_classe) REFERENCES classes (id) ON DELETE CASCADE,
                FOREIGN KEY(matricule_enseignant) REFERENCES enseignants (matricule) ON DELETE CASCADE,
                FOREIGN KEY(id_trimestre) REFERENCES trimestres (id) ON DELETE CASCADE
            )
            """
        )
        op.execute(
            """
            INSERT INTO notes__reconstruite (
                id, date, note, note_classe, created_at, updated_at,
                matricule_eleve, id_cours, id_classe, matricule_enseignant, id_trimestre
            )
            SELECT id, date, note, note_classe, created_at, updated_at,
                matricule_eleve, id_cours, id_classe, matricule_enseignant, id_trimestre
            FROM notes
            """
        )
        op.execute("DROP TABLE notes")
        op.execute("ALTER TABLE notes__reconstruite RENAME TO notes")
        conn.exec_driver_sql(
            "CREATE INDEX ix_notes_matricule_eleve ON notes (matricule_eleve)"
        )
        conn.exec_driver_sql(
            "CREATE INDEX ix_notes_id_classe ON notes (id_classe)"
        )
    else:
        op.drop_index("uq_note_eleve_cours_sans_trimestre", table_name="notes")
        op.drop_index("uq_note_eleve_cours_trimestre", table_name="notes")
        op.create_unique_constraint(
            "uq_note_eleve_cours_trimestre",
            "notes",
            ["matricule_eleve", "id_cours", "id_trimestre"],
        )
        op.alter_column(
            "notes", "matricule_enseignant",
            existing_type=sa.String(), nullable=False,
        )
        op.drop_constraint("notes_matricule_enseignant_fkey", "notes", type_="foreignkey")
        op.create_foreign_key(
            "notes_matricule_enseignant_fkey", "notes", "enseignants",
            ["matricule_enseignant"], ["matricule"], ondelete="CASCADE",
        )