"""ajout_table_cloture_alertes

Table de rappel actif des élèves non réinscrits lors d'une clôture d'année
(classe suivante inexistante, doublon d'inscription…) : la clôture persiste
chaque cas passé dans rapport.erreurs, et un endpoint dédié permet à l'admin
de les traiter (GET /api/cloture/alertes, POST .../resoudre).

Revision ID: aa836c24c299
Revises: a6c8e0f2b4d6
Create Date: 2026-09-20 10:30:39

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aa836c24c299'
down_revision: Union[str, Sequence[str], None] = 'a6c8e0f2b4d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cloture_alertes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_annee_scolaire", sa.Integer(), nullable=False),
        sa.Column("matricule", sa.String(), nullable=False),
        sa.Column("nom", sa.String(), nullable=True),
        sa.Column("prenom", sa.String(), nullable=True),
        sa.Column("motif", sa.String(), nullable=False),
        sa.Column("resolue", sa.Boolean(), nullable=False),
        sa.Column("cree_le", sa.DateTime(), nullable=False),
        sa.Column("resolue_le", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["id_annee_scolaire"], ["annees_scolaires.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cloture_alertes_id_annee_scolaire"), "cloture_alertes", ["id_annee_scolaire"], unique=False)
    op.create_index(op.f("ix_cloture_alertes_matricule"), "cloture_alertes", ["matricule"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_cloture_alertes_matricule"), table_name="cloture_alertes")
    op.drop_index(op.f("ix_cloture_alertes_id_annee_scolaire"), table_name="cloture_alertes")
    op.drop_table("cloture_alertes")