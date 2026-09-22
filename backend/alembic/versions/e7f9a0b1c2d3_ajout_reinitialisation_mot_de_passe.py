"""ajout_reinitialisation_mot_de_passe

Table des jetons de réinitialisation du mot de passe (mot de passe oublié).
Le jeton brut (secrets.token_hex) n'est jamais persisté : seul son hash
SHA-256 l'est (jeton_hash, unique), avec une durée de vie de 30 minutes.
`utilise_le` marque la consommation du jeton (usage unique) ; `id_utilisateur`
est cascade-supprimé avec le compte utilisateur.

Revision ID: e7f9a0b1c2d3
Revises: b2c4d6e8f0a1
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f9a0b1c2d3'
down_revision: Union[str, Sequence[str], None] = 'b2c4d6e8f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mot_de_passe_reinitialisations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("id_utilisateur", sa.Integer(), nullable=False),
        sa.Column("jeton_hash", sa.String(), nullable=False),
        sa.Column("expire_le", sa.DateTime(), nullable=False),
        sa.Column("utilise_le", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["id_utilisateur"], ["utilisateurs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mot_de_passe_reinitialisations_jeton_hash"),
        "mot_de_passe_reinitialisations", ["jeton_hash"], unique=True,
    )
    op.create_index(
        op.f("ix_mot_de_passe_reinitialisations_id_utilisateur"),
        "mot_de_passe_reinitialisations", ["id_utilisateur"], unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_mot_de_passe_reinitialisations_id_utilisateur"), table_name="mot_de_passe_reinitialisations")
    op.drop_index(op.f("ix_mot_de_passe_reinitialisations_jeton_hash"), table_name="mot_de_passe_reinitialisations")
    op.drop_table("mot_de_passe_reinitialisations")