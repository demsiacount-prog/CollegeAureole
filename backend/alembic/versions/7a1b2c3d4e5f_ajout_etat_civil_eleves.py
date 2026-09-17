"""ajout_etat_civil_eleves

Révision : complète l'état civil des élèves pour l'édition d'un acte de
naissance (n° d'acte, père, mère) — champs optionnels, rétrocompatibles.

Revision ID: 7a1b2c3d4e5f
Revises: e3f2a9c1b4d7
Create Date: 2026-09-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1b2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = 'e3f2a9c1b4d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('eleves', sa.Column('numero_acte', sa.String(), nullable=True))
    op.add_column('eleves', sa.Column('nom_pere', sa.String(), nullable=True))
    op.add_column('eleves', sa.Column('nom_mere', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('eleves', 'nom_mere')
    op.drop_column('eleves', 'nom_pere')
    op.drop_column('eleves', 'numero_acte')