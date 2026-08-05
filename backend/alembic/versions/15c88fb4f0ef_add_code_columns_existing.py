"""add_code_columns_existing

Ajoute les colonnes de codes (inscriptions, paiements, dépenses, cours,
tuteurs, classes, salles) aux bases existantes migrées par l'ancienne chaîne
Alembic, puis attribue les codes rétroactivement (backfill) et crée les index
uniques.

La baseline 37c410820056 décrit le schéma complet pour une base vierge ; elle
ne suffit pas pour une base existante qui n'a pas (ou pas toutes) les colonnes
de codes. Déploiement d'une base existante :

    alembic stamp 37c410820056 && alembic upgrade head

La révision est idempotente : sur une base vierge déjà montée par la baseline,
les colonnes et index existant sont détectés (inspect) et laissés intacts, et le
backfill ne trouve aucune ligne.

Revision ID: 15c88fb4f0ef
Revises: 37c410820056
Create Date: 2026-08-01 11:59:14.642910

"""
import logging
from datetime import date, datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

logger = logging.getLogger("alembic.runtime.migration")

# revision identifiers, used by Alembic.
revision: str = '15c88fb4f0ef'
down_revision: Union[str, Sequence[str], None] = '37c410820056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, colonne, index unique) — les 7 colonnes de codes des bases existantes
# (l'ancienne chaîne pouvait s'arrêter avant code_inscription : tout est idempotent).
_COLONNES = [
    ("inscriptions", "code_inscription", "ix_inscriptions_code_inscription"),
    ("paiements", "code_paiement", "ix_paiements_code_paiement"),
    ("depenses", "code_depense", "ix_depenses_code_depense"),
    ("cours", "code_cours", "ix_cours_code_cours"),
    ("tuteurs", "code_tuteur", "ix_tuteurs_code_tuteur"),
    ("classes", "code_classe", "ix_classes_code_classe"),
    ("salles", "code_salle", "ix_salles_code_salle"),
]

# cours, tuteurs, classes, salles : compteur global, année de la migration.
_GLOBAUX = [
    ("cours", "code_cours", "COU"),
    ("tuteurs", "code_tuteur", "TUT"),
    ("classes", "code_classe", "CLA"),
    ("salles", "code_salle", "SAL"),
]


def _annee(valeur):
    """Année (modulo 100) d'une valeur date, SQLite (str) ou PostgreSQL (date)."""
    if isinstance(valeur, str):
        valeur = date.fromisoformat(valeur[:10])
    return (valeur.year if valeur else datetime.now().year) % 100


def _annee_active(bind, date_valeur):
    """date_debut de l'année scolaire contenant date_valeur, sinon None."""
    row = bind.execute(
        sa.text(
            "SELECT date_debut FROM annees_scolaires "
            "WHERE date_debut <= :d AND date_fin >= :d "
            "ORDER BY date_debut DESC LIMIT 1"
        ),
        {"d": date_valeur},
    ).fetchone()
    return row[0] if row else None


def _backfill_inscriptions(bind):
    rows = bind.execute(
        sa.text(
            "SELECT i.id, a.date_debut "
            "FROM inscriptions i "
            "LEFT JOIN annees_scolaires a ON a.id = i.id_annee_scolaire "
            "WHERE i.code_inscription IS NULL "
            "ORDER BY i.id_annee_scolaire, i.id"
        )
    ).fetchall()
    if not rows:
        return
    compteurs = {}
    for iid, date_debut in rows:
        annee = _annee(date_debut)
        compteurs[annee] = compteurs.get(annee, 0) + 1
        code = f"INS{annee:02d}{compteurs[annee]:05d}"
        bind.execute(
            sa.text("UPDATE inscriptions SET code_inscription = :code WHERE id = :id"),
            {"code": code, "id": iid},
        )
    logger.info("Migration : %d code(s) d'inscription attribué(s).", len(rows))


