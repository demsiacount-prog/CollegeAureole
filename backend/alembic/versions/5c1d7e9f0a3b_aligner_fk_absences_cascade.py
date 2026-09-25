"""aligner_fk_absences_cascade

La baseline créait la FK `absences.matricule_eleve` sans `ON DELETE CASCADE`,
alors que le modèle la déclare avec CASCADE. En base, l'action par défaut
(NO ACTION) bloquait alors la suppression d'un élève ayant des absences si la
couche applicative ne purgeait pas d'abord : on recrée la FK avec l'action de
suppression déclarée par le modèle.

Revision ID: 5c1d7e9f0a3b
Revises: 4bb3f4eede17
Create Date: 2026-09-24

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '5c1d7e9f0a3b'
down_revision: Union[str, Sequence[str], None] = '4bb3f4eede17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("absences_matricule_eleve_fkey", "absences", type_="foreignkey")
    op.create_foreign_key(
        "absences_matricule_eleve_fkey", "absences", "eleves",
        ["matricule_eleve"], ["matricule"], ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("absences_matricule_eleve_fkey", "absences", type_="foreignkey")
    op.create_foreign_key(
        "absences_matricule_eleve_fkey", "absences", "eleves",
        ["matricule_eleve"], ["matricule"],
    )