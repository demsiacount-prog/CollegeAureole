"""Intégrité financière, historique académique et rôles métier.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


MONEY_COLUMNS = (
    ("classes", "frais_inscription"), ("classes", "mensualite"),
    ("inscriptions", "montant_total"), ("inscriptions", "credit_disponible"),
    ("echeances", "montant_du"), ("echeances", "montant_paye"),
    ("paiements", "montant"), ("depenses", "montant"),
)


def _replace_fk(table: str, column: str, target: str, ondelete: str) -> None:
    """PostgreSQL crée des noms de contraintes variables selon l'historique.
    On supprime donc la FK existante portant la colonne, puis on la recrée."""
    op.execute(f"""
        DO $$ DECLARE r record; BEGIN
          FOR r IN SELECT c.conname FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            JOIN unnest(c.conkey) WITH ORDINALITY k(attnum, ord) ON true
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = k.attnum
            WHERE c.contype = 'f' AND n.nspname = current_schema()
              AND t.relname = '{table}' AND a.attname = '{column}'
          LOOP EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', '{table}', r.conname); END LOOP;
        END $$;
    """)
    op.create_foreign_key(f"fk_{table}_{column}", table, target, [column], ["matricule" if column.startswith("matricule") else "id"], ondelete=ondelete)


def upgrade() -> None:
    for table, column in MONEY_COLUMNS:
        op.alter_column(table, column, existing_type=sa.Float(), type_=sa.Numeric(10, 2), postgresql_using=f"{column}::numeric(10,2)")

    # Les données existantes restent consultables, mais les montants impossibles
    # ne peuvent plus être injectés hors de FastAPI.
    for table, column, name, expression in (
        ("classes", "frais_inscription", "ck_classes_frais_non_negatif", "frais_inscription >= 0"),
        ("classes", "mensualite", "ck_classes_mensualite_non_negative", "mensualite >= 0"),
        ("inscriptions", "montant_total", "ck_inscriptions_total_non_negatif", "montant_total >= 0"),
        ("inscriptions", "credit_disponible", "ck_inscriptions_credit_non_negatif", "credit_disponible >= 0"),
        ("echeances", "montant_du", "ck_echeances_du_non_negatif", "montant_du >= 0"),
        ("echeances", "montant_paye", "ck_echeances_paye_non_negatif", "montant_paye >= 0"),
        ("paiements", "montant", "ck_paiements_montant_positif", "montant > 0"),
        ("depenses", "montant", "ck_depenses_montant_positif", "montant > 0"),
    ):
        op.create_check_constraint(name, table, expression)

    op.add_column("annees_scolaires", sa.Column("supprime", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("annees_scolaires", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("inscriptions", sa.Column("supprime", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("inscriptions", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("paiements", sa.Column("annule", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("paiements", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("depenses", sa.Column("annule", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("depenses", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
    for table, column in (("annees_scolaires", "supprime"), ("inscriptions", "supprime"), ("paiements", "annule"), ("depenses", "annule")):
        op.create_index(f"ix_{table}_{column}", table, [column])

    # Dates métier : le format historique était ISO YYYY-MM-DD.
    op.alter_column("notes", "date", existing_type=sa.String(), type_=sa.Date(), postgresql_using='"date"::date')
    op.alter_column("eleves", "date_de_naissance", existing_type=sa.String(), type_=sa.Date(), postgresql_using="date_de_naissance::date")

    _replace_fk("trimestres", "annee_scolaire_id", "annees_scolaires", "RESTRICT")
    _replace_fk("seances", "id_annee_scolaire", "annees_scolaires", "RESTRICT")
    _replace_fk("notes", "id_trimestre", "trimestres", "SET NULL")
    for table, column, target in (
        ("notes", "matricule_eleve", "eleves"), ("notes", "id_cours", "cours"), ("notes", "id_classe", "classes"), ("notes", "matricule_enseignant", "enseignants"),
        ("bulletins", "matricule_eleve", "eleves"), ("bulletins", "id_trimestre", "trimestres"), ("bulletins", "id_classe", "classes"),
        ("inscriptions", "matricule_eleve", "eleves"), ("echeances", "id_inscription", "inscriptions"), ("paiements", "id_inscription", "inscriptions"),
    ):
        _replace_fk(table, column, target, "RESTRICT")

    # PostgreSQL Enum : IF NOT EXISTS permet d'appliquer la migration sur une
    # base déjà mise à jour manuellement sans échec.
    op.execute("ALTER TYPE roleutilisateur ADD VALUE IF NOT EXISTS 'enseignant'")
    op.execute("ALTER TYPE roleutilisateur ADD VALUE IF NOT EXISTS 'parent'")


def downgrade() -> None:
    # Les données supprimées logiquement/annulées sont conservées volontairement.
    # Le downgrade restaure seulement la structure, sans les effacer.
    op.execute("ALTER TABLE notes ALTER COLUMN date TYPE varchar USING date::varchar")
    op.execute("ALTER TABLE eleves ALTER COLUMN date_de_naissance TYPE varchar USING date_de_naissance::varchar")
    for table, column in (("annees_scolaires", "supprime"), ("inscriptions", "supprime"), ("paiements", "annule"), ("depenses", "annule")):
        op.drop_index(f"ix_{table}_{column}", table_name=table)
    for table, columns in (("annees_scolaires", ("deleted_at", "supprime")), ("inscriptions", ("deleted_at", "supprime")), ("paiements", ("deleted_at", "annule")), ("depenses", ("deleted_at", "annule"))):
        for column in columns:
            op.drop_column(table, column)
    for table, _, name, _ in (
        ("classes", "frais_inscription", "ck_classes_frais_non_negatif", ""), ("classes", "mensualite", "ck_classes_mensualite_non_negative", ""),
        ("inscriptions", "montant_total", "ck_inscriptions_total_non_negatif", ""), ("inscriptions", "credit_disponible", "ck_inscriptions_credit_non_negatif", ""),
        ("echeances", "montant_du", "ck_echeances_du_non_negatif", ""), ("echeances", "montant_paye", "ck_echeances_paye_non_negatif", ""),
        ("paiements", "montant", "ck_paiements_montant_positif", ""), ("depenses", "montant", "ck_depenses_montant_positif", ""),
    ):
        op.drop_constraint(name, table, type_="check")
    for table, column in MONEY_COLUMNS:
        op.alter_column(table, column, existing_type=sa.Numeric(10, 2), type_=sa.Float(), postgresql_using=f"{column}::double precision")
