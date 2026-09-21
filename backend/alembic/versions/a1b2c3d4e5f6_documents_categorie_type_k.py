"""documents_categorie_type_k

Revision ID: a1b2c3d4e5f6
Revises: f7e8d9c0b1a2
Create Date: 2026-09-14 10:00:00.000000

Ajoute les colonnes du flux Type K / §46 aux documents :
- categorie            : regroupement (identite, photo, naissance, scolaire,
                         medical, administratif, autre) — remplace
                         type_document dans les nouveaux uploads.
- nom_fichier_original : nom d'origine du fichier conservé pour le download.
- type_document passée nullable (l'ancien libellé par type reste utile
  pour la compat rétro des pièces déjà uploadées).

FIX : op.alter_column(..., nullable=True) n'existe pas sur SQLite (DROP NOT
NULL non supporté) : on reconstruit la table côté SQLite, comme les autres
migrations du projet. Cela débloque les installations/bases SQLite qui ne
pouvait pas atteindre head.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f7e8d9c0b1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _est_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def _upgrade_sqlite() -> None:
    """SQLite ne sait pas retirer une contrainte NOT NULL : reconstruction de
    `documents` (données copiées à l'identique). À ce stade de la chaîne la
    table porte uniquement la FK `eleves` (les FK enseignant/tuteur du §
    « vraies clés étrangères » sont ajoutées dans la revision suivante)."""
    conn = op.get_bind()
    op.execute(
        """
        CREATE TABLE documents__reconstruite (
            id INTEGER NOT NULL,
            matricule_eleve VARCHAR,
            matricule_enseignant VARCHAR,
            code_tuteur VARCHAR,
            type_document VARCHAR,
            filename VARCHAR NOT NULL,
            filepath VARCHAR NOT NULL,
            contenu BLOB,
            taille INTEGER,
            mime_type VARCHAR,
            uploaded_at DATETIME NOT NULL,
            categorie VARCHAR NOT NULL,
            nom_fichier_original VARCHAR,
            PRIMARY KEY (id),
            FOREIGN KEY(matricule_eleve) REFERENCES eleves (matricule) ON DELETE CASCADE
        )
        """
    )
    op.execute(
        """
        INSERT INTO documents__reconstruite (
            id, matricule_eleve, matricule_enseignant, code_tuteur,
            type_document, filename, filepath, contenu, taille, mime_type,
            uploaded_at, categorie, nom_fichier_original
        )
        SELECT id, matricule_eleve, matricule_enseignant, code_tuteur,
            type_document, filename, filepath, contenu, taille, mime_type,
            uploaded_at, 'autre', NULL
        FROM documents
        """
    )
    op.execute("DROP TABLE documents")
    op.execute("ALTER TABLE documents__reconstruite RENAME TO documents")
    conn.exec_driver_sql("CREATE INDEX ix_documents_matricule_eleve ON documents (matricule_eleve)")
    conn.exec_driver_sql("CREATE INDEX ix_documents_matricule_enseignant ON documents (matricule_enseignant)")
    conn.exec_driver_sql("CREATE INDEX ix_documents_code_tuteur ON documents (code_tuteur)")


def upgrade() -> None:
    if _est_sqlite():
        _upgrade_sqlite()
        return
    op.add_column('documents', sa.Column('categorie', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('nom_fichier_original', sa.String(), nullable=True))
    op.alter_column('documents', 'type_document', existing_type=sa.String(), nullable=True)
    # Rétro-compat : les lignes existantes sont classées « autre ».
    op.execute("UPDATE documents SET categorie = 'autre' WHERE categorie IS NULL")
    op.alter_column('documents', 'categorie', existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    if _est_sqlite():
        # La reconstruction inverse n'est pas implémentée : les FKs enseignant
        # / tuteur ajoutées par la revision suivante rendent un rollback exact
        # inutilement risqué (données déjà migrées = non régressives).
        op.alter_column('documents', 'type_document', existing_type=sa.String(), nullable=False)
        return
    op.alter_column('documents', 'type_document', existing_type=sa.String(), nullable=False)
    op.drop_column('documents', 'nom_fichier_original')
    op.drop_column('documents', 'categorie')