"""supprimer_role_utilisateurs

Révision : la bascule vers un compte administrateur unique supprime la
notion de rôle (admin/directeur/comptable). Nettoie les comptes non-admin
puis retire la colonne `role` et le type enum `roleutilisateur`.

Revision ID: e3f2a9c1b4d7
Revises: ceefcae0ad62
Create Date: 2026-09-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f2a9c1b4d7'
down_revision: Union[str, Sequence[str], None] = 'ceefcae0ad62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Supprime les comptes non-admin, la colonne role et l'enum associé."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    # 1) Nettoyage : ne conserve que les comptes administrateurs.
    op.execute("DELETE FROM utilisateurs WHERE role <> 'ADMIN'")

    # 2) La colonne role n'a plus de raison d'être.
    op.drop_column('utilisateurs', 'role')

    # 3) Suppression du type enum natif désormais orphelin.
    if dialect == "postgresql":
        op.execute("DROP TYPE IF EXISTS roleutilisateur")


def downgrade() -> None:
    """Rétablit une colonne role (valeur par défaut ADMIN) sans enum natif
    (utilisateur unique)."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("CREATE TYPE roleutilisateur AS ENUM ('ADMIN', 'DIRECTEUR', 'COMPTABLE')")
        op.add_column('utilisateurs', sa.Column(
            'role',
            sa.Enum('ADMIN', 'DIRECTEUR', 'COMPTABLE', name='roleutilisateur'),
            nullable=False,
            server_default='ADMIN',
        ))
    else:
        op.add_column('utilisateurs', sa.Column(
            'role',
            sa.String(),
            nullable=False,
            server_default='ADMIN',
        ))