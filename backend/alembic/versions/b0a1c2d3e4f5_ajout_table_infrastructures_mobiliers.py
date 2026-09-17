"""ajout_table_infrastructures_mobiliers

Fiche de renseignements 1er cycle (document 4) : ajoute la table
`etablissement_infrastructures` (une ligne par année scolaire) pour stocker
le bloc « Infrastructures et mobiliers » :
- salles construites (dur / semi-dur / banco / autres)
- directions (dur / banco / autres) + logement de la direction
- mobiliers (tables-bancs, chaises, armoires, tableaux, divers)

Revision ID: b0a1c2d3e4f5
Revises: a1b2c3d4e5f6
Create Date: 2026-09-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b0a1c2d3e4f5'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'etablissement_infrastructures',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('id_annee_scolaire', sa.Integer(), sa.ForeignKey('annees_scolaires.id'), nullable=False),
        # Salles construites
        sa.Column('salles_dur', sa.Integer(), nullable=True),
        sa.Column('salles_semi_dur', sa.Integer(), nullable=True),
        sa.Column('salles_banco', sa.Integer(), nullable=True),
        sa.Column('salles_autres', sa.Integer(), nullable=True),
        # Directions
        sa.Column('direction_dur', sa.Integer(), nullable=True),
        sa.Column('direction_banco', sa.Integer(), nullable=True),
        sa.Column('direction_autres', sa.Integer(), nullable=True),
        sa.Column('logement_direction', sa.Integer(), nullable=True),
        # Mobiliers
        sa.Column('tables_bancs', sa.Integer(), nullable=True),
        sa.Column('chaises', sa.Integer(), nullable=True),
        sa.Column('armoires', sa.Integer(), nullable=True),
        sa.Column('tableaux', sa.Integer(), nullable=True),
        sa.Column('mobilier_divers', sa.Integer(), nullable=True),
        sa.UniqueConstraint('id_annee_scolaire', name='uq_etab_infra_annee'),
    )


def downgrade() -> None:
    op.drop_table('etablissement_infrastructures')