def _backfill_paiements(bind):
    rows = bind.execute(
        sa.text(
            "SELECT p.id, a.date_debut "
            "FROM paiements p "
            "LEFT JOIN inscriptions i ON i.id = p.id_inscription "
            "LEFT JOIN annees_scolaires a ON a.id = i.id_annee_scolaire "
            "WHERE p.code_paiement IS NULL "
            "ORDER BY p.id"
        )
    ).fetchall()
    if not rows:
        return
    compteurs = {}
    for pid, date_debut in rows:
        annee = _annee(date_debut)
        compteurs[annee] = compteurs.get(annee, 0) + 1
        code = f"PAI{annee:02d}{compteurs[annee]:05d}"
        bind.execute(
            sa.text("UPDATE paiements SET code_paiement = :code WHERE id = :id"),
            {"code": code, "id": pid},
        )
    logger.info("Migration : %d code(s) de paiement attribué(s).", len(rows))


def _backfill_depenses(bind):
    rows = bind.execute(
        sa.text("SELECT id, date FROM depenses WHERE code_depense IS NULL ORDER BY date, id")
    ).fetchall()
    if not rows:
        return
    compteurs = {}
    for did, date_valeur in rows:
        date_valeur = date.fromisoformat(date_valeur[:10]) if isinstance(date_valeur, str) else date_valeur
        active = _annee_active(bind, date_valeur)
        annee = _annee(active)
        compteurs[annee] = compteurs.get(annee, 0) + 1
        code = f"DEP{annee:02d}{compteurs[annee]:05d}"
        bind.execute(
            sa.text("UPDATE depenses SET code_depense = :code WHERE id = :id"),
            {"code": code, "id": did},
        )
    logger.info("Migration : %d code(s) de dépense attribué(s).", len(rows))


def _backfill_globaux(bind, table, colonne, prefixe):
    rows = bind.execute(
        sa.text(f"SELECT id FROM {table} WHERE {colonne} IS NULL ORDER BY id")
    ).fetchall()
    if not rows:
        return
    annee = datetime.now().year % 100
    for i, (rid,) in enumerate(rows, start=1):
        code = f"{prefixe}{annee:02d}{i:05d}"
        bind.execute(
            sa.text(f"UPDATE {table} SET {colonne} = :code WHERE id = :id"),
            {"code": code, "id": rid},
        )
    logger.info("Migration : %d code(s) %s attribué(s).", len(rows), prefixe)


def upgrade() -> None:
    """Ajoute les colonnes, backfill, puis index uniques."""
    bind = op.get_bind()
    inspector = inspect(bind)

    def colonnes(table):
        return {c["name"] for c in inspector.get_columns(table)}

    def index_existe(nom):
        for t in inspector.get_table_names():
            if nom in {i["name"] for i in inspector.get_indexes(t)}:
                return True
        return False

    # "ADD COLUMN IF NOT EXISTS" n'existe pas en SQLite : on teste en Python.
    for table, colonne, _index in _COLONNES:
        if colonne not in colonnes(table):
            op.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} VARCHAR")

    _backfill_inscriptions(bind)
    _backfill_paiements(bind)
    _backfill_depenses(bind)
    for table, colonne, prefixe in _GLOBAUX:
        _backfill_globaux(bind, table, colonne, prefixe)

    for table, colonne, index in _COLONNES:
        if not index_existe(index):
            op.execute(f"CREATE UNIQUE INDEX {index} ON {table} ({colonne})")


def downgrade() -> None:
    """Downgrade schema (meilleur effort : DROP COLUMN absent de SQLite < 3.35)."""
    for table, colonne, index in reversed(_COLONNES):
        op.execute(f"DROP INDEX IF EXISTS {index}")
        try:
            op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS {colonne}")
        except Exception:  # SQLite n'accepte pas "DROP COLUMN IF EXISTS"
            op.execute(f"ALTER TABLE {table} DROP COLUMN {colonne}")
