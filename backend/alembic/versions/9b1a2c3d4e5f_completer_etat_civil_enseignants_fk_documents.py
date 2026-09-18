"""completer_etat_civil_enseignants_fk_documents

Ajoute à `enseignants` les champs d'état civil demandés par les fiches de
renseignements (lieu de naissance, nationalité, situation matrimoniale + index
de recherche), transforme les rattachements de pièces jointes enseignant/tuteur
en vraies clés étrangères et horodate les infrastructures.

Revision ID: 9b1a2c3d4e5f
Revises: e6a5f4a3b2c1
Create Date: 2026-09-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b1a2c3d4e5f'
down_revision: Union[str, Sequence[str], None] = 'e6a5f4a3b2c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _est_sqlite() -> bool:
    return op.get_bind().dialect.name == "sqlite"


def upgrade() -> None:
    # État civil enseignant (fiches de renseignements doc6 / 1er cycle).
    op.add_column('enseignants', sa.Column('lieu_de_naissance', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('nationalite', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('situation_matrimoniale', sa.String(), nullable=True))

    # Index de recherche sur les noms (listes, tris de fiches).
    op.create_index(op.f('ix_enseignants_nom'), 'enseignants', ['nom'], unique=False)
    op.create_index(op.f('ix_enseignants_prenom'), 'enseignants', ['prenom'], unique=False)

    # Documents : purge des références orphelines puis vraies clés étrangères.
    op.execute(
        """
        UPDATE documents
           SET matricule_enseignant = NULL
         WHERE matricule_enseignant IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM enseignants
                            WHERE enseignants.matricule = documents.matricule_enseignant)
        """
    )
    op.execute(
        """
        UPDATE documents
           SET code_tuteur = NULL
         WHERE code_tuteur IS NOT NULL
           AND NOT EXISTS (SELECT 1 FROM tuteurs
                            WHERE tuteurs.code_tuteur = documents.code_tuteur)
        """
    )
    if not _est_sqlite():
        op.create_foreign_key(
            'fk_documents_matricule_enseignant', 'documents', 'enseignants',
            ['matricule_enseignant'], ['matricule'], ondelete='SET NULL',
        )
        op.create_foreign_key(
            'fk_documents_code_tuteur', 'documents', 'tuteurs',
            ['code_tuteur'], ['code_tuteur'], ondelete='SET NULL',
        )

    # Horodatage des infrastructures (une ligne par année scolaire).
    op.add_column(
        'etablissement_infrastructures',
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.add_column(
        'etablissement_infrastructures',
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_column('etablissement_infrastructures', 'updated_at')
    op.drop_column('etablissement_infrastructures', 'created_at')

    if not _est_sqlite():
        op.drop_constraint('fk_documents_code_tuteur', 'documents', type_='foreignkey')
        op.drop_constraint('fk_documents_matricule_enseignant', 'documents', type_='foreignkey')

    op.drop_index(op.f('ix_enseignants_prenom'), table_name='enseignants')
    op.drop_index(op.f('ix_enseignants_nom'), table_name='enseignants')
    op.drop_column('enseignants', 'situation_matrimoniale')
    op.drop_column('enseignants', 'nationalite')
    op.drop_column('enseignants', 'lieu_de_naissance')