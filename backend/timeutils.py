# timeutils.py
"""Utilitaires de date/heure centralisés.

Toute l'application doit produire des datetimes *timezone-aware* en UTC.
`datetime.utcnow()` est dépréciée (Python 3.12+) et surtout dangereuse ici :
elle renvoie un datetime naïf (sans tzinfo) qui se compare et se sérialise
de façon incohérente avec des datetimes aware, et `datetime.now()` (sans
argument) renvoie l'heure *locale* du serveur, ce qui posait un vrai bug de
cohérence entre colonnes (certaines en heure locale, d'autres en UTC naïf).

Règle unique désormais : on utilise `now_utc()` partout (colonnes ORM,
JWT, comparaisons métier), et les colonnes DateTime sont déclarées avec
`timezone=True` (TIMESTAMPTZ côté PostgreSQL) pour stocker l'info de fuseau.
"""
from datetime import datetime, timezone


def now_utc() -> datetime:
    """Retourne l'instant présent, timezone-aware, en UTC."""
    return datetime.now(timezone.utc)
