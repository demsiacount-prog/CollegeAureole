"""add_created_at_updated_at_all_models

Revision ID: 3e6ecb87e60c
Revises: 0002
Create Date: 2026-07-20 17:43:09.875908

"""
from datetime import datetime
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e6ecb87e60c'
down_revision = '0002'
branch_labels = None
depends_on = None

TABLES = [
    "annees_scolaires",
    "bulletin_details",
    "bulletins",
    "classe_cours",
    "classes",
    "cours",
    "notes",
    "salles",
    "trimestres",
    "tuteurs",
]

now_str = datetime.now().isoformat()


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("created_at", sa.String(), nullable=True))
        op.add_column(table, sa.Column("updated_at", sa.String(), nullable=True))
        op.execute(f"UPDATE {table} SET created_at = '{now_str}', updated_at = '{now_str}'")
        op.alter_column(table, "created_at", nullable=False)
        op.alter_column(table, "updated_at", nullable=False)


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")
