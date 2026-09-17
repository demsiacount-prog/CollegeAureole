"""ajout_champs_documents_admin

Revision ID: d5e6f7a8b9c0
Revises: d4e6f8a0b2c4
Create Date: 2026-09-11 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'd4e6f8a0b2c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ajout des champs nécessaires aux documents officiels de rentrée.

    - etablissement : localisation et statut (rapport succinct de rentrée).
    - enseignants : renseignements administratifs (fiche de renseignements).
    """
    op.add_column('etablissement', sa.Column('village_quartier', sa.String(), nullable=True))
    op.add_column('etablissement', sa.Column('commune', sa.String(), nullable=True))
    op.add_column('etablissement', sa.Column('cercle', sa.String(), nullable=True))
    op.add_column('etablissement', sa.Column('statut_administratif', sa.String(), nullable=True))
    op.add_column('etablissement', sa.Column('type_ecole', sa.String(), nullable=True))
    op.add_column('etablissement', sa.Column('mode', sa.String(), nullable=True))

    op.add_column('enseignants', sa.Column('genre', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('nina', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('date_naissance', sa.Date(), nullable=True))
    op.add_column('enseignants', sa.Column('categorie', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('echelon', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('fonction', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('sf_nombre_enfants', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('date_contrat', sa.Date(), nullable=True))
    op.add_column('enseignants', sa.Column('classe_tenue', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('dernier_poste', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('date_arrivee_cap', sa.Date(), nullable=True))
    op.add_column('enseignants', sa.Column('diplome', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('observations', sa.String(), nullable=True))


def downgrade() -> None:
    for col in (
        'observations', 'diplome', 'date_arrivee_cap', 'dernier_poste',
        'classe_tenue', 'date_contrat', 'sf_nombre_enfants', 'fonction',
        'echelon', 'categorie', 'date_naissance', 'nina', 'genre',
    ):
        op.drop_column('enseignants', col)
    for col in ('mode', 'type_ecole', 'statut_administratif', 'cercle', 'commune', 'village_quartier'):
        op.drop_column('etablissement', col)