import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# PostgreSQL uniquement : DATABASE_URL est requis (cf. .env / .env.example).
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL est requis (PostgreSQL). Configurez votre .env : "
        "DATABASE_URL=postgresql://<utilisateur>:<mot_de_passe>@localhost:5432/collegeaureole"
    )

_engine_kwargs = {"echo": os.getenv("SQL_ECHO", "false").strip().lower() == "true"}

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
