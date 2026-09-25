import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquant")

if not DATABASE_URL.startswith("postgres"):
    raise RuntimeError("DATABASE_URL doit être une URL PostgreSQL (postgres:// ou postgresql://)")

# PostgreSQL : pool de connexions pour serveur multi-clients.
_engine_kwargs = {"echo": os.getenv("SQL_ECHO", "false").strip().lower() == "true"}
_engine_kwargs.update(
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()