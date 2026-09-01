"""ajout_academie_cap_etablissement

Revision ID: ceefcae0ad62
Revises: a4f2c81de907
Create Date: 2026-08-30 11:48:36.861996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ceefcae0ad62'
down_revision: Union[str, Sequence[str], None] = 'a4f2c81de907'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajout des colonnes academie et cap à la fiche établissement."""
    op.add_column('etablissement', sa.Column('academie', sa.String(), nullable=False, server_default=''))
    op.add_column('etablissement', sa.Column('cap', sa.String(), nullable=False, server_default=''))


def downgrade() -> None:
    op.drop_column('etablissement', 'cap')
    op.drop_column('etablissement', 'academie')
