"""rendre_nullables_notes_bulletins

Lève les contraintes NOT NULL devenues gênantes pour deux cas métier légitimes :
- `notes.note` : saisie « note de classe seule » (composition absente) ;
  l'invariant « au moins une des deux notes » reste porté par l'API (422),
  pas par la colonne ;
- `bulletins.moyenne_generale` : aucune matière coefficientée → moyenne non
  applicable, stockée NULL (jamais un 0.0 fallacieux).

Revision ID: b2c4d6e8f0a1
Revises: aa836c24c299
Create Date: 2026-09-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c4d6e8f0a1'
down_revision: Union[str, Sequence[str], None] = 'aa836c24c299'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("notes") as batch_op:
        batch_op.alter_column("note", existing_type=sa.Float(), nullable=True)
    with op.batch_alter_table("bulletins") as batch_op:
        batch_op.alter_column("moyenne_generale", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    # On ne restaure pas NOT NULL si des valeurs NULL existent : les remettre à 0
    # réintroduirait des moyennes/notes falsifiées au bulletin officiel.
    op.execute("SELECT 1")
    lignes = sa.text(
        "SELECT (SELECT COUNT(*) FROM notes WHERE note IS NULL) "
        "     + (SELECT COUNT(*) FROM bulletins WHERE moyenne_generale IS NULL)"
    )
    nul = op.get_bind().execute(lignes).scalar()
    if nul:
        raise RuntimeError(
            f"{nul} valeur(s) NULL à consolider avant le retour à NOT NULL : "
            "réintroduire une contrainte strictement non-nullable est impossible sans falsifier les données."
        )
    with op.batch_alter_table("notes") as batch_op:
        batch_op.alter_column("note", existing_type=sa.Float(), nullable=False)
    with op.batch_alter_table("bulletins") as batch_op:
        batch_op.alter_column("moyenne_generale", existing_type=sa.Float(), nullable=False)