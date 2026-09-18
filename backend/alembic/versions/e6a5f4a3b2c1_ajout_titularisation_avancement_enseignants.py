"""ajout_titularisation_avancement_enseignants

Ajoute les champs « Date de titularisation » et « Date du dernier avancement »
à la table enseignants, requis par la fiche de renseignements du 1er cycle
(personnel enseignant).

Revision ID: e6a5f4a3b2c1
Revises: d1e2f3a4b5c6
Create Date: 2026-09-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6a5f4a3b2c1'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('enseignants', sa.Column('date_titularisation', sa.Date(), nullable=True))
    op.add_column('enseignants', sa.Column('date_dernier_avancement', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('enseignants', 'date_dernier_avancement')
    op.drop_column('enseignants', 'date_titularisation')