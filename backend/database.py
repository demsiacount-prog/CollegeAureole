import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()


def get_data_dir() -> str:
    """Répertoire de données persistant (mode desktop SQLite) ou None si DATABASE_URL est fourni."""
    if os.getenv("DATABASE_URL"):
        return None
    _db_dir = os.getenv("AUREOLE_DATA_DIR", os.path.join(os.path.expanduser("~"), ".college-aureole"))
    os.makedirs(_db_dir, exist_ok=True)
    return _db_dir


# Support PostgreSQL (via DATABASE_URL) ou SQLite (fallback pour le mode desktop)
_DATABASE_URL = os.getenv("DATABASE_URL")
if _DATABASE_URL:
    DATABASE_URL = _DATABASE_URL
else:
    _db_dir = get_data_dir()
    DATABASE_URL = f"sqlite:///{os.path.join(_db_dir, 'collegeaureole.db')}"

_engine_kwargs = {"echo": os.getenv("SQL_ECHO", "false").strip().lower() == "true"}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
