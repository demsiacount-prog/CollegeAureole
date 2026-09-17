"""ajouter_role_utilisateurs

Ajoute la colonne `role` aux utilisateurs (rôles proposés à la création :
ADMIN, DIRECTEUR, SECRETAIRE, ENSEIGNANT, COMPTABLE). Simple étiquette : la
validation des valeurs se fait au niveau du service de création.

Revision ID: a7c8d9e0f1a2
Revises: a2b4c6d8e0f2
Create Date: 2026-09-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c8d9e0f1a2'
down_revision: Union[str, Sequence[str], None] = 'a2b4c6d8e0f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajoute la colonne role, tous les comptes existants deviennent ADMIN."""
    op.add_column('utilisateurs', sa.Column(
        'role',
        sa.String(),
        nullable=False,
        server_default='ADMIN',
    ))


def downgrade() -> None:
    op.drop_column('utilisateurs', 'role')