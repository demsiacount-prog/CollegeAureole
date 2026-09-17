"""ajout_prenom_fonction_parents

Révision : complète l'état civil des parents des élèves pour l'affichage des
prénoms et des fonctions du père et de la mère dans le dossier élève et
l'acte de naissance — champs optionnels, rétrocompatibles.

Revision ID: d4e6f8a0b2c4
Revises: b3e5f7a9c1d2
Create Date: 2026-09-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e6f8a0b2c4'
down_revision: Union[str, Sequence[str], None] = 'b3e5f7a9c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('eleves', sa.Column('prenom_pere', sa.String(), nullable=True))
    op.add_column('eleves', sa.Column('fonction_pere', sa.String(), nullable=True))
    op.add_column('eleves', sa.Column('prenom_mere', sa.String(), nullable=True))
    op.add_column('eleves', sa.Column('fonction_mere', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('eleves', 'fonction_mere')
    op.drop_column('eleves', 'prenom_mere')
    op.drop_column('eleves', 'fonction_pere')
    op.drop_column('eleves', 'prenom_pere')