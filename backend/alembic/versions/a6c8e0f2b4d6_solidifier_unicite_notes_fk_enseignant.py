"""solidifier_unicite_notes_fk_enseignant

Cette revision est désactivée (no-op) : le schéma applicatif cible, décrit par
le modèle `notes`, correspond exactement à ce que produit la baseline de la
chaîne — contrainte UNIQUE `uq_note_eleve_cours_trimestre` sur
(matricule_eleve, id_cours, id_trimestre), et FK `matricule_enseignant`
NOT NULL avec ON DELETE CASCADE. Elle reste dans la chaîne uniquement pour
préserver l'historique des bases déjà migrées : son `upgrade` comme son
`downgrade` ne touchent à rien.

Revision ID: a6c8e0f2b4d6
Revises: 9b1a2c3d4e5f
Create Date: 2026-09-19

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a6c8e0f2b4d6'
down_revision: Union[str, Sequence[str], None] = '9b1a2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass