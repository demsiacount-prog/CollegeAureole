"""ajout_nb_redoublements_inscriptions

Ajoute la colonne `nb_redoublements` à la table `inscriptions` : chaque élève
dispose d'un compteur du nombre de redoublements pour la classe de l'année
considérée (défaut 0). Ce compteur alimentera les effectifs de rentrée.

Revision ID: f7e8d9c0b1a2
Revises: a7c8d9e0f1a2
Create Date: 2026-09-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7e8d9c0b1a2'
down_revision: Union[str, Sequence[str], None] = 'a7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('inscriptions', sa.Column(
        'nb_redoublements',
        sa.Integer(),
        nullable=False,
        server_default='0',
    ))


def downgrade() -> None:
    op.drop_column('inscriptions', 'nb_redoublements')