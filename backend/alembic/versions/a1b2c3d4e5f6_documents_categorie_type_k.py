"""documents_categorie_type_k

Revision ID: a1b2c3d4e5f6
Revises: f7e8d9c0b1a2
Create Date: 2026-09-14 10:00:00.000000

Ajoute les colonnes du flux Type K / §46 aux documents :
- categorie            : regroupement (identite, photo, naissance, scolaire,
                         medical, administratif, autre) — remplace
                         type_document dans les nouveaux uploads.
- nom_fichier_original : nom d'origine du fichier conservé pour le download.
- type_document passée nullable (l'ancien libellé par type reste utile
  pour la compat rétro des pièces déjà uploadées).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'f7e8d9c0b1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('categorie', sa.String(), nullable=True))
    op.add_column('documents', sa.Column('nom_fichier_original', sa.String(), nullable=True))
    op.alter_column('documents', 'type_document', existing_type=sa.String(), nullable=True)
    # Rétro-compat : les lignes existantes sont classées « autre ».
    op.execute("UPDATE documents SET categorie = 'autre' WHERE categorie IS NULL")
    op.alter_column('documents', 'categorie', existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    op.alter_column('documents', 'type_document', existing_type=sa.String(), nullable=False)
    op.drop_column('documents', 'nom_fichier_original')
    op.drop_column('documents', 'categorie')