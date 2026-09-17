"""ajout_note_classe_notes

Révision : ajoute la note de classe (facultative) à la table notes.
La moyenne d'une matière vaut 60 % (composition) + 40 % (classe) ; en
l'absence de note de classe, la note de composition fait foi.

Revision ID: b3e5f7a9c1d2
Revises: 7a1b2c3d4e5f
Create Date: 2026-09-09

"""
from typing import Union, Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3e5f7a9c1d2'
down_revision: Union[str, Sequence[str], None] = '7a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('notes', sa.Column('note_classe', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('notes', 'note_classe')