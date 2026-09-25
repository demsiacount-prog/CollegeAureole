"""email_enseignants_facultatif

L'email d'un enseignant devient facultatif : la plupart des enseignants
maliens n'ont pas d'adresse e-mail. Une valeur absente est stockée NULL
(toujours autorisé par l'index unique : plusieurs NULL coexistent).

Revision ID: 4bb3f4eede17
Revises: e7f9a0b1c2d3
Create Date: 2026-09-24 06:32:01.826018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bb3f4eede17'
down_revision: Union[str, Sequence[str], None] = 'e7f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("enseignants") as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    # Ne recolle pas NOT NULL si des lignes sans email existent : ce serait
    # falsifier la saisie pour restaurer une contrainte devenue inutile.
    nuls = op.get_bind().execute(
        sa.text("SELECT COUNT(*) FROM enseignants WHERE email IS NULL")
    ).scalar()
    if nuls:
        raise RuntimeError(
            f"{nuls} enseignant(s) sans email : restauration de NOT NULL impossible "
            "sans inventer une adresse."
        )
    with op.batch_alter_table("enseignants") as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(), nullable=False)
