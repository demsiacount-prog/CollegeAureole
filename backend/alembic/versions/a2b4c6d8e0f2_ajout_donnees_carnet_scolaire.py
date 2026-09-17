"""ajout_donnees_carnet_scolaire

Révision : complète les données du carnet scolaire (modèle officiel doc8) —
état civil de l'élève (n° d'acte alternatif, date de l'acte, autorité de
délivrance) et lien de parenté du tuteur. Champs optionnels, rétrocompatibles.

Revision ID: a2b4c6d8e0f2
Revises: d5e6f7a8b9c0
Create Date: 2026-09-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a2b4c6d8e0f2'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('eleves', sa.Column('jugement_suppletif', sa.String(), nullable=True))
    op.add_column('eleves', sa.Column('date_acte', sa.Date(), nullable=True))
    op.add_column('eleves', sa.Column('delivre_par', sa.String(), nullable=True))
    op.add_column('tuteurs', sa.Column('lien_parente', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('tuteurs', 'lien_parente')
    op.drop_column('eleves', 'delivre_par')
    op.drop_column('eleves', 'date_acte')
    op.drop_column('eleves', 'jugement_suppletif')