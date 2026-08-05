"""cleanup_paiements_zero

Supprime les paiements à montant nul (montant <= 0).

Historique invalide : ces lignes étaient créées quand une échéance déjà soldée
restait dans la file EN_ATTENTE/PARTIEL (sur_ech = 0). Elles ne contribuent à
aucun total financier (montant 0) et bloquaient la sérialisation des dossiers
élèves (PaiementResponse exigeait montant > 0).

La révision est idempotente et compatible SQLite/PostgreSQL.

Revision ID: c3f7a2b9d1e4
Revises: 15c88fb4f0ef
Create Date: 2026-08-04 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3f7a2b9d1e4'
down_revision: Union[str, Sequence[str], None] = '15c88fb4f0ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM paiements WHERE montant <= 0")


def downgrade() -> None:
    """Rien à restaurer : les lignes supprimées sont des artefacts invalides."""
    pass
