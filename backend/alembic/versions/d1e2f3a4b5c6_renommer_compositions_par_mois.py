"""renommer_compositions_par_mois

Révision : renomme les compositions auto-générées pour qu'elles portent
le nom de leur mois (« Composition 1 » → « Composition Octobre », etc.).

La règle est la même que dans periodes.py : le mois est déduit du jour
médian de la période, ce qui garantit des noms distincts pour une année
scolaire classique (≈ 1 composition par mois).

Revision ID: d1e2f3a4b5c6
Revises: b0a1c2d3e4f5
Create Date: 2026-09-18

"""
from typing import Union, Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, Sequence[str], None] = 'b0a1c2d3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MOIS_FRANCAIS = (
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
)


def _mois_composition(date_debut, date_fin) -> str:
    """Mois (en français) du jour médian d'une composition."""
    milieu = date_debut + (date_fin - date_debut) // 2
    return MOIS_FRANCAIS[milieu.month - 1]


def upgrade() -> None:
    connexion = op.get_bind()
    trimestres = sa.table(
        "trimestres",
        sa.column("id", sa.Integer),
        sa.column("annee_scolaire_id", sa.Integer),
        sa.column("type", sa.String),
        sa.column("nom", sa.String),
        sa.column("date_debut", sa.Date),
        sa.column("date_fin", sa.Date),
    )
    lignes = connexion.execute(
        sa.select(
            trimestres.c.id,
            trimestres.c.annee_scolaire_id,
            trimestres.c.nom,
            trimestres.c.date_debut,
            trimestres.c.date_fin,
        )
        .where(trimestres.c.type == "COMPOSITION")
        .order_by(trimestres.c.annee_scolaire_id, trimestres.c.date_debut)
    )
    noms_par_annee: dict[int, set[str]] = {}
    for ligne in lignes:
        nouveau_nom = f"Composition {_mois_composition(ligne.date_debut, ligne.date_fin)}"
        pris = noms_par_annee.setdefault(ligne.annee_scolaire_id, set())
        if nouveau_nom in pris:
            continue
        pris.add(nouveau_nom)
        connexion.execute(
            trimestres.update()
            .where(trimestres.c.id == ligne.id)
            .values(nom=nouveau_nom)
        )


def downgrade() -> None:
    pass