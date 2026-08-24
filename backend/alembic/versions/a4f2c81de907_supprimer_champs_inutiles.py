"""Suppression des colonnes inutiles : uuid, heures_hebdo_max, version_initialisee

Revision ID: a4f2c81de907
Revises: f17c959ae532
Create Date: 2026-08-23 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4f2c81de907'
down_revision: Union[str, Sequence[str], None] = 'f17c959ae532'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# table → nom de l'index unique sur la colonne uuid
TABLES_UUID = {
    'annees_scolaires': 'ix_annees_scolaires_uuid',
    'depenses': 'ix_depenses_uuid',
    'enseignants': 'ix_enseignants_uuid',
    'salles': 'ix_salles_uuid',
    'tuteurs': 'ix_tuteurs_uuid',
    'utilisateurs': 'ix_utilisateurs_uuid',
    'classes': 'ix_classes_uuid',
    'cours': 'ix_cours_uuid',
    'trimestres': 'ix_trimestres_uuid',
    'classe_cours': 'ix_classe_cours_uuid',
    'eleves': 'ix_eleves_uuid',
    'seances': 'ix_seances_uuid',
    'absences': 'ix_absences_uuid',
    'bulletins': 'ix_bulletins_uuid',
    'inscriptions': 'ix_inscriptions_uuid',
    'notes': 'ix_notes_uuid',
    'bulletin_details': 'ix_bulletin_details_uuid',
    'echeances': 'ix_echeances_uuid',
    'paiements': 'ix_paiements_uuid',
    'remises': 'ix_remises_uuid',
}


def upgrade() -> None:
    for table, index in TABLES_UUID.items():
        op.drop_index(index, table_name=table)
        op.drop_column(table, 'uuid')
    op.drop_column('enseignants', 'heures_hebdo_max')
    op.drop_column('etablissement', 'version_initialisee')


def downgrade() -> None:
    op.add_column('etablissement', sa.Column('version_initialisee', sa.String(), nullable=True))
    op.add_column('enseignants', sa.Column('heures_hebdo_max', sa.Float(), nullable=True))
    for table, index in TABLES_UUID.items():
        op.add_column(table, sa.Column('uuid', sa.String(), nullable=False, server_default=''))
        # Backfill de valeurs uniques avant de recréer l'index unique.
        op.execute(sa.text(f"UPDATE {table} SET uuid = gen_random_uuid()::text"))
        op.create_index(index, table, ['uuid'], unique=True)
