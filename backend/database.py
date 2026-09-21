import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquant")

_engine_kwargs = {"echo": os.getenv("SQL_ECHO", "false").strip().lower() == "true"}

if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL : pool de connexions pour serveur multi-clients.
    _engine_kwargs.update(
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )

engine = create_engine(DATABASE_URL, **_engine_kwargs)

if DATABASE_URL.startswith("sqlite"):
    # FIX RISQUE CRITIQUE (durabilité des données) : `synchronous=NORMAL` en
    # mode WAL n'attend pas l'écriture sur disque avant d'accuser réception.
    # Une coupure d'alimentation ou un crash OS peut perdre la dernière
    # transaction committée (notes, paiements…). Le défaut est désormais
    # `synchronous=FULL` (durable) ; le mode NORMAL reste configurable pour les
    # environnements où la perf prime, via SQLITE_SYNCHRONOUS.
    _sqlite_synchronous = os.getenv("SQLITE_SYNCHRONOUS", "FULL").strip().upper()
    _sqlite_busy_timeout = int(os.getenv("SQLITE_BUSY_TIMEOUT", "5000"))

    def _configure_sqlite(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=%s" % _sqlite_synchronous)
        cursor.execute("PRAGMA foreign_keys=ON")
        # Évite les erreurs « database is locked » sous accès multi-connexions
        # (WebView + API) en attendant que le verrou se libère.
        cursor.execute("PRAGMA busy_timeout=%d" % _sqlite_busy_timeout)
        cursor.execute("PRAGMA wal_autocheckpoint=1000")
        cursor.execute("PRAGMA journal_size_limit=67108864")  # 64 Mo
        cursor.close()

    event.listen(engine, "connect", _configure_sqlite)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
