"""Génération des identifiants de type {PRÉFIXE}{année}{n°}.

Compteur calculé côté application par MAX(n° existant pour le préfixe) + 1 :
robuste aux suppressions (contrairement à COUNT(*) + 1) et cohérent entre
SQLite et PostgreSQL. Deux familles de numérotation :

- globale (enseignants, tuteurs, classes, cours, salles) : année de création,
  compteur jamais réinitialisé ;
- annuelle (inscriptions, paiements, dépenses, élèves) : année dérivée de
  l'année scolaire concernée (inscription pour les élèves), compteur qui
  repart à 1 chaque année.

Dans les événements before_insert, `session` doit être transmis : SQLAlchemy
déclenche tous les before_insert avant d'émettre les INSERT, un MAX sur la
table ne verrait alors aucune ligne pour un flush groupé → codes dupliqués.
Un compteur courant est donc maintenu dans session.info pendant le flush.

PostgreSQL : verrou advisory `pg_advisory_xact_lock` sur {préfixe, année}
pour sérialiser la génération entre sessions concurrentes.
"""
from datetime import datetime

from sqlalchemy import select, text


def _make_lock_key(prefixe: str, annee_num: int) -> int:
    """Clé de verrou advisory stable pour un couple (préfixe, année)."""
    raw = f"{prefixe}{annee_num:02d}".encode()
    return int.from_bytes(raw[:4].ljust(4, b"\x00"), "big") & 0x7FFFFFFF


def prochain_numero(connection, colonne, prefixe: str, annee_num: int) -> int:
    """Plus grand n° existant pour {préfixe}{année} + 1."""
    prefix = f"{prefixe}{annee_num:02d}"
    codes = connection.execute(
        select(colonne).where(colonne.like(f"{prefix}%"))
    ).scalars().all()
    numeros = [int(c[len(prefix):]) for c in codes if c and c.startswith(prefix)]
    return (max(numeros) if numeros else 0) + 1


def generer_code(connection, colonne, prefixe: str, annee_num: int, session=None) -> str:
    """Génère un identifiant {préfixe}{année:02d}{compteur:05d}.

    Avec une session fournie, un compteur courant est maintenu dans
    `session.info` pendant un même flush : indispensable quand plusieurs
    lignes sont insérées dans un seul commit (tous les before_insert
    s'exécutent avant que les INSERT ne soient émis, le MAX sur la table
    ne verrait alors qu'aucune ligne → codes dupliqués).

    Sur PostgreSQL, un verrou advisory est acquis avant le MAX pour
    sérialiser les sessions concurrentes."""
    prefix = f"{prefixe}{annee_num:02d}"
    if session is not None:
        cle = (prefixe, annee_num)
        compteur = session.info.get(cle)
        if compteur is None:
            # PostgreSQL : verrou advisory avant le SELECT MAX
            if connection.dialect.name == "postgresql":
                lock_key = _make_lock_key(prefixe, annee_num)
                connection.execute(
                    text("SELECT pg_advisory_xact_lock(:k)"), {"k": lock_key}
                )
            compteur = prochain_numero(connection, colonne, prefixe, annee_num)
            session.info[cle] = compteur
        else:
            compteur += 1
            session.info[cle] = compteur
        return f"{prefix}{compteur:05d}"
    return f"{prefix}{prochain_numero(connection, colonne, prefixe, annee_num):05d}"


def annee_creation() -> int:
    return datetime.now().year % 100


def resoudre_annee(connection, annee_scolaire_id=None) -> int:
    """Année (2 chiffres) de l'année scolaire donnée, sinon de l'année active,
    sinon l'année courante."""
    from models.annees_scolaires import AnneesScolaires

    if annee_scolaire_id is not None:
        row = connection.execute(
            select(AnneesScolaires.date_debut).where(AnneesScolaires.id == annee_scolaire_id)
        ).first()
        if row:
            return row[0].year % 100

    row = connection.execute(
        select(AnneesScolaires.date_debut)
        .where(AnneesScolaires.active.is_(True))
        .order_by(AnneesScolaires.date_debut.desc())
    ).first()
    return row[0].year % 100 if row else annee_creation()


def annee_scolaire_pour_date(connection, date_valeur) -> int:
    """Année (2 chiffres) de l'année scolaire englobant une date, sinon année courante."""
    from models.annees_scolaires import AnneesScolaires

    row = connection.execute(
        select(AnneesScolaires.date_debut).where(
            AnneesScolaires.date_debut <= date_valeur,
            AnneesScolaires.date_fin >= date_valeur,
        ).order_by(AnneesScolaires.date_debut.desc())
    ).first()
    return row[0].year % 100 if row else annee_creation()


def annee_scolaire_depuis_inscription(connection, id_inscription) -> int:
    """Année (2 chiffres) de l'année scolaire de l'inscription liée, sinon année courante."""
    from models.inscriptions import Inscriptions
    from models.annees_scolaires import AnneesScolaires

    row = connection.execute(
        select(AnneesScolaires.date_debut)
        .select_from(Inscriptions)
        .join(AnneesScolaires, Inscriptions.id_annee_scolaire == AnneesScolaires.id)
        .where(Inscriptions.id == id_inscription)
    ).first()
    return row[0].year % 100 if row else annee_creation()
